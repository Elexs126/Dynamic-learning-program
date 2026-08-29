# -*- coding: utf-8 -*-
"""
张宇考研数学《高等数学18讲》全自动高精度提取与结构化 Markdown 转换脚本
严格遵循企业级标准架构：
- 进程池生命周期单次初始化 (Zero-Redundant Loading)
- 自适应计算设备探测与调度 (Auto CUDA / DirectML / CPU)
- GPU/DML 有界渲染预取流水线 + CPU 批量分发
- 实时增量日志与原子化缓存机制 (Crash-Resistant Journaling & Atomic Save)
- 数学符号/微积分公式 LaTeX 标准化 + 题型/考点/例题/宇哥点拨智能排版
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
# auto: 优先 CUDA，其次 Windows DirectML (RTX 3080 Ti)，都不可用时自动转 CPU
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

# 数学与微积分符号映射表
CHAR_MAP = {
    '\uf00a': "'", '\uf00b': "''", '\uf00c': "'''",
    '\uf0b1': r"\pm ", '\uf0b6': r"\partial ", '\uf0b7': r"\cdot ", '\uf0b9': r"\neq ",
    '\uf0e0': r"\alpha ", '\uf0e1': r"\beta ", '\uf0e2': r"\gamma ", '\uf0e3': r"\delta ",
    '\uf0e4': r"\varepsilon ", '\uf0e8': r"\theta ", '\uf0eb': r"\lambda ", '\uf0ec': r"\mu ",
    '\uf0ee': r"\xi ", '\uf0f4': r"\varphi ", '\uf0f6': r"\omega ",
    'π': r"\pi", 'λ': r"\lambda", 'α': r"\alpha", 'β': r"\beta", 'γ': r"\gamma",
    'δ': r"\delta", 'ε': r"\varepsilon", 'η': r"\eta", 'θ': r"\theta",
    'μ': r"\mu", 'σ': r"\sigma", 'τ': r"\tau", 'φ': r"\varphi", 'ω': r"\omega",
    '≤': r"\le ", '≥': r"\ge ", '≠': r"\neq ", '∈': r"\in ", '→': r"\to ",
    '∞': r"\infty", '∑': r"\sum ", '∏': r"\prod ", '∫': r"\int ", '∬': r"\iint ", '∭': r"\iiint ",
    '∮': r"\oint ", '∪': r"\cup ", '∩': r"\cap ", '∅': r"\emptyset ",
    '⊂': r"\subset ", '⊆': r"\subseteq ", '√': r"\sqrt", '±': r"\pm ",
    '×': r"\times ", '÷': r"\div ", '·': r"\cdot ",
}

# 噪音与水印正则过滤
NOISE_PATTERNS = [
    r"公众号[：:].*",
    r"羊驼学长.*",
    r"免费分享.*",
    r"关注公众号.*",
    r"扫码了解.*",
    r"第\s*\d+\s*页",
    r"手最快资料同步.*",
]

CHAPTER_CONFIG = [
    {
        "file": "第01讲_函数极限与连续.md",
        "title": "第 1 讲 函数极限与连续",
        "start_page": 7,
        "end_page": 81,
    },
    {
        "file": "第02讲_数列极限.md",
        "title": "第 2 讲 数列极限",
        "start_page": 82,
        "end_page": 104,
    },
    {
        "file": "第03讲_一元函数微分学的概念.md",
        "title": "第 3 讲 一元函数微分学的概念",
        "start_page": 105,
        "end_page": 124,
    },
    {
        "file": "第04讲_一元函数微分学的计算.md",
        "title": "第 4 讲 一元函数微分学的计算",
        "start_page": 125,
        "end_page": 144,
    },
    {
        "file": "第05讲_一元函数微分学的应用_一__几何应用.md",
        "title": "第 5 讲 一元函数微分学的应用（一）——几何应用",
        "start_page": 145,
        "end_page": 169,
    },
    {
        "file": "第06讲_一元函数微分学的应用_二__中值定理_微分等式与微分不等式.md",
        "title": "第 6 讲 一元函数微分学的应用（二）——中值定理、微分等式与微分不等式",
        "start_page": 170,
        "end_page": 191,
    },
    {
        "file": "第07讲_一元函数微分学的应用_三__物理应用与经济应用.md",
        "title": "第 7 讲 一元函数微分学的应用（三）——物理应用与经济应用",
        "start_page": 192,
        "end_page": 200,
    },
    {
        "file": "第08讲_一元函数积分学的概念与性质.md",
        "title": "第 8 讲 一元函数积分学的概念与性质",
        "start_page": 201,
        "end_page": 235,
    },
    {
        "file": "第09讲_一元函数积分学的计算.md",
        "title": "第 9 讲 一元函数积分学的计算",
        "start_page": 236,
        "end_page": 268,
    },
    {
        "file": "第10讲_一元函数积分学的应用_一__几何应用.md",
        "title": "第 10 讲 一元函数积分学的应用（一）——几何应用",
        "start_page": 269,
        "end_page": 287,
    },
    {
        "file": "第11讲_一元函数积分学的应用_二__积分等式与积分不等式.md",
        "title": "第 11 讲 一元函数积分学的应用（二）——积分等式与积分不等式",
        "start_page": 288,
        "end_page": 299,
    },
    {
        "file": "第12讲_一元函数积分学的应用_三__物理应用与经济应用.md",
        "title": "第 12 讲 一元函数积分学的应用（三）——物理应用与经济应用",
        "start_page": 300,
        "end_page": 309,
    },
    {
        "file": "第13讲_多元函数微分学.md",
        "title": "第 13 讲 多元函数微分学",
        "start_page": 310,
        "end_page": 343,
    },
    {
        "file": "第14讲_二重积分.md",
        "title": "第 14 讲 二重积分",
        "start_page": 344,
        "end_page": 382,
    },
    {
        "file": "第15讲_微分方程.md",
        "title": "第 15 讲 微分方程",
        "start_page": 383,
        "end_page": 414,
    },
    {
        "file": "第16讲_无穷级数.md",
        "title": "第 16 讲 无穷级数",
        "start_page": 415,
        "end_page": 469,
    },
    {
        "file": "第17讲_多元函数积分学的预备知识.md",
        "title": "第 17 讲 多元函数积分学的预备知识",
        "start_page": 470,
        "end_page": 493,
    },
    {
        "file": "第18讲_多元函数积分学.md",
        "title": "第 18 讲 多元函数积分学",
        "start_page": 494,
        "end_page": 551,
    },
    {
        "file": "附录_1_图像变换.md",
        "title": "附录 1 图像变换",
        "start_page": 552,
        "end_page": 554,
    },
    {
        "file": "附录_2_常用平面图形.md",
        "title": "附录 2 常用平面图形",
        "start_page": 555,
        "end_page": 557,
    },
    {
        "file": "附录_3_常用空间图形.md",
        "title": "附录 3 常用空间图形",
        "start_page": 558,
        "end_page": 560,
    },
    {
        "file": "附录_4_重要公式.md",
        "title": "附录 4 重要公式",
        "start_page": 561,
        "end_page": 563,
    },
    {
        "file": "附录_5_从指数函数到双曲函数.md",
        "title": "附录 5 从指数函数到双曲函数",
        "start_page": 564,
        "end_page": 568,
    },
    {
        "file": "附录_6_变形技巧.md",
        "title": "附录 6 变形技巧",
        "start_page": 569,
        "end_page": 586,
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
        
        # 过滤顶部页眉
        if y0 < page_height * 0.045:
            if "张宇" in text or "高等数学" in text or "18讲" in text or "第" in text and "讲" in text:
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

def format_chapter_markdown(chapter_info, pages_dict):
    title = chapter_info["title"]
    start_p = chapter_info["start_page"]
    end_p = chapter_info["end_page"]
    
    md_lines = []
    md_lines.append(f"# {title}\n")
    md_lines.append(f"> **收录范围**：PDF 第 {start_p} 页 至 第 {end_p} 页\n")
    md_lines.append("---\n")
    
    for pno in range(start_p, end_p + 1):
        lines = pages_dict.get(pno, [])
        if not lines:
            continue
            
        md_lines.append(f"\n<!-- Page {pno} -->\n")
        
        for line in lines:
            if re.match(r"^第\s*\d+\s*讲", line) and pno == start_p:
                continue
                    
            # 常见板块
            if "内容概要" in line or "【内容概要】" in line:
                md_lines.append("\n## 【内容概要】\n")
                continue
            if "考试内容" in line or "【考试内容】" in line:
                md_lines.append("\n## 【考试内容】\n")
                continue
            if "考纲要求" in line or "【考纲要求】" in line or "大纲要求" in line or "【大纲要求】" in line:
                md_lines.append("\n## 【大纲要求】\n")
                continue
            if "知识框架" in line or "【知识框架】" in line or "知识结构" in line or "【知识结构】" in line:
                md_lines.append("\n## 【知识框架】\n")
                continue
            if "重点、难点" in line or "【重点、难点】" in line or "【重点难点】" in line:
                md_lines.append("\n## 【重点难点】\n")
                continue
            if "本讲概览" in line or "【本讲概览】" in line:
                md_lines.append("\n## 【本讲概览】\n")
                continue
            if "例题精解" in line or "【例题精解】" in line or "典型例题" in line or "【典型例题】" in line:
                md_lines.append("\n## 【典型例题精解】\n")
                continue
            if "习题精解" in line or "【习题精解】" in line or "本讲习题" in line:
                md_lines.append("\n## 【本讲习题精解】\n")
                continue
                
            # 题型识别
            if re.match(r"^【题型[一二三四五六七八九十\d]+.*】", line) or re.match(r"^题型[一二三四五六七八九十\d]+", line):
                md_lines.append(f"\n### {line}\n")
                continue
                
            # 定义、定理
            if re.match(r"^定义\s*\d*\.?\d*", line) or re.match(r"^定理\s*\d*\.?\d*", line) or re.match(r"^推论\s*\d*\.?\d*", line) or re.match(r"^性质\s*\d*", line):
                md_lines.append(f"\n### {line}\n")
                continue
                
            # 一、二、三、四...
            if re.match(r"^[一二三四五六七八九十]+、", line):
                md_lines.append(f"\n### {line}\n")
                continue
                
            # (一)、(二)、(三)...
            if re.match(r"^[（\(][一二三四五六七八九十]+[）\)]", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 例题
            if re.match(r"^【例(\d+\.\d+|\d+)?】", line) or re.match(r"^【例题】", line) or re.match(r"^例\s*\d+", line) or re.match(r"^例题\s*\d+", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 宇哥点拨 / 点拨 / 评注
            if "宇哥点拨" in line or "【宇哥点拨】" in line:
                md_lines.append(f"\n> **【宇哥点拨】** {line.replace('【宇哥点拨】', '').replace('宇哥点拨', '').strip()}")
                continue
            if "【点拨】" in line or line.startswith("点拨：") or line.startswith("点拨 "):
                md_lines.append(f"\n> **【点拨】** {line.replace('【点拨】', '').replace('点拨：', '').replace('点拨 ', '').strip()}")
                continue
            if "【注】" in line or line.startswith("注：") or line.startswith("注 "):
                md_lines.append(f"\n> **【注】** {line.replace('【注】', '').replace('注：', '').replace('注 ', '').strip()}")
                continue
            if "【评注】" in line or "评注" in line:
                md_lines.append(f"\n> **【评注】** {line.replace('【评注】', '').replace('评注', '').strip()}")
                continue
                
            # 解析与证明
            if line.startswith("【解析】") or line.startswith("【解】") or line.startswith("【证】") or line.startswith("【分析】"):
                md_lines.append(f"\n**{line[:4]}** {line[4:]}\n")
                continue
                
            # 选项 (A) (B) (C) (D)
            if re.match(r"^\([A-D]\)", line) or re.match(r"^（[A-D]）", line):
                md_lines.append(f"- {line}")
                continue
                
            md_lines.append(line)
            
    return "\n".join(md_lines)

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
    pdf_path = r"d:\考研动态学习项目\教材\数一\高数18讲.pdf"
    base_out_dir = r"d:\考研动态学习项目\配套讲义\张宇高等数学18讲"
    cache_file = os.path.join(base_out_dir, "ocr_cache.json")
    
    os.makedirs(base_out_dir, exist_ok=True)
    
    pages_dict = load_ocr_cache(cache_file)
            
    all_target_pages = set()
    for cfg in CHAPTER_CONFIG:
        for p in range(cfg["start_page"], cfg["end_page"] + 1):
            all_target_pages.add(p)
            
    missing_pages = sorted(list(all_target_pages - set(pages_dict.keys())))
    print(f"《张宇高等数学18讲》总目标页数: {len(all_target_pages)}, 已缓存: {len(pages_dict)}, 待处理: {len(missing_pages)}")
    
    if missing_pages:
        device = resolve_ocr_device(OCR_DEVICE)
        run_ocr_pages(pdf_path, missing_pages, pages_dict, cache_file, device)
        compact_ocr_cache(cache_file, pages_dict)
        print(f"OCR 数据已成功缓存至: {cache_file}")
    elif os.path.exists(get_cache_journal_file(cache_file)):
        compact_ocr_cache(cache_file, pages_dict)
        print(f"OCR 增量缓存已合并至: {cache_file}")
        
    print("\n正在生成结构化 Markdown 讲义文档...")
    for cfg in CHAPTER_CONFIG:
        md_content = format_chapter_markdown(cfg, pages_dict)
        out_path = os.path.join(base_out_dir, cfg["file"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f" -> 成功生成: {cfg['file']} (第 {cfg['start_page']}~{cfg['end_page']} 页)")
        
    print("\n全部提取与格式化完成！所有文件已输出至 配套讲义/张宇高等数学18讲/")

if __name__ == "__main__":
    main()
