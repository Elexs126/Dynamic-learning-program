# -*- coding: utf-8 -*-
"""
Builder for 王道操作系统 课后选择题 (5 Chapters, 656 MCQs)
"""

import os
import re
from os_mcq_img_map import os_mcq_page_images

BASE_DIR = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\05_操作系统_选择题"
os.makedirs(BASE_DIR, exist_ok=True)

with open("scripts/os_mcq_full_text.txt", "r", encoding="utf-8") as f:
    raw_content = f.read()

def clean_text(text):
    text = text.replace("\uf001", "")
    text = text.replace("\uf0ee", "")
    text = text.replace("公众号：做题本最 TOP", "")
    text = text.replace("公众号：做题本最TOP", "")
    text = text.replace("公众号：做题本集结地", "")
    text = re.sub(r'王道操作系统课后习题·[^\n]+', '', text)
    text = re.sub(r'·\s*第\s*\d+\s*页[，,]\s*共\s*\d+\s*页\s*·', '', text)
    text = re.sub(r'第\s*\d+\s*页[，,]\s*共\s*\d+\s*页', '', text)
    text = re.sub(r'（答案见原书\s*P\d+）', '', text)
    text = text.replace("", "(").replace("", ")").replace("", "[").replace("", "]")
    text = text.replace("", "[").replace("", "]")
    text = text.replace("", "|")
    text = text.replace("", "∑")
    text = text.replace("", "'")
    return text

# Map each page text
page_chunks = raw_content.split("==================== PAGE ")
full_body = ""
for chunk in page_chunks[1:]:
    lines = chunk.split("\n")
    p_num = int(lines[0].replace(" ====================", "").strip())
    p_text = clean_text("\n".join(lines[1:]))
    full_body += f"\n<!-- PAGE_{p_num} -->\n" + p_text

# Skip table of contents (Page 1)
toc_end = full_body.find("<!-- PAGE_2 -->")
full_body = full_body[toc_end:]

sections_info = [
    # Chapter 1
    {"ch": "第1章 计算机系统概述", "file": "第01章_计算机系统概述.md", "sec": "1.1 操作系统的基本概念", "regex": r"1\.1\s*操作系统的基本概念"},
    {"ch": "第1章 计算机系统概述", "file": "第01章_计算机系统概述.md", "sec": "1.2 操作系统发展历程", "regex": r"1\.2\s*操作系统发展历程"},
    {"ch": "第1章 计算机系统概述", "file": "第01章_计算机系统概述.md", "sec": "1.3 操作系统的运行环境", "regex": r"1\.3\s*操作系统的运行环境"},
    {"ch": "第1章 计算机系统概述", "file": "第01章_计算机系统概述.md", "sec": "1.6 虚拟机", "regex": r"1\.6\s*虚拟机"},
    # Chapter 2
    {"ch": "第2章 进程与线程", "file": "第02章_进程与线程.md", "sec": "2.1 进程与线程简介", "regex": r"2\.1\s*进程与线程简介"},
    {"ch": "第2章 进程与线程", "file": "第02章_进程与线程.md", "sec": "2.2 CPU调度", "regex": r"2\.2\s*CPU\s*调度"},
    {"ch": "第2章 进程与线程", "file": "第02章_进程与线程.md", "sec": "2.3 同步与互斥", "regex": r"2\.3\s*同步与互斥"},
    {"ch": "第2章 进程与线程", "file": "第02章_进程与线程.md", "sec": "2.4 死锁", "regex": r"2\.4\s*死锁"},
    # Chapter 3
    {"ch": "第3章 内存管理", "file": "第03章_内存管理.md", "sec": "3.1 内存管理概念", "regex": r"3\.1\s*内存管理概念"},
    {"ch": "第3章 内存管理", "file": "第03章_内存管理.md", "sec": "3.2 虚拟内存管理", "regex": r"3\.2\s*虚拟内存管理"},
    # Chapter 4
    {"ch": "第4章 文件管理", "file": "第04章_文件管理.md", "sec": "4.1 文件系统基础", "regex": r"4\.1\s*文件系统基础"},
    {"ch": "第4章 文件管理", "file": "第04章_文件管理.md", "sec": "4.2 目录与文件", "regex": r"4\.2\s*目录与文件"},
    {"ch": "第4章 文件管理", "file": "第04章_文件管理.md", "sec": "4.3 文件系统", "regex": r"4\.3\s*文件系统"},
    # Chapter 5
    {"ch": "第5章 输入/输出管理", "file": "第05章_输入输出管理.md", "sec": "5.1 I/O管理概述", "regex": r"5\.1\s*I/O\s*管理概述"},
    {"ch": "第5章 输入/输出管理", "file": "第05章_输入输出管理.md", "sec": "5.2 设备独立性软件", "regex": r"5\.2\s*设备独立性软件"},
    {"ch": "第5章 输入/输出管理", "file": "第05章_输入输出管理.md", "sec": "5.3 磁盘和固态硬盘", "regex": r"5\.3\s*磁盘和固态硬盘"},
]

