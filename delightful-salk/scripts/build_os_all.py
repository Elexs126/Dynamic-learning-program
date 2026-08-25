# -*- coding: utf-8 -*-
"""
Full Builder for 王道操作系统 综合大题 (5 Chapters, 78 Questions)
"""

import os
import re

BASE_DIR = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\02_操作系统_综合大题"
IMG_DIR = r"王道计算机考研408/images/os"
os.makedirs(BASE_DIR, exist_ok=True)

with open("scripts/os_full_text.txt", "r", encoding="utf-8") as f:
    raw_content = f.read()

def clean_pua(text):
    text = text.replace("\uf001", "")
    text = text.replace("\uf0ee", "")
    text = text.replace("\uf0e0\uf0e1\uf0e2", " ")
    text = text.replace("\uf0e0", "{").replace("\uf0e1", "").replace("\uf0e2", "}")
    text = text.replace("公众号：做题本最TOP", "")
    text = text.replace("王道操作系统综合题·", "")
    text = re.sub(r'所有题本：[^\n]+', '', text)
    text = re.sub(r'第\s*\d+\s*页[，,]\s*共\s*\d+\s*页', '', text)
    text = re.sub(r'^\s*[1-5]\.\s*(?:概述|进程与线程|内存管理|文件管理|输入/\s*输出管理|输入/输出管理)\s*$', '', text, flags=re.MULTILINE)
    return text

# Map of images per page
page_images = {
    3: ["p3_img1.jpeg"],
    4: ["p4_img1.jpeg"],
    5: ["p5_img1.jpeg", "p5_img2.jpeg"],
    6: ["p6_img1.jpeg", "p6_img2.jpeg"],
    7: ["p7_img1.jpeg"],
    8: ["p8_img1.jpeg"],
    12: ["p12_img1.jpeg"],
    13: ["p13_img1.jpeg"],
    18: ["p18_img1.jpeg", "p18_img2.jpeg"],
    24: ["p24_img1.jpeg"],
    25: ["p25_img1.jpeg"],
    27: ["p27_img1.jpeg"],
    28: ["p28_img1.jpeg"],
    29: ["p29_img1.jpeg"],
    31: ["p31_img1.jpeg"],
    32: ["p32_img1.jpeg"],
    33: ["p33_img1.jpeg", "p33_img2.jpeg"],
    34: ["p34_img1.jpeg"],
    35: ["p35_img1.jpeg", "p35_img2.jpeg"],
    36: ["p36_img1.jpeg"],
    37: ["p37_img1.jpeg"],
    39: ["p39_img1.jpeg"],
    40: ["p40_img1.jpeg"],
    41: ["p41_img1.jpeg"],
    45: ["p45_img1.jpeg"],
    46: ["p46_img1.jpeg"],
    49: ["p49_img1.jpeg"],
    50: ["p50_img1.jpeg", "p50_img2.jpeg"],
    54: ["p54_img1.jpeg"],
    58: ["p58_img1.jpeg"],
    59: ["p59_img1.jpeg"],
    60: ["p60_img1.jpeg"],
    61: ["p61_img1.jpeg"],
    62: ["p62_img1.jpeg"],
    65: ["p65_img1.jpeg"],
    68: ["p68_img1.jpeg"],
    69: ["p69_img1.jpeg"],
    75: ["p75_img1.jpeg"],
    76: ["p76_img1.jpeg"],
}

# Parse pages
page_chunks = raw_content.split("==================== PAGE ")

pages_data = {}
for chunk in page_chunks[1:]:
    lines = chunk.split("\n")
    p_num_str = lines[0].replace(" ====================", "").strip()
    p_num = int(p_num_str)
    p_text = clean_pua("\n".join(lines[1:]))
    pages_data[p_num] = p_text

# Chapter definitions
chapters = [
    {
        "filename": "第01章_计算机系统概述.md",
        "title": "《王道操作系统》· 第1章 计算机系统概述（综合大题全解）",
        "intro": "本章包含 1.2 操作系统发展历程（2道综合大题）。",
        "ch_name": "第1章 计算机系统概述",
        "sections": [
            {"title": "1.2 操作系统发展历程", "pages": [2]}
        ]
    },
    {
        "filename": "第02章_进程与线程.md",
        "title": "《王道操作系统》· 第2章 进程与线程（综合大题全解）",
        "intro": "本章包含 2.1 进程与线程简介 (1题), 2.2 CPU 调度 (10题), 2.3 同步与互斥 (29题), 2.4 死锁 (4题)，共计 44 道综合大题与统考真题。",
        "ch_name": "第2章 进程与线程",
        "sections": [
            {"title": "2.1 进程与线程简介", "pages": [3]},
            {"title": "2.2 CPU 调度", "pages": [4, 5, 6, 7, 8, 9]},
            {"title": "2.3 同步与互斥", "pages": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]},
            {"title": "2.4 死锁", "pages": [31, 32, 33]}
        ]
    },
    {
        "filename": "第03章_内存管理.md",
        "title": "《王道操作系统》· 第3章 内存管理（综合大题全解）",
        "intro": "本章包含 3.1 内存管理概念 (11题), 3.2 虚拟内存管理 (22题)，共计 33 道综合大题与历年统考真题。",
        "ch_name": "第3章 内存管理",
        "sections": [
            {"title": "3.1 内存管理概念", "pages": [34, 35, 36, 37, 38, 39, 40]},
            {"title": "3.2 虚拟内存管理", "pages": [41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56]}
        ]
    },
    {
        "filename": "第04章_文件管理.md",
        "title": "《王道操作系统》· 第4章 文件管理（综合大题全解）",
        "intro": "本章包含 4.2 目录与文件 (15题), 4.3 文件系统 (2题)，共计 17 道综合大题与历年统考真题。",
        "ch_name": "第4章 文件管理",
        "sections": [
            {"title": "4.2 目录与文件", "pages": [57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69]},
            {"title": "4.3 文件系统", "pages": [69]}
        ]
    },
    {
        "filename": "第05章_输入输出管理.md",
        "title": "《王道操作系统》· 第5章 输入/输出管理（综合大题全解）",
        "intro": "本章包含 5.1 I/O管理概述 (2题), 5.2 设备独立性软件 (3题), 5.3 磁盘与固态硬盘 (8题)，共计 13 道综合大题与历年统考真题。",
        "ch_name": "第5章 输入/输出管理",
        "sections": [
            {"title": "5.1 I/O 管理概述", "pages": [70]},
            {"title": "5.2 设备独立性软件", "pages": [71, 72]},
            {"title": "5.3 磁盘与固态硬盘", "pages": [73, 74, 75, 76, 77, 78]}
        ]
    }
]

