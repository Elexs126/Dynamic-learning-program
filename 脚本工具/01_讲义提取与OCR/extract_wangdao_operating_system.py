# -*- coding: utf-8 -*-
"""
王道考研《2027操作系统考研复习指导》全自动高精度提取与结构化 Markdown 转换脚本
计算机408专业课级深度适配：
- 严格遵循优化架构：DirectML/GPU硬件加速 + 渲染预取流水线 + 逐页增量日志容灾
- 408 知识体系结构化 (考纲内容 / 复习提示 / 知识框架 / 疑难点 / 深度点拨)
- C/C++ 伪代码与 P/V 信号量智能识别 (自动构建 ```c 代码块)
- 选择题 (A/B/C/D) 与综合应用题题干、答案与深度解析智能结构化
- 计算机数学与地址计算公式 LaTeX 标准化 ($2^{32}=4\\text{GB}$, $\\text{周转时间}$, $\\le$, $\\ge$)
- 彻底过滤页眉页脚与王道宣传水印
"""

import os
import sys
import re
import json
import time
import atexit
import threading
from collections import deque
import cv2
import numpy as np
import pymupdf
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

# ------------------------------ 性能配置 ------------------------------
OCR_DEVICE = "auto"
OCR_DPI = 150

MAX_CPU_WORKERS = 4
CPU_PAGE_BATCH_SIZE = 4

GPU_RENDER_WORKERS = 2
GPU_PREFETCH_PAGES = 4

USE_ANGLE_CLASSIFIER = True
PROGRESS_EVERY = 10

_WORKER_OCR = None
_WORKER_DOC = None
_WORKER_DPI = OCR_DPI
_RENDER_THREAD_STATE = threading.local()

# 计算机 408 常用符号映射表
CHAR_MAP = {
    '\uf00a': "'", '\uf00b': "''", '\uf00c': "'''",
    '\uf0b1': r"\pm ", '\uf0b6': r"\partial ", '\uf0b7': r"\cdot ", '\uf0b9': r"\neq ",
    '\uf0e0': r"\alpha ", '\uf0e1': r"\beta ", '\uf0e2': r"\gamma ", '\uf0e3': r"\delta ",
    '\uf0e4': r"\varepsilon ", '\uf0e8': r"\theta ", '\uf0eb': r"\lambda ", '\uf0ec': r"\mu ",
    '\uf0ee': r"\xi ", '\uf0f4': r"\varphi ", '\uf0f6': r"\omega ",
    '≤': r"\le ", '≥': r"\ge ", '≠': r"\neq ", '∈': r"\in ", '→': r"\to ",
    '∞': r"\infty", '∑': r"\sum ", '∏': r"\prod ", '√': r"\sqrt", '±': r"\pm ",
    '×': r"\times ", '÷': r"\div ", '·': r"\cdot ",
    'μ': r"\mu ", 'λ': r"\lambda ", 'α': r"\alpha ", 'β': r"\beta ",
}

# 噪音与水印正则过滤
NOISE_PATTERNS = [
    r"王道考研.*",
    r"王道论坛.*",
    r"王道训练营.*",
    r"操作系统考研复习指导.*",
    r"关注公众号.*",
    r"扫码看视频.*",
    r"第\s*\d+\s*页",
    r"手最快资料同步.*",
]

CHAPTER_CONFIG = [
    {
        "file": "第01章_计算机系统概述.md",
        "title": "第1章 计算机系统概述",
        "start_page": 13,
        "end_page": 48,
    },
    {
        "file": "第02章_进程与线程.md",
        "title": "第2章 进程与线程",
        "start_page": 49,
        "end_page": 187,
    },
    {
        "file": "第03章_内存管理.md",
        "title": "第3章 内存管理",
        "start_page": 188,
        "end_page": 262,
    },
    {
        "file": "第04章_文件管理.md",
        "title": "第4章 文件管理",
        "start_page": 263,
        "end_page": 316,
    },
    {
        "file": "第05章_输入输出管理.md",
        "title": "第5章 输入/输出管理",
        "start_page": 317,
        "end_page": 372,
    },
]

