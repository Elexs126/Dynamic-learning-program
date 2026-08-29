# -*- coding: utf-8 -*-
"""
考研数学 概率论与数理统计 辅导讲义（基础强化一本通）全自动高精度提取脚本
多进程并行 OCR + 智能结构化 Markdown 转换 + 题型/考点/公式清洗
"""

import os
import sys
import re
import json
import time
import cv2
import numpy as np
import pymupdf
from concurrent.futures import ProcessPoolExecutor, as_completed

# 符号映射表（数学符号标准化为 LaTeX）
CHAR_MAP = {
    '\uf00a': "'", '\uf00b': "''", '\uf00c': "'''",
    '\uf0b1': r"\pm ", '\uf0b6': r"\partial ", '\uf0b7': r"\cdot ", '\uf0b9': r"\neq ",
    '\uf0e0': r"\alpha ", '\uf0e1': r"\beta ", '\uf0e2': r"\gamma ", '\uf0e3': r"\delta ",
    '\uf0e4': r"\varepsilon ", '\uf0e8': r"\theta ", '\uf0eb': r"\lambda ", '\uf0ec': r"\mu ",
    '\uf0ee': r"\xi ", '\uf0f4': r"\varphi ", '\uf0f6': r"\omega ",
    'π': r"\pi", 'λ': r"\lambda", 'α': r"\alpha", 'β': r"\beta", 'θ': r"\theta",
    'μ': r"\mu", 'σ': r"\sigma", 'ρ': r"\rho", 'φ': r"\varphi", 'ω': r"\omega",
    '≤': r"\le ", '≥': r"\ge ", '≠': r"\neq ", '∈': r"\in ", '→': r"\to ",
    '∞': r"\infty", '∑': r"\sum ", '∏': r"\prod ", '∫': r"\int ", '∬': r"\iint ",
    '∪': r"\cup ", '∩': r"\cap ", '∅': r"\emptyset ", '⊂': r"\subset ", '⊆': r"\subseteq ",
    '√': r"\sqrt", '±': r"\pm ", '×': r"\times ", '÷': r"\div ",
}

# 噪音与水印正则过滤
NOISE_PATTERNS = [
    r"后续更新公众号.*",
    r"永久联系微信.*",
    r"李良官方配套.*",
    r"扫码了解课程.*",
    r"官方配套扫码了解.*",
    r"本章配套习题.*",
    r"微信刷题小程序.*",
    r"经验超市考研数学系列丛书.*",
    r"TIANJIN\s*UNIVERSITY\s*PRESS.*",
    r"National\s*Postgraduate\s*Entrance\s*Examination.*",
    r"4\.9元.*",
    r"支持错题导出.*",
    r"第\s*\d+\s*页",
]

CHAPTER_CONFIG = [
    # 基础篇
    {
        "part": "01_基础篇",
        "file": "第01章_随机事件和概率.md",
        "title": "第一章 随机事件和概率",
        "start_page": 10,
        "end_page": 29,
    },
    {
        "part": "01_基础篇",
        "file": "第02章_一维随机变量及其分布.md",
        "title": "第二章 一维随机变量及其分布",
        "start_page": 30,
        "end_page": 50,
    },
    {
        "part": "01_基础篇",
        "file": "第03章_多维随机变量及其分布.md",
        "title": "第三章 多维随机变量及其分布",
        "start_page": 51,
        "end_page": 76,
    },
    {
        "part": "01_基础篇",
        "file": "第04章_数字特征.md",
        "title": "第四章 数字特征",
        "start_page": 77,
        "end_page": 95,
    },
    {
        "part": "01_基础篇",
        "file": "第05章_大数定律和中心极限定理.md",
        "title": "第五章 大数定律和中心极限定理",
        "start_page": 96,
        "end_page": 100,
    },
    {
        "part": "01_基础篇",
        "file": "第06章_数理统计的基本概念.md",
        "title": "第六章 数理统计的基本概念",
        "start_page": 101,
        "end_page": 115,
    },
    {
        "part": "01_基础篇",
        "file": "第07章_参数估计与假设检验.md",
        "title": "第七章 参数估计与假设检验",
        "start_page": 116,
        "end_page": 127,
    },
    # 强化篇
    {
        "part": "02_强化篇",
        "file": "第01章_随机事件和概率.md",
        "title": "第一章 随机事件和概率",
        "start_page": 129,
        "end_page": 144,
    },
    {
        "part": "02_强化篇",
        "file": "第02章_一维随机变量及其分布.md",
        "title": "第二章 一维随机变量及其分布",
        "start_page": 145,
        "end_page": 170,
    },
    {
        "part": "02_强化篇",
        "file": "第03章_多维随机变量及其分布.md",
        "title": "第三章 多维随机变量及其分布",
        "start_page": 171,
        "end_page": 191,
    },
    {
        "part": "02_强化篇",
        "file": "第04章_数字特征.md",
        "title": "第四章 数字特征",
        "start_page": 192,
        "end_page": 211,
    },
    {
        "part": "02_强化篇",
        "file": "第05章_大数定律和中心极限定理.md",
        "title": "第五章 大数定律和中心极限定理",
        "start_page": 212,
        "end_page": 219,
    },
    {
        "part": "02_强化篇",
        "file": "第06章_数理统计的基本概念.md",
        "title": "第六章 数理统计的基本概念",
        "start_page": 220,
        "end_page": 233,
    },
    {
        "part": "02_强化篇",
        "file": "第07章_参数估计与假设检验.md",
        "title": "第七章 参数估计与假设检验",
        "start_page": 234,
        "end_page": 248,
    },
]

