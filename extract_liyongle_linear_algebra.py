# -*- coding: utf-8 -*-
"""
2027李永乐考研数学《线性代数辅导讲义【强化】》全自动高精度提取与结构化 Markdown 转换脚本
多进程并发 OCR + 数学公式/矩阵 LaTeX 标准化 + 题型/定理/例题/评注智能排版
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

# 数学与线性代数符号映射表
CHAR_MAP = {
    '\uf00a': "'", '\uf00b': "''", '\uf00c': "'''",
    '\uf0b1': r"\pm ", '\uf0b6': r"\partial ", '\uf0b7': r"\cdot ", '\uf0b9': r"\neq ",
    '\uf0e0': r"\alpha ", '\uf0e1': r"\beta ", '\uf0e2': r"\gamma ", '\uf0e3': r"\delta ",
    '\uf0e4': r"\varepsilon ", '\uf0e8': r"\theta ", '\uf0eb': r"\lambda ", '\uf0ec': r"\mu ",
    '\uf0ee': r"\xi ", '\uf0f4': r"\varphi ", '\uf0f6': r"\omega ",
    'π': r"\pi", 'λ': r"\lambda", 'α': r"\alpha", 'β': r"\beta", 'γ': r"\gamma",
    'η': r"\eta", 'ξ': r"\xi", 'θ': r"\theta", 'μ': r"\mu", 'σ': r"\sigma",
    '≤': r"\le ", '≥': r"\ge ", '≠': r"\neq ", '∈': r"\in ", '→': r"\to ",
    '∞': r"\infty", '∑': r"\sum ", '∏': r"\prod ", '∫': r"\int ",
    '∪': r"\cup ", '∩': r"\cap ", '∅': r"\emptyset ", '⊂': r"\subset ", '⊆': r"\subseteq ",
    '√': r"\sqrt", '±': r"\pm ", '×': r"\times ", '÷': r"\div ", '·': r"\cdot ",
    '|A|': r"|A|", 'A^T': r"A^T", 'A^*': r"A^*", 'A^{-1}': r"A^{-1}",
}

# 噪音与水印正则过滤
NOISE_PATTERNS = [
    r"手最快资料同步.*",
    r"永乐讲线代公众号.*",
    r"关注公众号.*",
    r"考研线性代数无忧.*",
    r"微信刷题小程序.*",
    r"第\s*\d+\s*页",
    r"^学习札记$",
    r"公众号【研料库.*",
]

CHAPTER_CONFIG = [
    {
        "file": "第01章_行列式.md",
        "title": "第一章 行列式 —— 每一章都有应用",
        "start_page": 14,
        "end_page": 43,
    },
    {
        "file": "第02章_矩阵.md",
        "title": "第二章 矩阵 —— 基础，防混淆",
        "start_page": 44,
        "end_page": 79,
    },
    {
        "file": "第03章_n维向量.md",
        "title": "第三章 n维向量 —— 难点，加油",
        "start_page": 80,
        "end_page": 109,
    },
    {
        "file": "第04章_线性方程组.md",
        "title": "第四章 线性方程组 —— 重点，别马虎大意",
        "start_page": 110,
        "end_page": 142,
    },
    {
        "file": "第05章_特征值和特征向量.md",
        "title": "第五章 特征值和特征向量 —— 重点，综合性强",
        "start_page": 143,
        "end_page": 174,
    },
    {
        "file": "第06章_二次型.md",
        "title": "第六章 二次型 —— 重点，注意和特征值、特征向量的联系",
        "start_page": 175,
        "end_page": 205,
    },
    {
        "file": "附录_45分钟水平测试.md",
        "title": "附录 45分钟水平测试",
        "start_page": 206,
        "end_page": 211,
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
    
    lines_data = []
    for item in results:
        bbox, text, score = item
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        
        # 过滤顶部页眉
        if y0 < pix.height * 0.045:
            if "线性代数" in text or "辅导讲义" in text or "第一章" in text or "第二章" in text or "第三章" in text or "第四章" in text or "第五章" in text or "第六章" in text:
                continue
                
        cleaned = clean_line_text(text)
        if cleaned:
            lines_data.append({
                "bbox": [x0, y0, x1, y1],
                "text": cleaned,
                "score": score
            })
            
    # 智能行排序 (根据 y 坐标聚类同行，再按 x 排序)
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
            # 过滤章节大标题在起始页的重复
            if line.startswith("第一章") or line.startswith("第二章") or line.startswith("第三章") or line.startswith("第四章") or line.startswith("第五章") or line.startswith("第六章"):
                if pno == start_p:
                    continue
            if line in ["行列式", "矩阵", "n维向量", "线性方程组", "特征值和特征向量", "二次型", "45分钟水平测试"]:
                if pno == start_p:
                    continue
                    
            # 识别知识结构网络图与主要大板块
            if "知识结构网络图" in line:
                md_lines.append("\n## 一、知识结构网络图\n")
                continue
            if "基本内容与重要结论" in line:
                md_lines.append("\n## 二、基本内容与重要结论\n")
                continue
            if "典型例题分析选讲" in line:
                md_lines.append("\n## 三、典型例题分析选讲\n")
                continue
            if "练习题严选" in line:
                md_lines.append("\n## 四、练习题严选\n")
                continue
            if "参考答案与提示" in line:
                md_lines.append("\n## 参考答案与提示\n")
                continue
                
            # 识别定义、定理、推论、性质
            if re.match(r"^定义\s*\d+\.\d+", line) or re.match(r"^定理\s*\d+\.\d+", line) or re.match(r"^推论\s*\d+\.\d+", line) or re.match(r"^性质\s*\d+", line):
                md_lines.append(f"\n### {line}\n")
                continue
                
            # 识别大纲板块 一、二、三、四...
            if re.match(r"^[一二三四五六七八九十]+、", line):
                md_lines.append(f"\n### {line}\n")
                continue
                
            # 识别 (一)、(二)、(三)
            if re.match(r"^[（\(][一二三四五六七八九十]+[）\)]", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 识别例题
            if re.match(r"^【例(\d+\.\d+|\d+)?】", line) or re.match(r"^【例题】", line) or re.match(r"^例\s*\d+", line):
                md_lines.append(f"\n#### {line}\n")
                continue
                
            # 识别编者注与评注
            if "【编者注】" in line or "编者注" in line:
                md_lines.append(f"\n> **【编者注】** {line.replace('【编者注】', '').replace('编者注', '').strip()}")
                continue
            if "【评注】" in line or "评注" in line:
                md_lines.append(f"\n> **【评注】** {line.replace('【评注】', '').replace('评注', '').strip()}")
                continue
                
            # 识别解析与证明
            if line.startswith("【解析】") or line.startswith("【解】") or line.startswith("【证】") or line.startswith("【分析】"):
                md_lines.append(f"\n**{line[:4]}** {line[4:]}\n")
                continue
                
            # 识别选项 (A) (B) (C) (D)
            if re.match(r"^\([A-D]\)", line) or re.match(r"^（[A-D]）", line):
                md_lines.append(f"- {line}")
                continue
                
            # 普通行
            md_lines.append(line)
            
    return "\n".join(md_lines)

def main():
    pdf_path = r"d:\考研动态学习项目\教材\数一\27李永乐线代辅导讲义【强化】【公众号：研料库，料最全】.pdf"
    base_out_dir = r"d:\考研动态学习项目\配套讲义\李永乐线性代数辅导讲义【强化】"
    cache_file = os.path.join(base_out_dir, "ocr_cache.json")
    
    os.makedirs(base_out_dir, exist_ok=True)
    
    pages_dict = {}
    if os.path.exists(cache_file):
        print(f"发现已有 OCR 缓存: {cache_file}，正在加载...")
        with open(cache_file, "r", encoding="utf-8") as f:
            raw_cache = json.load(f)
            pages_dict = {int(k): v for k, v in raw_cache.items()}
            
    all_target_pages = set()
    for cfg in CHAPTER_CONFIG:
        for p in range(cfg["start_page"], cfg["end_page"] + 1):
            all_target_pages.add(p)
            
    missing_pages = sorted(list(all_target_pages - set(pages_dict.keys())))
    print(f"《李永乐线性代数强化辅导讲义》总目标页数: {len(all_target_pages)}, 已缓存: {len(pages_dict)}, 待处理: {len(missing_pages)}")
    
    if missing_pages:
        print(f"启动 10 进程并发高速 OCR 提取...")
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
                    
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(pages_dict, f, ensure_ascii=False, indent=2)
        print(f"OCR 数据已成功缓存至: {cache_file}")
        
    print("\n正在生成结构化 Markdown 讲义文档...")
    for cfg in CHAPTER_CONFIG:
        md_content = format_chapter_markdown(cfg, pages_dict)
        out_path = os.path.join(base_out_dir, cfg["file"])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f" -> 成功生成: {cfg['file']} (第 {cfg['start_page']}~{cfg['end_page']} 页)")
        
    print("\n全部提取与格式化完成！所有文件已输出至 配套讲义/李永乐线性代数辅导讲义【强化】/")

if __name__ == "__main__":
    main()