def clean_line_text(line):
    for k, v in CHAR_MAP.items():
        line = line.replace(k, v)
    
    for pat in NOISE_PATTERNS:
        line = re.sub(pat, "", line, flags=re.IGNORECASE)
    
    line = line.strip()
    return line

def get_onnx_providers():
    try:
        import onnxruntime as ort
        return ort.get_available_providers()
    except Exception as exc:
        print(f"警告：无法读取 ONNX Runtime 后端（{exc}），将使用 CPU。")
        return ["CPUExecutionProvider"]

def resolve_ocr_device(requested_device):
    requested = requested_device.strip().lower()
    if requested not in {"auto", "cpu", "cuda", "dml"}:
        raise ValueError("OCR_DEVICE 只能是 auto / cpu / cuda / dml")

    providers = get_onnx_providers()
    has_cuda = "CUDAExecutionProvider" in providers
    has_dml = "DmlExecutionProvider" in providers

    if requested == "auto":
        selected = "cuda" if has_cuda else "dml" if has_dml else "cpu"
    elif requested == "cuda" and not has_cuda:
        print("警告：请求使用 CUDA，但 CUDAExecutionProvider 不可用，已转为 CPU。")
        selected = "cpu"
    elif requested == "dml" and not has_dml:
        print("警告：请求使用 DirectML，但 DmlExecutionProvider 不可用，已转为 CPU。")
        selected = "cpu"
    else:
        selected = requested

    print(f"ONNX Runtime 可用后端: {providers}")
    print(f"本次 OCR 实际使用: {selected.upper()}")
    return selected

def close_worker_resources():
    global _WORKER_OCR, _WORKER_DOC
    if _WORKER_DOC is not None:
        try:
            _WORKER_DOC.close()
        except Exception:
            pass
        _WORKER_DOC = None
    _WORKER_OCR = None

def init_worker(pdf_path, dpi, device, intra_op_threads, open_document=True):
    global _WORKER_OCR, _WORKER_DOC, _WORKER_DPI
    from rapidocr_onnxruntime import RapidOCR

    use_cuda = device == "cuda"
    use_dml = device == "dml"
    _WORKER_OCR = RapidOCR(
        det_use_cuda=use_cuda,
        cls_use_cuda=use_cuda,
        rec_use_cuda=use_cuda,
        det_use_dml=use_dml,
        cls_use_dml=use_dml,
        rec_use_dml=use_dml,
        intra_op_num_threads=intra_op_threads,
        inter_op_num_threads=1,
        print_verbose=False,
    )
    _WORKER_DOC = pymupdf.open(pdf_path) if open_document else None
    _WORKER_DPI = dpi
    atexit.register(close_worker_resources)

def render_page(doc, pno, dpi):
    page = doc[pno - 1]
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
    page_height = pix.height
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    return img, page_height

def ocr_rendered_page(pno, img, page_height):
    if _WORKER_OCR is None:
        raise RuntimeError("OCR worker 未初始化")

    if USE_ANGLE_CLASSIFIER:
        results, _ = _WORKER_OCR(img)
    else:
        results, _ = _WORKER_OCR(img, use_cls=False)

    if not results:
        return pno, []
    
    lines_data = []
    for item in results:
        bbox, text, score = item
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        
        # 过滤顶部页眉 (王道考研、操作系统、第X章)
        if y0 < page_height * 0.045:
            if "王道" in text or "操作系统" in text or "复习指导" in text or ("第" in text and "章" in text):
                continue
                
        cleaned = clean_line_text(text)
        if cleaned:
            lines_data.append({
                "bbox": [x0, y0, x1, y1],
                "text": cleaned,
                "score": score
            })
            
    lines_data.sort(key=lambda item: item["bbox"][1])
    
    sorted_lines = []
    current_line = []
    last_y = None
    
    for item in lines_data:
        y_center = (item["bbox"][1] + item["bbox"][3]) / 2
        if last_y is None or abs(y_center - last_y) < 14:
            current_line.append(item)
            last_y = y_center if last_y is None else (last_y + y_center) / 2
        else:
            current_line.sort(key=lambda it: it["bbox"][0])
            sorted_lines.append(current_line)
            current_line = [item]
            last_y = y_center
            
    if current_line:
        current_line.sort(key=lambda it: it["bbox"][0])
        sorted_lines.append(current_line)
        
    page_text_lines = []
    for row in sorted_lines:
        row_text = " ".join([it["text"] for it in row]).strip()
        if row_text:
            page_text_lines.append(row_text)
            
    return pno, page_text_lines