def clean_line_text(line):
    for k, v in CHAR_MAP.items():
        line = line.replace(k, v)
    
    for pat in NOISE_PATTERNS:
        line = re.sub(pat, "", line, flags=re.IGNORECASE)
    
    line = line.strip()
    return line

def process_page_worker(args):
    pdf_path, pno, dpi = args
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    
    doc = pymupdf.open(pdf_path)
    page = doc[pno - 1]
    
    # 渲染页面
    pix = page.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
    results, _ = ocr(img)
    doc.close()
    
    if not results:
        return pno, []
    
    # 解析文本行并按版面位置排序 (y 主排序, x 次排序)
    # 计算每个框的坐标: [x0, y0, x1, y1]
    lines_data = []
    for item in results:
        bbox, text, score = item
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        
        # 过滤顶部页眉(概率论与数理统计辅导讲义等)
        if y0 < pix.height * 0.05:
            if "概率论" in text or "辅导讲义" in text or "第一章" in text or "第二章" in text or "第三章" in text or "第四章" in text or "第五章" in text or "第六章" in text or "第七章" in text:
                continue
                
        cleaned = clean_line_text(text)
        if cleaned:
            lines_data.append({
                "bbox": [x0, y0, x1, y1],
                "text": cleaned,
                "score": score
            })
            
    # 智能行排序：根据 y 轴阈值聚类同行，再按 x 排序
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
        
    # 合并为行文本
    page_text_lines = []
    for row in sorted_lines:
        row_text = " ".join([it["text"] for it in row]).strip()
        if row_text:
            page_text_lines.append(row_text)
            
    return pno, page_text_lines