def split_questions_from_pages(pages_list, sec_title):
    combined_text = ""
    for p in pages_list:
        text = pages_data.get(p, "")
        clean_lines = []
        for line in text.split("\n"):
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("第") and ("章" in line_str or "页" in line_str):
                continue
            if line_str in ["计算机系统概述", "进程与线程", "内存管理", "文件管理", "输入/ 输出管理", "输入/输出管理"]:
                continue
            if re.match(r'^\d+\.\d+\s*', line_str) and any(kw in line_str for kw in ["管理", "历程", "调度", "互斥", "死锁", "概念", "软件", "磁盘", "目录", "文件", "简介", "系统"]):
                continue
            clean_lines.append(line_str)
        combined_text += f"\n<!-- PAGE_{p} -->\n" + "\n".join(clean_lines)
    
    # Match real questions: line starting with \d+\. followed by text with length > 10 or Chinese characters
    q_matches = []
    for m in re.finditer(r'(?:\n|\A)(\d{1,2})\.\s*([^\n]*)', combined_text):
        q_num = int(m.group(1))
        first_line = m.group(2).strip()
        # skip isolated section numbers or empty titles
        if len(first_line) > 2 or "【" in first_line or "设" in first_line or "有" in first_line or "在" in first_line or "假" in first_line or "某" in first_line or "请" in first_line or "一" in first_line or "如" in first_line or "简" in first_line:
            q_matches.append(m)
    
    questions = []
    for i, m in enumerate(q_matches):
        q_num = int(m.group(1))
        start_pos = m.start()
        end_pos = q_matches[i+1].start() if i+1 < len(q_matches) else len(combined_text)
        
        q_content = combined_text[start_pos:end_pos].strip()
        
        preceding_text = combined_text[:start_pos]
        page_marks = re.findall(r'<!-- PAGE_(\d+) -->', preceding_text)
        origin_page = int(page_marks[-1]) if page_marks else pages_list[0]
        
        sub_pages = re.findall(r'<!-- PAGE_(\d+) -->', q_content)
        all_q_pages = [origin_page] + [int(sp) for sp in sub_pages]
        
        q_clean = re.sub(r'<!-- PAGE_\d+ -->', '', q_content).strip()
        
        # Remove question prefix like "1. " from inside content if needed, but keeping text clean
        q_images = []
        for qp in sorted(set(all_q_pages)):
            if qp in page_images:
                for img_name in page_images[qp]:
                    q_images.append(f"![题图及相关图表代码](../../images/os/{img_name})")
        
        questions.append({
            "num": q_num,
            "page": origin_page,
            "content": q_clean,
            "images": q_images
        })
    
    # deduplicate by question number sequentially
    deduped = []
    seen = set()
    for q in questions:
        if q["num"] not in seen:
            seen.add(q["num"])
            deduped.append(q)
        elif len(deduped) > 0 and q["num"] == deduped[-1]["num"]:
            # duplicate header, merge
            deduped[-1]["content"] += "\n" + q["content"]
            deduped[-1]["images"].extend(q["images"])
        else:
            deduped.append(q)
            
    return deduped

# Generate Markdown files
for ch in chapters:
    filepath = os.path.join(BASE_DIR, ch["filename"])
    total_q_count = 0
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {ch['title']}\n\n")
        f.write(f"> {ch['intro']}\n\n---\n\n")
        
        for sec in ch["sections"]:
            sec_title = sec["title"]
            f.write(f"## {sec_title}\n\n")
            
            qs = split_questions_from_pages(sec["pages"], sec_title)
            total_q_count += len(qs)
            
            for q in qs:
                f.write(f"### 第 {q['num']} 题（P{q['page']}）\n\n")
                f.write(f"{q['content']}\n\n")
                
                # Append relevant images if any
                if q["images"]:
                    for img_md in sorted(set(q["images"])):
                        f.write(f"{img_md}\n\n")
                
                f.write(f"> **【课程】** 操作系统\n")
                f.write(f"> **【章节】** {ch['ch_name']} · {sec_title}\n\n---\n\n")
                
    print(f"Generated {ch['filename']} ({total_q_count} questions)")

print("\nAll 5 chapters of 王道操作系统 综合大题 generated successfully!")