def process_page_worker(pno):
    if _WORKER_DOC is None:
        raise RuntimeError("PDF worker 未初始化")
    img, page_height = render_page(_WORKER_DOC, pno, _WORKER_DPI)
    return ocr_rendered_page(pno, img, page_height)

def process_page_batch(page_numbers):
    return [process_page_worker(pno) for pno in page_numbers]

def split_page_batches(page_numbers, batch_size):
    return [
        page_numbers[index:index + batch_size]
        for index in range(0, len(page_numbers), batch_size)
    ]

def init_render_thread(pdf_path):
    _RENDER_THREAD_STATE.doc = pymupdf.open(pdf_path)

def render_page_in_thread(pno, dpi):
    doc = getattr(_RENDER_THREAD_STATE, "doc", None)
    if doc is None:
        raise RuntimeError("PDF render thread 未初始化")
    img, page_height = render_page(doc, pno, dpi)
    return pno, img, page_height

def iter_prefetched_pages(executor, page_numbers, dpi, prefetch_count):
    page_iter = iter(page_numbers)
    pending = deque()

    def submit_one():
        try:
            page_no = next(page_iter)
        except StopIteration:
            return False
        pending.append(
            (page_no, executor.submit(render_page_in_thread, page_no, dpi))
        )
        return True

    for _ in range(min(prefetch_count, len(page_numbers))):
        submit_one()

    while pending:
        expected_page, future = pending.popleft()
        try:
            result = future.result()
        except Exception as exc:
            raise RuntimeError(f"PDF 第 {expected_page} 页渲染失败") from exc
        if result[0] != expected_page:
            raise RuntimeError("渲染预取页码错位")
        submit_one()
        yield result

# ----------------- 计算机408 代码与专业排版格式化 -----------------

CODE_KEYWORDS = [
    r"\bsemaphore\b", r"\bP\(", r"\bV\(", r"\bwait\(", r"\bsignal\(",
    r"\bcobegin\b", r"\bcoend\b", r"\bmutex\b", r"\bprocess\b",
    r"\btypedef\b", r"\bstruct\b", r"\bvoid\b", r"\bint\b",
    r"\bwhile\s*\(", r"\bfor\s*\(", r"\bif\s*\(", r"\breturn\b",
    r"\bpthread_create\b", r"\bpthread_join\b", r"\bpthread_mutex\b",
    r"\bfork\(\)", r"\bexec\b", r"\bpipe\(", r"\bmain\(\)"
]

def is_code_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    # 纯中文叙述非代码
    chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", stripped))
    if chinese_chars > 3:
        return False
    return any(re.search(kw, stripped, re.IGNORECASE) for kw in CODE_KEYWORDS) or stripped.endswith(";") or stripped in ["{", "}"]