def format_chapter_markdown(chapter_info, pages_dict):
    title = chapter_info["title"]
    start_p = chapter_info["start_page"]
    end_p = chapter_info["end_page"]
    part = chapter_info["part"]
    
    md_lines = []
    md_lines.append(f"# {title}\n")
    md_lines.append(f"> **收录范围**：{part} · PDF 第 {start_p} 页 至 第 {end_p} 页\n")
    md_lines.append("---\n")
    
    current_section = None
    
    for pno in range(start_p, end_p + 1):
        lines = pages_dict.get(pno, [])
        if not lines:
            continue
            
        md_lines.append(f"\n<!-- Page {pno} -->\n")
        
        in_callout = False
        
        for line in lines:
            # 过滤章节大标题重复出现
            if line.startswith("第一章") or line.startswith("第二章") or line.startswith("第三章") or line.startswith("第四章") or line.startswith("第五章") or line.startswith("第六章") or line.startswith("第七章"):
                if pno == start_p:
                    continue
            if line == "随机事件和概率" or line == "一维随机变量及其分布" or line == "多维随机变量及其分布" or line == "数字特征" or line == "大数定律和中心极限定理" or line == "数理统计的基本概念" or line == "参数估计与假设检验":
                if pno == start_p:
                    continue
                    
            # 识别主要大纲块
            if "【大纲要求】" in line:
                md_lines.append("\n## 【大纲要求】\n")
                continue
            if "【本章重点】" in line:
                md_lines.append("\n## 【本章重点】\n")
                continue
            if "【基础知识】" in line:
                md_lines.append("\n## 【基础知识】\n")
                continue
            if "【考点梳理】" in line or "<考点梳理>" in line:
                md_lines.append("\n## 【考点梳理】\n")
                continue
            if "【精选例题】" in line or "<精选例题>" in line:
                md_lines.append("\n## 【精选例题】\n")
                continue
            if "【方法小结】" in line or "<方法小结>" in line:
                md_lines.append("\n## 【方法小结】\n")
                continue
                
            # 识别题型
            if re.match(r"^【题型[一二三四五六七八九十\d]+.*】", line):
                md_lines.append(f"\n### {line}\n")
                continue
                
            # 识别章节一、二、三、四、五、六、七、八、九、十...
            if re.match(r"^[一二三四五六七八九十]+、", line):
                md_lines.append(f"\n### {line}\n")
                continue
                
            # 识别 (一)、(二)、(三)
            if re.match(r"^[（\(][一二三四五六七八九十]+[）\)]", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 识别良哥解读
            if "良哥解读" in line:
                md_lines.append("\n> **【良哥解读】**")
                continue
                
            # 识别例题
            if re.match(r"^【例(\d+\.\d+|\d+)?】", line) or re.match(r"^【例题】", line) or re.match(r"^例\s*\d+", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 识别解析
            if line.startswith("【解析】") or line.startswith("【解】") or line.startswith("【证】"):
                md_lines.append(f"\n**{line[:4]}** {line[4:]}\n")
                continue
                
            # 识别选择题选项 (A) (B) (C) (D)
            if re.match(r"^\([A-D]\)", line) or re.match(r"^（[A-D]）", line):
                md_lines.append(f"- {line}")
                continue
                
            # 普通正文行
            md_lines.append(line)
            
    return "\n".join(md_lines)

def main():
    pdf_path = r"d:\考研动态学习项目\01.27考研数学-概率论与数理统计-辅导讲义-基础强化一本通【数一二三通用.pdf"
    base_out_dir = r"d:\考研动态学习项目\配套讲义\李良概率论与数理统计辅导讲义"
    cache_file = os.path.join(base_out_dir, "ocr_cache.json")
    
    os.makedirs(base_out_dir, exist_ok=True)
    os.makedirs(os.path.join(base_out_dir, "01_基础篇"), exist_ok=True)
    os.makedirs(os.path.join(base_out_dir, "02_强化篇"), exist_ok=True)
    
    # 检查缓存
    pages_dict = {}
    if os.path.exists(cache_file):
        print(f"发现已有 OCR 缓存: {cache_file}，正在加载...")
        with open(cache_file, "r", encoding="utf-8") as f:
            raw_cache = json.load(f)
            pages_dict = {int(k): v for k, v in raw_cache.items()}
            
    # 计算需要处理的页码 (从 Page 10 到 Page 248)
    all_target_pages = set()
    for cfg in CHAPTER_CONFIG:
        for p in range(cfg["start_page"], cfg["end_page"] + 1):
            all_target_pages.add(p)
            
    missing_pages = sorted(list(all_target_pages - set(pages_dict.keys())))
    print(f"总目标页数: {len(all_target_pages)}, 已缓存: {len(pages_dict)}, 待处理: {len(missing_pages)}")
    
    if missing_pages:
        print(f"启动多进程高并发 OCR 提取 (使用 10 核心并行加速)...")
        tasks = [(pdf_path, pno, 150) for pno in missing_pages]
        
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=10) as executor:
            future_to_page = {executor.submit(process_page_worker, t): t[1] for t in tasks}
            
            done_count = 0
            for future in as_completed(future_to_page):
                pno, lines = future.result()
                pages_dict[pno] = lines
                done_count += 1
                if done_count % 10 == 0 or done_count == len(tasks):
                    elapsed = time.time() - t0
                    speed = done_count / elapsed if elapsed > 0 else 0
                    print(f"已完成: {done_count}/{len(tasks)} 页 ({done_count/len(tasks)*100:.1f}%), 速度: {speed:.2f} 页/秒")
                    
        # 保存缓存
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(pages_dict, f, ensure_ascii=False, indent=2)
        print(f"OCR 数据已缓存至: {cache_file}")
        
    # 生成各章节 Markdown 文件
    print("\n正在生成结构化 Markdown 讲义文档...")
    for cfg in CHAPTER_CONFIG:
        md_content = format_chapter_markdown(cfg, pages_dict)
        out_path = os.path.join(base_out_dir, cfg["part"], cfg["file"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f" -> 成功生成: {cfg['part']}/{cfg['file']} (第 {cfg['start_page']}~{cfg['end_page']} 页)")
        
    print("\n全部提取与格式化完成！所有文件已输出至 配套讲义/李良概率论与数理统计辅导讲义/")

if __name__ == "__main__":
    main()
