# -*- coding: utf-8 -*-
"""
Builder for 王道数据结构 综合应用题/解答题 (8 Chapters, 161 Questions)
"""

import os
import re
from dsa_big_img_map import dsa_big_page_images

BASE_DIR = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\06_数据结构_综合大题"
os.makedirs(BASE_DIR, exist_ok=True)

with open("scripts/dsa_big_full_text.txt", "r", encoding="utf-8") as f:
    raw_content = f.read()

def clean_text(text):
    text = text.replace("\uf001", "")
    text = text.replace("\uf0ee", "")
    text = text.replace("公众号：做题本集结地", "")
    text = text.replace("WD·数据结构·", "")
    text = re.sub(r'·\s*第\s*\d+\s*页[，,]\s*共\s*\d+\s*页\s*·', '', text)
    text = re.sub(r'第\s*\d+\s*页[，,]\s*共\s*\d+\s*页', '', text)
    text = re.sub(r'（答案见\s*P\d+）', '', text)
    text = re.sub(r'二、综合应用题', '', text)
    text = re.sub(r'^\s*\d\.\s*(?:绪论|线性表|栈[、\s]*队列和数组|串|树与二叉树|图|查找|排序)\s*$', '', text, flags=re.MULTILINE)
    text = text.replace("", "(").replace("", ")").replace("", "[").replace("", "]")
    text = text.replace("", "[").replace("", "]")
    text = text.replace("", "|")
    text = text.replace("", "∑")
    text = text.replace("", "'")
    return text

page_chunks = raw_content.split("==================== PAGE ")
full_body = ""
for chunk in page_chunks[1:]:
    lines = chunk.split("\n")
    p_num = int(lines[0].replace(" ====================", "").strip())
    p_text = clean_text("\n".join(lines[1:]))
    full_body += f"\n<!-- PAGE_{p_num} -->\n" + p_text

toc_end = full_body.find("<!-- PAGE_2 -->")
full_body = full_body[toc_end:]

sections_info = [
    # Chapter 1
    {"ch": "第1章 绪论", "file": "第01章_绪论.md", "sec": "1.1 数据结构的基本概念", "regex": r"1\.1\s*数据结构的基本概念"},
    {"ch": "第1章 绪论", "file": "第01章_绪论.md", "sec": "1.2 算法和算法评价", "regex": r"1\.2\s*算法和算法评价"},
    # Chapter 2
    {"ch": "第2章 线性表", "file": "第02章_线性表.md", "sec": "2.2 线性表的顺序表示", "regex": r"2\.2\s*线性表的顺序表示"},
    {"ch": "第2章 线性表", "file": "第02章_线性表.md", "sec": "2.3 线性表的链式表示", "regex": r"2\.3\s*线性表的链式表示"},
    # Chapter 3
    {"ch": "第3章 栈、队列和数组", "file": "第03章_栈_队列和数组.md", "sec": "3.1 栈", "regex": r"3\.1\s*栈"},
    {"ch": "第3章 栈、队列和数组", "file": "第03章_栈_队列和数组.md", "sec": "3.2 队列", "regex": r"3\.2\s*队列"},
    {"ch": "第3章 栈、队列和数组", "file": "第03章_栈_队列和数组.md", "sec": "3.3 栈和队列的应用", "regex": r"3\.3\s*栈和队列的应用"},
    # Chapter 4
    {"ch": "第4章 串", "file": "第04章_串.md", "sec": "4.2 串的模式匹配", "regex": r"4\.2\s*串的模式匹配"},
    # Chapter 5
    {"ch": "第5章 树与二叉树", "file": "第05章_树与二叉树.md", "sec": "5.1 树的基本概念", "regex": r"5\.1\s*树的基本概念"},
    {"ch": "第5章 树与二叉树", "file": "第05章_树与二叉树.md", "sec": "5.2 二叉树的概念", "regex": r"5\.2\s*二叉树的概念"},
    {"ch": "第5章 树与二叉树", "file": "第05章_树与二叉树.md", "sec": "5.3 二叉树的遍历和线索二叉树", "regex": r"5\.3\s*二叉树的遍历和线索二叉树"},
    {"ch": "第5章 树与二叉树", "file": "第05章_树与二叉树.md", "sec": "5.4 树、森林", "regex": r"5\.4\s*树[、\s]*森林"},
    {"ch": "第5章 树与二叉树", "file": "第05章_树与二叉树.md", "sec": "5.5 树与二叉树的应用", "regex": r"5\.5\s*树与二叉树的应用"},
    # Chapter 6
    {"ch": "第6章 图", "file": "第06章_图.md", "sec": "6.1 图的基本概念", "regex": r"6\.1\s*图的基本概念"},
    {"ch": "第6章 图", "file": "第06章_图.md", "sec": "6.2 图的存储及基本操作", "regex": r"6\.2\s*图的存储及基本操作"},
    {"ch": "第6章 图", "file": "第06章_图.md", "sec": "6.3 图的遍历", "regex": r"6\.3\s*图的遍历"},
    {"ch": "第6章 图", "file": "第06章_图.md", "sec": "6.4 图的应用", "regex": r"6\.4\s*图的应用"},
    # Chapter 7
    {"ch": "第7章 查找", "file": "第07章_查找.md", "sec": "7.2 顺序查找和折半查找", "regex": r"7\.2\s*顺序查找和折半查找"},
    {"ch": "第7章 查找", "file": "第07章_查找.md", "sec": "7.3 树形查找", "regex": r"7\.3\s*树形查找"},
    {"ch": "第7章 查找", "file": "第07章_查找.md", "sec": "7.4 B树和B+树", "regex": r"7\.4\s*B\s*树"},
    {"ch": "第7章 查找", "file": "第07章_查找.md", "sec": "7.5 散列(Hash)表", "regex": r"7\.5\s*散列"},
    # Chapter 8
    {"ch": "第8章 排序", "file": "第08章_排序.md", "sec": "8.2 插入排序", "regex": r"8\.2\s*插入排序"},
    {"ch": "第8章 排序", "file": "第08章_排序.md", "sec": "8.3 交换排序", "regex": r"8\.3\s*交换排序"},
    {"ch": "第8章 排序", "file": "第08章_排序.md", "sec": "8.4 选择排序", "regex": r"8\.4\s*选择排序"},
    {"ch": "第8章 排序", "file": "第08章_排序.md", "sec": "8.5 归并排序、基数排序和计数排序", "regex": r"8\.5\s*归并排序"},
    {"ch": "第8章 排序", "file": "第08章_排序.md", "sec": "8.6 各种内部排序算法的比较及应用", "regex": r"8\.6\s*各种内部排序算法"},
    {"ch": "第8章 排序", "file": "第08章_排序.md", "sec": "8.7 外部排序", "regex": r"8\.7\s*外部排序"},
]