# Find start position of each section
sec_spans = []
for i, s in enumerate(sections_info):
    m = re.search(s["regex"], full_body)
    if m:
        sec_spans.append((m.start(), s))
    else:
        print(f"WARNING: Section not found: {s['sec']}")

sec_spans.sort(key=lambda x: x[0])

# Slice text for each section
section_texts = []
for i in range(len(sec_spans)):
    start_pos, s_info = sec_spans[i]
    end_pos = sec_spans[i+1][0] if i+1 < len(sec_spans) else len(full_body)
    sec_content = full_body[start_pos:end_pos]
    section_texts.append((s_info, sec_content))

def format_options(text):
    lines = text.split("\n")
    res = []
    for line in lines:
        l = line.strip()
        if re.search(r'A\..*?B\..*?C\..*?D\.', l):
            parts = re.split(r'(?=[A-D]\.)', l)
            for p in parts:
                if p.strip():
                    res.append(p.strip())
        elif re.search(r'A\..*?B\.', l) and not re.search(r'C\.', l):
            parts = re.split(r'(?=[A-B]\.)', l)
            for p in parts:
                if p.strip():
                    res.append(p.strip())
        elif re.search(r'C\..*?D\.', l) and not re.search(r'A\.', l):
            parts = re.split(r'(?=[C-D]\.)', l)
            for p in parts:
                if p.strip():
                    res.append(p.strip())
        else:
            res.append(line)
    return "\n".join(res)

def parse_questions_in_section(sec_text):
    q_matches = list(re.finditer(r'(?:\n|\A)(\d{1,2})\.\s*([^\n]*)', sec_text))
    questions = []
    for i, m in enumerate(q_matches):
        q_num = int(m.group(1))
        start_pos = m.start()
        end_pos = q_matches[i+1].start() if i+1 < len(q_matches) else len(sec_text)
        
        q_chunk = sec_text[start_pos:end_pos].strip()
        
        preceding = sec_text[:start_pos]
        pm = re.findall(r'<!-- PAGE_(\d+) -->', preceding)
        orig_p = int(pm[-1]) if pm else 2
        
        sub_pm = re.findall(r'<!-- PAGE_(\d+) -->', q_chunk)
        all_pages = [orig_p] + [int(sp) for sp in sub_pm]
        
        q_clean = re.sub(r'<!-- PAGE_\d+ -->', '', q_chunk).strip()
        q_clean = re.sub(r'^\d\.\d[^\n]*\n', '', q_clean).strip()
        q_clean = re.sub(r'^第\s*\d+\s*章[^\n]*\n', '', q_clean).strip()
        
        q_clean = format_options(q_clean)
        
        q_images = []
        for qp in sorted(set(all_pages)):
            if qp in os_mcq_page_images:
                for img_name in os_mcq_page_images[qp]:
                    q_images.append(f"![题图及相关图表代码](../../images/os_mcq/{img_name})")
        
        questions.append({
            "num": q_num,
            "page": orig_p,
            "content": q_clean,
            "images": q_images
        })
    
    deduped = []
    seen = set()
    for q in questions:
        if q["num"] not in seen:
            seen.add(q["num"])
            deduped.append(q)
        elif len(deduped) > 0 and q["num"] == deduped[-1]["num"]:
            deduped[-1]["content"] += "\n" + q["content"]
            deduped[-1]["images"].extend(q["images"])
        else:
            deduped.append(q)
            
    return deduped

# Group by chapter file
chapter_files = {}
for s_info, s_text in section_texts:
    fname = s_info["file"]
    if fname not in chapter_files:
        chapter_files[fname] = {
            "ch_name": s_info["ch"],
            "sections": []
        }
    qs = parse_questions_in_section(s_text)
    chapter_files[fname]["sections"].append({
        "sec_title": s_info["sec"],
        "questions": qs
    })

total_os_questions = 0
for fname, ch_data in chapter_files.items():
    filepath = os.path.join(BASE_DIR, fname)
    ch_q_count = sum(len(s["questions"]) for s in ch_data["sections"])
    total_os_questions += ch_q_count
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# 《王道操作系统》· {ch_data['ch_name']}（课后选择题全解）\n\n")
        f.write(f"> 本章共包含 {len(ch_data['sections'])} 个小节，共计 {ch_q_count} 道精选选择题。\n\n---\n\n")
        
        for s in ch_data["sections"]:
            sec_title = s["sec_title"]
            f.write(f"## {sec_title}\n\n")
            
            for q in s["questions"]:
                f.write(f"### 第 {q['num']} 题（P{q['page']}）\n\n")
                f.write(f"{q['content']}\n\n")
                
                if q["images"]:
                    for img_md in sorted(set(q["images"])):
                        f.write(f"{img_md}\n\n")
                
                f.write(f"> **【课程】** 操作系统\n")
                f.write(f"> **【章节】** {ch_data['ch_name']} · {sec_title}\n\n---\n\n")
                
    print(f"Generated {fname} ({ch_q_count} items)")

print(f"\nAll OS MCQ chapters generated! Total questions: {total_os_questions}")
