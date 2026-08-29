# -*- coding: utf-8 -*-
"""
王道考研《2027计算机组成原理考研复习指导》全自动高精度提取与结构化 Markdown 转换脚本
计算机408专业课级深度适配：
- DirectML/GPU硬件加速 + 渲染预取流水线 + 逐页增量日志容灾
- 408 计组知识体系结构化 (考纲内容 / 复习提示 / 知识框架 / 疑难点 / 深度点拨 / 考点追踪)
- x86 / MIPS 汇编代码、RTL 微操作传输 (PC->MAR) 与 C 语言伪代码智能识别 (自动构建 ```assembly / ```c 代码块)
- 计组核心数学符号与公式标准化 ($[X]_{\\text{补}}$, IEEE 754, $2^{32}=4\\text{GB}$, $TP=\\frac{n}{k+n-1}$, $\\le$, $\\ge$, $\\mu s$)
- 选择题 (A/B/C/D) 与综合题题干、答案与深度解析智能结构化
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

CHAR_MAP = {
    '\uf00a': "'", '\uf00b': "''", '\uf00c': "'''",
    '\uf0b1': r"\pm ", '\uf0b6': r"\partial ", '\uf0b7': r"\cdot ", '\uf0b9': r"\neq ",
    '\uf0e0': r"\alpha ", '\uf0e1': r"\beta ", '\uf0e2': r"\gamma ", '\uf0e3': r"\delta ",
    '\uf0e4': r"\varepsilon ", '\uf0e8': r"\theta ", '\uf0eb': r"\lambda ", '\uf0ec': r"\mu ",
    '\uf0ee': r"\xi ", '\uf0f4': r"\varphi ", '\uf0f6': r"\omega ",
    '≤': r"\le ", '≥': r"\ge ", '≠': r"\neq ", '∈': r"\in ", '→': r"\to ",
    '∞': r"\infty", '∑': r"\sum ", '∏': r"\prod ", '√': r"\sqrt", '±': r"\pm ",
    '×': r"\times ", '÷': r"\div ", '·': r"\cdot ",
    'μ': r"\mu ", 'λ': r"\lambda ", 'α': r"\alpha ", 'β': r"\beta ", 'Δ': r"\Delta ",
    '⊕': r"\oplus ",
}

NOISE_PATTERNS = [
    r"王道考研.*",
    r"王道论坛.*",
    r"王道训练营.*",
    r"计算机组成原理考研复习指导.*",
    r"关注公众号.*",
    r"扫码看视频.*",
    r"第\s*\d+\s*页",
    r"手最快资料同步.*",
    r"官方开源.*",
    r"最新配套视频请上.*",
]

CHAPTER_CONFIG = [
    {
        "file": "第01章_计算机系统概述.md",
        "title": "第1章 计算机系统概述",
        "start_page": 13,
        "end_page": 24,
    },
    {
        "file": "第02章_数据的表示和运算.md",
        "title": "第2章 数据的表示和运算",
        "start_page": 25,
        "end_page": 88,
    },
    {
        "file": "第03章_存储系统.md",
        "title": "第3章 存储系统",
        "start_page": 89,
        "end_page": 159,
    },
    {
        "file": "第04章_指令系统.md",
        "title": "第4章 指令系统",
        "start_page": 160,
        "end_page": 206,
    },
    {
        "file": "第05章_中央处理器.md",
        "title": "第5章 中央处理器",
        "start_page": 207,
        "end_page": 285,
    },
    {
        "file": "第06章_总线.md",
        "title": "第6章 总线",
        "start_page": 286,
        "end_page": 302,
    },
    {
        "file": "第07章_输入输出系统.md",
        "title": "第7章 输入/输出系统",
        "start_page": 303,
        "end_page": 340,
    },
]

ALL_TEX_COMMANDS = [
    r"\alpha", r"\beta", r"\gamma", r"\delta", r"\varepsilon", r"\theta",
    r"\lambda", r"\mu", r"\xi", r"\eta", r"\sigma", r"\tau", r"\varphi", r"\omega",
    r"\pi", r"\Lambda", r"\Sigma", r"\Phi", r"\Omega", r"\Delta",
    r"\pm", r"\neq", r"\le", r"\ge", r"\in", r"\notin", r"\to", r"\infty",
    r"\sum", r"\prod", r"\int", r"\iint", r"\sqrt", r"\times", r"\div", r"\cdot",
    r"\partial", r"\oplus", r"\dots", r"\cdots", r"\vdots", r"\ddots"
]

def clean_line_text(line):
    for k, v in CHAR_MAP.items():
        line = line.replace(k, v)
    
    for pat in NOISE_PATTERNS:
        line = re.sub(pat, "", line, flags=re.IGNORECASE)
    
    return line.strip()

def get_onnx_providers():
    try:
        import onnxruntime as ort
        return ort.get_available_providers()
    except Exception as exc:
        print(f"警告：无法读取 ONNX Runtime 后端（{exc}），将使用 CPU。")
        return ["CPUExecutionProvider"]

def resolve_ocr_device(requested_device):
    requested = requested_device.strip().lower()
    providers = get_onnx_providers()
    has_cuda = "CUDAExecutionProvider" in providers
    has_dml = "DmlExecutionProvider" in providers

    if requested == "auto":
        selected = "cuda" if has_cuda else "dml" if has_dml else "cpu"
    elif requested == "cuda" and not has_cuda:
        selected = "cpu"
    elif requested == "dml" and not has_dml:
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
            if "王道" in text or "计算机组成原理" in text or "复习指导" in text or ("第" in text and "章" in text):
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

# ----------------- 计组专有格式化与代码识别 -----------------

ASM_KEYWORDS = [
    r"^\s*(mov|add|sub|mul|div|inc|dec|and|or|xor|not|shl|shr|sar|sal|rol|ror)\b",
    r"^\s*(jmp|je|jne|jz|jnz|jg|jge|jl|jle|ja|jae|jb|jbe|call|ret|push|pop)\b",
    r"^\s*(lw|sw|lh|sh|lb|sb|lui|addu|subu|slt|slti|sll|srl|sra|beq|bne|jal|jr)\b",
    r"^\s*(MAR|MDR|PC|IR|ACC|PSW|SP|ALU)\s*[\<\\-]*\\to",
    r"^\s*\(PC\)\s*\\to", r"^\s*\(MAR\)\s*\\to", r"^\s*M\(MAR\)\s*\\to",
]

def is_asm_or_code_line(line):
    s = line.strip()
    if not s:
        return False
    chinese_chars = len(re.findall(r"[\u4e00-\u9fa5]", s))
    if chinese_chars > 3 and not (s.startswith("//") or s.startswith(";")):
        return False
    if any(re.search(kw, s, re.IGNORECASE) for kw in ASM_KEYWORDS):
        return True
    if s.endswith(";") and (len(re.findall(r"[a-zA-Z0-9_\*\=\(\)\s,\$]", s)) == len(s)):
        return True
    return False

def split_options_if_needed(line):
    opts = list(re.finditer(r"(?<![a-zA-Z0-9])([A-D][．\.\s])", line))
    if len(opts) >= 2:
        parts = []
        for i in range(len(opts)):
            start = opts[i].start()
            end = opts[i+1].start() if i + 1 < len(opts) else len(line)
            opt_text = line[start:end].strip()
            opt_text = re.sub(r"^([A-D])[．\.\s]\s*", r"- \1. ", opt_text)
            parts.append(opt_text)
        return parts
    elif len(opts) == 1 and line.startswith(opts[0].group(1)):
        opt_text = re.sub(r"^([A-D])[．\.\s]\s*", r"- \1. ", line)
        return [opt_text]
    return [line]

def wrap_cs_math(line):
    if not line.strip() or line.startswith("```"):
        return line
        
    prefix = ""
    for pfx in ["> **【王道点拨】** ", "> **【注意】** ", "> **【命题点】** ", "> **【易错点】** ", "> **【考点追踪】** ", "- A. ", "- B. ", "- C. ", "- D. ", "### ", "#### ", "##### ", "**【解析】** ", "**【分析】** ", "**【答案】** "]:
        if line.startswith(pfx):
            prefix = pfx
            line = line[len(pfx):].strip()
            break

    # 包装常见补码与原码表示 [X]补 -> $[X]_{\text{补}}$
    line = re.sub(r"\[([a-zA-Z0-9_\+\-]+)\]\s*(原|补|反|移)", r"$[\1]_{\\text{\2}}$", line)
    
    # 修复常见路径反斜杠
    line = re.sub(r"\\(file|dir|root|path|user|home)\b", r"/\\1", line)

    # 包装 $2^{32}$, $2^{16}$, $2^{10}$
    line = re.sub(r"\b2\^(\d+)\b", r"$2^{\1}$", line)
    line = re.sub(r"\b2\^{(\d+)}\b", r"$2^{\1}$", line)
    
    # 包装纯算式与时间公式
    line = re.sub(r"\b(\d+)\s*([\+\-\*\/])\s*(\d+)\s*=\s*(\d+)\b", r"$\1 \2 \3 = \4$", line)
    
    # 包装裸 TeX 命令
    for sym in ALL_TEX_COMMANDS:
        pattern = r"(?<!\$)" + re.escape(sym) + r"(?!\$)"
        line = re.sub(pattern, lambda m, s=sym: f" ${s}$ ", line)

    line = re.sub(r"\$\s*([^\$]+?)\s*\$\s*([\+\-\*\/=><≠,;]+)\s*\$\s*([^\$]+?)\s*\$", r"$\1 \2 \3$", line)
    line = re.sub(r"\$\s*([^\$]+?)\s*\$\s*\$\s*([^\$]+?)\s*\$", r"$\1 \2$", line)
    line = re.sub(r"\s+", " ", line).strip()
    
    return prefix + line

def format_chapter(chapter_info, pages_dict):
    title = chapter_info["title"]
    start_p = chapter_info["start_page"]
    end_p = chapter_info["end_page"]
    
    md_lines = []
    md_lines.append(f"# {title}\n")
    md_lines.append(f"> **收录范围**：PDF 第 {start_p} 页 至 第 {end_p} 页\n")
    md_lines.append("---\n")
    
    in_code_block = False
    in_answers_section = False
    
    for pno in range(start_p, end_p + 1):
        raw_lines = pages_dict.get(str(pno), pages_dict.get(pno, []))
        if not raw_lines:
            continue
            
        md_lines.append(f"\n<!-- Page {pno} -->\n")
        
        for raw_line in raw_lines:
            line = raw_line.strip()
            if not line:
                continue
                
            # 过滤章节大标题重复
            if pno == start_p and (line.startswith("第1章") or line.startswith("第2章") or line.startswith("第3章") or line.startswith("第4章") or line.startswith("第5章") or line.startswith("第6章") or line.startswith("第7章")):
                continue
            if pno == start_p and line in ["计算机系统概述", "数据的表示和运算", "存储系统", "指令系统", "中央处理器", "总线", "输入/输出系统", "输入输出系统"]:
                continue

            # 智能汇编与代码块识别
            if is_asm_or_code_line(line):
                if not in_code_block:
                    md_lines.append("\n```assembly")
                    in_code_block = True
                md_lines.append(line)
                continue
            else:
                if in_code_block:
                    md_lines.append("```\n")
                    in_code_block = False

            # 王道板块与大纲识别
            if "【考纲内容】" in line or line == "考纲内容":
                md_lines.append("\n## 【考纲内容】\n")
                continue
            if "【复习提示】" in line or line == "复习提示":
                md_lines.append("\n## 【复习提示】\n")
                continue
            if "【知识框架】" in line or "知识框架" in line:
                md_lines.append("\n## 【知识框架】\n")
                continue
            if "本节习题精选" in line or line.endswith("本节习题精选"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = False
                continue
            if "答案与解析" in line or line.endswith("答案与解析"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = True
                continue
            if "本章小结" in line or line.endswith("本章小结"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = False
                continue
            if "常见问题和易混淆知识点" in line or line.endswith("常见问题和易混淆知识点"):
                md_lines.append(f"\n## 【{line}】\n")
                in_answers_section = False
                continue

            # 识别二级节标题 (如 1.1 计算机发展历程)
            if re.match(r"^\*?\d+\.\d+\s+[\u4e00-\u9fa5]", line):
                md_lines.append(f"\n### {line}\n")
                in_answers_section = False
                continue
                
            # 识别三级小节标题 (如 1.1.1 计算机硬件的发展)
            if re.match(r"^\*?\d+\.\d+\.\d+\s+[\u4e00-\u9fa5]", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 识别四级标题 (如 1．硬件系统, 1. 概念)
            if re.match(r"^[1-9]\s*[．\.]\s*[\u4e00-\u9fa5]", line):
                md_lines.append(f"\n##### {line}\n")
                continue
                
            # 识别题型分类
            if line in ["一、单项选择题", "单项选择题", "选择题"]:
                md_lines.append("\n### 单项选择题\n")
                continue
            if line in ["二、综合应用题", "综合应用题", "综合题"]:
                md_lines.append("\n### 综合应用题\n")
                continue
                
            # 识别王道特色 Callout 引用框
            if "王道点拨" in line or "【王道点拨】" in line:
                clean_t = line.replace("【王道点拨】", "").replace("王道点拨", "").strip()
                md_lines.append(f"\n> **【王道点拨】** {clean_t}\n")
                continue
            if line.startswith("注意") or "【注意】" in line:
                clean_t = line.replace("【注意】", "").replace("注意：", "").replace("注意", "").strip()
                md_lines.append(f"\n> **【注意】** {clean_t}\n")
                continue
            if "考点追踪" in line or "【考点追踪】" in line:
                clean_t = line.replace("【考点追踪】", "").replace("考点追踪", "").strip()
                md_lines.append(f"\n> **【考点追踪】** {clean_t}\n")
                continue
            if "命题点" in line or "【命题点】" in line:
                clean_t = line.replace("【命题点】", "").replace("命题点：", "").replace("命题点", "").strip()
                md_lines.append(f"\n> **【命题点】** {clean_t}\n")
                continue
            if "易错点" in line or "【易错点】" in line:
                clean_t = line.replace("【易错点】", "").replace("易错点：", "").replace("易错点", "").strip()
                md_lines.append(f"\n> **【易错点】** {clean_t}\n")
                continue

            # 识别题目答案与解析 (在答案部分，如 01.C 或 01. 【答案】C)
            m_ans = re.match(r"^0*([1-9]\d*)\s*[．\.]\s*([A-D])\b", line)
            if in_answers_section and m_ans:
                qnum = m_ans.group(1)
                ans = m_ans.group(2)
                md_lines.append(f"\n**{qnum}. 【答案】 {ans}**\n")
                continue
            elif in_answers_section and (line.startswith("【解析】") or line.startswith("【分析】")):
                md_lines.append(f"\n**{line[:4]}** {line[4:].strip()}\n")
                continue

            # 识别选择题题干编号 (如 01．计算机硬件能够直接执行... 或 11．【2012统考真题】...)
            m_q = re.match(r"^0*([1-9]\d*)\s*[．\.]\s*(.*)", line)
            if m_q and ("（）" in line or "()" in line or "下列" in line or "统考真题" in line or "【" in line):
                qnum = m_q.group(1)
                qcontent = m_q.group(2)
                md_lines.append(f"\n**{qnum}.** {wrap_cs_math(qcontent)}\n")
                continue

            # 识别并拆分选择题选项 (A. ... B. ... C. ... D. ...)
            split_opts = split_options_if_needed(line)
            for opt_line in split_opts:
                formatted_line = wrap_cs_math(opt_line)
                md_lines.append(formatted_line)
                
        if in_code_block:
            md_lines.append("```\n")
            in_code_block = False
            
    return "\n".join(md_lines)

# ----------------- 缓存与主入口 -----------------

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
                    pass
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
        except OSError:
            pass

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
            f"每进程 {threads_per_worker} 个 ONNX 线程..."
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
    pdf_path = r"d:\考研动态学习项目\教材\408\2027计算机组成原理_高清带书签版.pdf"
    base_out_dir = r"d:\考研动态学习项目\配套讲义\王道2027计算机组成原理考研复习指导"
    cache_file = os.path.join(base_out_dir, "ocr_cache.json")
    
    os.makedirs(base_out_dir, exist_ok=True)
    
    pages_dict = load_ocr_cache(cache_file)
            
    all_target_pages = set()
    for cfg in CHAPTER_CONFIG:
        for p in range(cfg["start_page"], cfg["end_page"] + 1):
            all_target_pages.add(p)
            
    missing_pages = sorted(list(all_target_pages - set(pages_dict.keys())))
    print(f"《王道2027计算机组成原理考研复习指导》总目标页数: {len(all_target_pages)}, 已缓存: {len(pages_dict)}, 待处理: {len(missing_pages)}")
    
    if missing_pages:
        device = resolve_ocr_device(OCR_DEVICE)
        run_ocr_pages(pdf_path, missing_pages, pages_dict, cache_file, device)
        compact_ocr_cache(cache_file, pages_dict)
        print(f"OCR 数据已成功缓存至: {cache_file}")
    elif os.path.exists(get_cache_journal_file(cache_file)):
        compact_ocr_cache(cache_file, pages_dict)
        print(f"OCR 增量缓存已合并至: {cache_file}")
        
    print("\n正在生成结构化 Markdown 讲义文档与汇编/微操作代码块排版...")
    for cfg in CHAPTER_CONFIG:
        md_content = format_chapter(cfg, pages_dict)
        out_path = os.path.join(base_out_dir, cfg["file"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f" -> 成功生成: {cfg['file']} (第 {cfg['start_page']}~{cfg['end_page']} 页)")
        
    print("\n全部提取与格式化完成！所有文件已输出至 配套讲义/王道2027计算机组成原理考研复习指导/")

if __name__ == "__main__":
    main()