sec_spans = []
for i, s in enumerate(sections_info):
    m = re.search(s["regex"], full_body)
    if m:
        sec_spans.append((m.start(), s))

sec_spans.sort(key=lambda x: x[0])

section_texts = []
for i in range(len(sec_spans)):
    start_pos, s_info = sec_spans[i]
    end_pos = sec_spans[i+1][0] if i+1 < len(sec_spans) else len(full_body)
    sec_content = full_body[start_pos:end_pos]
    section_texts.append((s_info, sec_content))

def parse_big_questions_in_section(sec_text, sec_title):
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
        
        # Filter out standalone headers
        if len(q_clean) < 15 and any(kw in q_clean for kw in ["线性表", "概述", "栈", "队列", "树", "图", "查找", "排序"]):
            continue
            
        q_images = []
        for qp in sorted(set(all_pages)):
            if qp in dsa_big_page_images:
                for img_name in dsa_big_page_images[qp]:
                    q_images.append(f"![题图及相关图表代码](../../images/dsa_big/{img_name})")
        
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

chapter_files = {}
for s_info, s_text in section_texts:
    fname = s_info["file"]
    if fname not in chapter_files:
        chapter_files[fname] = {
            "ch_name": s_info["ch"],
            "sections": []
        }
    qs = parse_big_questions_in_section(s_text, s_info["sec"])
    chapter_files[fname]["sections"].append({
        "sec_title": s_info["sec"],
        "questions": qs
    })

total_dsa_big_questions = 0
for fname, ch_data in chapter_files.items():
    filepath = os.path.join(BASE_DIR, fname)
    ch_q_count = sum(len(s["questions"]) for s in ch_data["sections"])
    total_dsa_big_questions += ch_q_count
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# 《王道数据结构》· {ch_data['ch_name']}（综合应用大题全解）\n\n")
        f.write(f"> 本章共包含 {len(ch_data['sections'])} 个小节，共计 {ch_q_count} 道核心综合应用题及代码设计题。\n\n---\n\n")
        
        for s in ch_data["sections"]:
            sec_title = s["sec_title"]
            f.write(f"## {sec_title}\n\n")
            
            for q in s["questions"]:
                f.write(f"### 第 {q['num']} 题（P{q['page']}）\n\n")
                f.write(f"{q['content']}\n\n")
                
                if q["images"]:
                    for img_md in sorted(set(q["images"])):
                        f.write(f"{img_md}\n\n")
                
                f.write(f"> **【课程】** 数据结构\n")
                f.write(f"> **【章节】** {ch_data['ch_name']} · {sec_title}\n\n---\n\n")
                
    print(f"Generated {fname} ({ch_q_count} items)")

print(f"\nAll Data Structure BIG chapters generated! Total questions: {total_dsa_big_questions}")