def format_cs_formulas_and_math(line):
    # 包装 $2^{32}$, $2^{16}$, \le, \ge, \neq, \mu s, \pm 等
    line = re.sub(r"\b2\^(\d+)\b", r"$2^{\1}$", line)
    line = re.sub(r"\b2\^{(\d+)}\b", r"$2^{\1}$", line)
    
    # 算式包装
    line = re.sub(r"\b(\d+)\s*([\+\-\*\/])\s*(\d+)\s*=\s*(\d+)\b", r"$\1 \2 \3 = \4$", line)
    
    # 包装裸 TeX 符号
    for sym in [r"\le", r"\ge", r"\neq", r"\pm", r"\times", r"\div", r"\to", r"\mu", r"\alpha", r"\beta", r"\lambda"]:
        line = re.sub(r"(?<!\$)" + re.escape(sym) + r"(?!\$)", f" ${sym}$ ", line)
        
    line = re.sub(r"\$\s*\$", "", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line

def format_wangdao_chapter_markdown(chapter_info, pages_dict):
    title = chapter_info["title"]
    start_p = chapter_info["start_page"]
    end_p = chapter_info["end_page"]
    
    md_lines = []
    md_lines.append(f"# {title}\n")
    md_lines.append(f"> **收录范围**：PDF 第 {start_p} 页 至 第 {end_p} 页\n")
    md_lines.append("---\n")
    
    in_code_block = False
    
    for pno in range(start_p, end_p + 1):
        lines = pages_dict.get(pno, [])
        if not lines:
            continue
            
        md_lines.append(f"\n<!-- Page {pno} -->\n")
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # 过滤章节大标题在起始页的重复
            if pno == start_p and (stripped.startswith("第1章") or stripped.startswith("第2章") or stripped.startswith("第3章") or stripped.startswith("第4章") or stripped.startswith("第5章")):
                continue
            if pno == start_p and stripped in ["计算机系统概述", "进程与线程", "内存管理", "文件管理", "输入/输出管理", "输入输出管理"]:
                continue
                
            # 代码块识别状态机
            if is_code_line(stripped):
                if not in_code_block:
                    md_lines.append("\n```c")
                    in_code_block = True
                md_lines.append(stripped)
                continue
            else:
                if in_code_block:
                    md_lines.append("```\n")
                    in_code_block = False

            # 板块与大纲标题识别
            if "【考纲内容】" in stripped or stripped == "考纲内容":
                md_lines.append("\n## 【考纲内容】\n")
                continue
            if "【复习提示】" in stripped or stripped == "复习提示":
                md_lines.append("\n## 【复习提示】\n")
                continue
            if "【知识框架】" in stripped or "知识框架" in stripped:
                md_lines.append("\n## 【知识框架】\n")
                continue
            if "本节习题精选" in stripped or "习题精选" in stripped:
                md_lines.append("\n## 【本节习题精选】\n")
                continue
            if "答案与解析" in stripped or "参考答案" in stripped:
                md_lines.append("\n## 【答案与解析】\n")
                continue
            if "本章疑难点" in stripped or "疑难点" in stripped:
                md_lines.append("\n## 【本章疑难点】\n")
                continue

            # 识别二级小节 (如 1.1 操作系统的基本概念)
            if re.match(r"^\d+\.\d+\s+[\u4e00-\u9fa5]", stripped):
                md_lines.append(f"\n### {stripped}\n")
                continue
                
            # 识别三级小节 (如 1.1.1 操作系统的概念)
            if re.match(r"^\d+\.\d+\.\d+\s+[\u4e00-\u9fa5]", stripped):
                md_lines.append(f"\n#### {stripped}\n")
                continue
                
            # 识别带圈数字或点号编号 (如 1. 概念, 2. 特征)
            if re.match(r"^[1-9]\s*[．\.]\s*[\u4e00-\u9fa5]", stripped):
                md_lines.append(f"\n##### {stripped}\n")
                continue

            # 识别题型分类
            if stripped in ["一、单项选择题", "单项选择题", "选择题"]:
                md_lines.append("\n### 单项选择题\n")
                continue
            if stripped in ["二、综合应用题", "综合应用题", "综合题"]:
                md_lines.append("\n### 综合应用题\n")
                continue
                
            # 识别王道特色点拨与注意
            if "【王道点拨】" in stripped or "王道点拨" in stripped:
                md_lines.append(f"\n> **【王道点拨】** {stripped.replace('【王道点拨】', '').replace('王道点拨', '').strip()}\n")
                continue
            if "【注意】" in stripped or "注意：" in stripped:
                md_lines.append(f"\n> **【注意】** {stripped.replace('【注意】', '').replace('注意：', '').strip()}\n")
                continue
            if "【命题点】" in stripped or "命题点：" in stripped:
                md_lines.append(f"\n> **【命题点】** {stripped.replace('【命题点】', '').replace('命题点：', '').strip()}\n")
                continue
            if "【易错点】" in stripped or "易错点：" in stripped:
                md_lines.append(f"\n> **【易错点】** {stripped.replace('【易错点】', '').replace('易错点：', '').strip()}\n")
                continue

            # 识别解析与答案
            if re.match(r"^\d+\s*[．\.]\s*【答案】", stripped) or stripped.startswith("【答案】"):
                md_lines.append(f"\n**{stripped}**\n")
                continue
            if stripped.startswith("【解析】") or stripped.startswith("【分析】"):
                md_lines.append(f"\n**{stripped[:4]}** {stripped[4:]}\n")
                continue

            # 识别选择题选项
            if re.match(r"^[A-D]\s*[．\.]", stripped) or re.match(r"^\([A-D]\)", stripped) or re.match(r"^（[A-D]）", stripped):
                md_lines.append(f"- {stripped}")
                continue

            # 普通文本与计算机算式标准化
            line_formatted = format_cs_formulas_and_math(stripped)
            md_lines.append(line_formatted)
            
        if in_code_block:
            md_lines.append("```\n")
            in_code_block = False
            
    return "\n".join(md_lines)

# ----------------- 缓存机制 -----------------

def save_cache_atomic(cache_file, pages_dict):
    temp_file = f"{cache_file}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(pages_dict, f, ensure_ascii=False, indent=2)
    os.replace(temp_file, cache_file)

def get_cache_journal_file(cache_file):
    return f"{cache_file}.journal.jsonl"

def load_ocr_cache(cache_file):
    pages_dict = {}
    if os.path.exists(cache_file):
        print(f"发现已有 OCR 缓存: {cache_file}，正在加载...")
        with open(cache_file, "r", encoding="utf-8") as f:
            raw_cache = json.load(f)
        pages_dict.update({int(k): v for k, v in raw_cache.items()})

    journal_file = get_cache_journal_file(cache_file)
    recovered_count = 0
    if os.path.exists(journal_file):
        with open(journal_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    pages_dict[int(entry["page"])] = entry["lines"]
                    recovered_count += 1
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    print(f"警告：忽略增量缓存中不完整的第 {line_no} 行。")
        if recovered_count:
            print(f"已从增量缓存恢复 {recovered_count} 条页面记录。")

    return pages_dict

class IncrementalCacheWriter:
    def __init__(self, cache_file):
        self.journal_file = get_cache_journal_file(cache_file)
        self.handle = None

    def __enter__(self):
        self.handle = open(self.journal_file, "a", encoding="utf-8", buffering=1)
        return self

    def add(self, page_no, lines):
        entry = {"page": int(page_no), "lines": lines}
        self.handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")

    def __exit__(self, exc_type, exc_value, traceback):
        if self.handle is not None:
            self.handle.close()
            self.handle = None

def compact_ocr_cache(cache_file, pages_dict):
    save_cache_atomic(cache_file, pages_dict)
    journal_file = get_cache_journal_file(cache_file)
    if os.path.exists(journal_file):
        try:
            os.remove(journal_file)
        except OSError as exc:
            print(f"警告：无法清理增量缓存（{exc}）。")

def print_progress(done_count, total_count, started_at):
    elapsed = time.time() - started_at
    speed = done_count / elapsed if elapsed > 0 else 0
    remaining = (total_count - done_count) / speed if speed > 0 else 0
    print(
        f"已完成: {done_count}/{total_count} 页 "
        f"({done_count / total_count * 100:.1f}%), "
        f"速度: {speed:.2f} 页/秒, 预计剩余: {remaining / 60:.1f} 分钟"
    )

def run_ocr_pages(pdf_path, missing_pages, pages_dict, cache_file, device):
    total = len(missing_pages)
    logical_cpus = max(1, os.cpu_count() or 1)
    started_at = time.time()
    done_count = 0
    next_progress = min(PROGRESS_EVERY, total)

    with IncrementalCacheWriter(cache_file) as cache_writer:
        def store_page_result(page_no, lines):
            nonlocal done_count, next_progress
            pages_dict[page_no] = lines
            cache_writer.add(page_no, lines)
            done_count += 1
            if done_count >= next_progress or done_count == total:
                print_progress(done_count, total, started_at)
                next_progress = min(next_progress + PROGRESS_EVERY, total)

        if device in {"cuda", "dml"}:
            print(f"启动单引擎 {device.upper()} OCR + {GPU_RENDER_WORKERS} 线程有界渲染预取...")
            init_worker(pdf_path, OCR_DPI, device, 1, open_document=False)
            try:
                with ThreadPoolExecutor(
                    max_workers=GPU_RENDER_WORKERS,
                    initializer=init_render_thread,
                    initargs=(pdf_path,),
                ) as render_executor:
                    for pno, img, page_height in iter_prefetched_pages(
                        render_executor,
                        missing_pages,
                        OCR_DPI,
                        GPU_PREFETCH_PAGES,
                    ):
                        try:
                            page_no, lines = ocr_rendered_page(pno, img, page_height)
                        except Exception as exc:
                            raise RuntimeError(f"PDF 第 {pno} 页 OCR 失败") from exc
                        store_page_result(page_no, lines)
            finally:
                close_worker_resources()
            return

        page_batches = split_page_batches(missing_pages, CPU_PAGE_BATCH_SIZE)
        worker_count = min(MAX_CPU_WORKERS, len(page_batches), max(1, logical_cpus // 2))
        threads_per_worker = max(1, logical_cpus // worker_count)
        print(
            f"启动 CPU OCR: {worker_count} 个常驻进程 × "
            f"每进程 {threads_per_worker} 个 ONNX 线程，"
            f"每任务最多 {CPU_PAGE_BATCH_SIZE} 页..."
        )

        with ProcessPoolExecutor(
            max_workers=worker_count,
            initializer=init_worker,
            initargs=(pdf_path, OCR_DPI, "cpu", threads_per_worker, True),
        ) as executor:
            future_to_batch = {
                executor.submit(process_page_batch, batch): batch
                for batch in page_batches
            }

            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    batch_results = future.result()
                except Exception as exc:
                    raise RuntimeError(f"PDF 第 {batch[0]}~{batch[-1]} 页批量 OCR 失败") from exc

                for page_no, lines in batch_results:
                    store_page_result(page_no, lines)

def main():
    pdf_path = r"d:\考研动态学习项目\教材\408\王道2027操作系统-高清带书签.pdf"
    base_out_dir = r"d:\考研动态学习项目\配套讲义\王道2027操作系统考研复习指导"
    cache_file = os.path.join(base_out_dir, "ocr_cache.json")
    
    os.makedirs(base_out_dir, exist_ok=True)
    
    pages_dict = load_ocr_cache(cache_file)
            
    all_target_pages = set()
    for cfg in CHAPTER_CONFIG:
        for p in range(cfg["start_page"], cfg["end_page"] + 1):
            all_target_pages.add(p)
            
    missing_pages = sorted(list(all_target_pages - set(pages_dict.keys())))
    print(f"《王道2027操作系统考研复习指导》总目标页数: {len(all_target_pages)}, 已缓存: {len(pages_dict)}, 待处理: {len(missing_pages)}")
    
    if missing_pages:
        device = resolve_ocr_device(OCR_DEVICE)
        run_ocr_pages(pdf_path, missing_pages, pages_dict, cache_file, device)
        compact_ocr_cache(cache_file, pages_dict)
        print(f"OCR 数据已成功缓存至: {cache_file}")
    elif os.path.exists(get_cache_journal_file(cache_file)):
        compact_ocr_cache(cache_file, pages_dict)
        print(f"OCR 增量缓存已合并至: {cache_file}")
        
    print("\n正在生成结构化 Markdown 讲义文档与 C/C++ 代码块排版...")
    for cfg in CHAPTER_CONFIG:
        md_content = format_wangdao_chapter_markdown(cfg, pages_dict)
        out_path = os.path.join(base_out_dir, cfg["file"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f" -> 成功生成: {cfg['file']} (第 {cfg['start_page']}~{cfg['end_page']} 页)")
        
    print("\n全部提取与格式化完成！所有文件已输出至 配套讲义/王道2027操作系统考研复习指导/")

if __name__ == "__main__":
    main()
