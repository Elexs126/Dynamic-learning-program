# -*- coding: utf-8 -*-
"""
Precise Builder for 王道计算机网络 课后选择题 (6 Chapters, 562 MCQs)
"""

import os
import re
from net_img_map import net_page_images

BASE_DIR = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\04_计算机网络_选择题"
os.makedirs(BASE_DIR, exist_ok=True)

with open("scripts/net_full_text.txt", "r", encoding="utf-8") as f:
    raw_content = f.read()

def clean_text(text):
    text = text.replace("\uf001", "")
    text = text.replace("\uf0ee", "")
    text = text.replace("公众号：做题本集结地", "")
    text = re.sub(r'王道计网选择篇·[^\n]+', '', text)
    text = re.sub(r'·\s*第\s*\d+\s*页[，,]\s*共\s*\d+\s*页\s*·', '', text)
    text = re.sub(r'第\s*\d+\s*页[，,]\s*共\s*\d+\s*页', '', text)
    text = re.sub(r'（本节答案见原书\s*P\d+）', '', text)
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
    {"ch": "第1章 计算机网络体系结构", "file": "第01章_计算机网络体系结构.md", "sec": "1.1 计算机网络概述", "regex": r"1\.1\s*计算机网络概述"},
    {"ch": "第1章 计算机网络体系结构", "file": "第01章_计算机网络体系结构.md", "sec": "1.2 计算机网络体系结构与参考模型", "regex": r"1\.2\s*计算机网络体系结构与参考模型"},
    # Chapter 2
    {"ch": "第2章 物理层", "file": "第02章_物理层.md", "sec": "2.1 通信基础", "regex": r"2\.1\s*通信基础"},
    {"ch": "第2章 物理层", "file": "第02章_物理层.md", "sec": "2.2 传输介质", "regex": r"2\.2\s*传输介质"},
    {"ch": "第2章 物理层", "file": "第02章_物理层.md", "sec": "2.3 物理层设备", "regex": r"2\.3\s*物理层设备"},
    # Chapter 3
    {"ch": "第3章 数据链路层", "file": "第03章_数据链路层.md", "sec": "3.1 数据链路层的功能", "regex": r"3\.1\s*数据链路层的功能"},
    {"ch": "第3章 数据链路层", "file": "第03章_数据链路层.md", "sec": "3.2 组帧", "regex": r"3\.2\s*组帧"},
    {"ch": "第3章 数据链路层", "file": "第03章_数据链路层.md", "sec": "3.3 差错控制", "regex": r"3\.3\s*差错控制"},
    {"ch": "第3章 数据链路层", "file": "第03章_数据链路层.md", "sec": "3.4 流量控制与可靠传输机制", "regex": r"3\.4\s*流量控制与可靠传输机制"},
    {"ch": "第3章 数据链路层", "file": "第03章_数据链路层.md", "sec": "3.5 介质访问控制", "regex": r"3\.5\s*介质访问控制"},
    {"ch": "第3章 数据链路层", "file": "第03章_数据链路层.md", "sec": "3.6 局域网", "regex": r"3\.6\s*局域网"},
    {"ch": "第3章 数据链路层", "file": "第03章_数据链路层.md", "sec": "3.7 广域网", "regex": r"3\.7\s*广域网"},
    {"ch": "第3章 数据链路层", "file": "第03章_数据链路层.md", "sec": "3.8 数据链路层设备", "regex": r"3\.8\s*数据链路层设备"},
    # Chapter 4
    {"ch": "第4章 网络层", "file": "第04章_网络层.md", "sec": "4.1 网络层的功能", "regex": r"4\.1\s*网络层的功能"},
    {"ch": "第4章 网络层", "file": "第04章_网络层.md", "sec": "4.2 IPv4", "regex": r"4\.2\s*IPv4"},
    {"ch": "第4章 网络层", "file": "第04章_网络层.md", "sec": "4.3 IPv6", "regex": r"4\.3\s*IPv6"},
    {"ch": "第4章 网络层", "file": "第04章_网络层.md", "sec": "4.4 路由算法与路由协议", "regex": r"4\.4\s*路由算法与路由协议"},
    {"ch": "第4章 网络层", "file": "第04章_网络层.md", "sec": "4.5 IP多播", "regex": r"4\.5\s*IP\s*多播"},
    {"ch": "第4章 网络层", "file": "第04章_网络层.md", "sec": "4.6 移动IP", "regex": r"4\.6\s*移动\s*IP"},
    {"ch": "第4章 网络层", "file": "第04章_网络层.md", "sec": "4.7 网络层设备", "regex": r"4\.7\s*网络层设备"},
    # Chapter 5
    {"ch": "第5章 传输层", "file": "第05章_传输层.md", "sec": "5.1 传输层提供的服务", "regex": r"5\.1\s*传输层提供的服务"},
    {"ch": "第5章 传输层", "file": "第05章_传输层.md", "sec": "5.2 UDP", "regex": r"5\.2\s*UDP"},
    {"ch": "第5章 传输层", "file": "第05章_传输层.md", "sec": "5.3 TCP", "regex": r"5\.3\s*TCP"},
    # Chapter 6
    {"ch": "第6章 应用层", "file": "第06章_应用层.md", "sec": "6.1 网络应用模型", "regex": r"6\.1\s*网络应用模型"},
    {"ch": "第6章 应用层", "file": "第06章_应用层.md", "sec": "6.2 域名系统", "regex": r"6\.2\s*域名系统"},
    {"ch": "第6章 应用层", "file": "第06章_应用层.md", "sec": "6.3 文件传输协议", "regex": r"6\.3\s*文件传输协议"},
    {"ch": "第6章 应用层", "file": "第06章_应用层.md", "sec": "6.4 电子邮件", "regex": r"6\.4\s*电子邮件"},
    {"ch": "第6章 应用层", "file": "第06章_应用层.md", "sec": "6.5 万维网", "regex": r"6\.5\s*万维网"},
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
            if qp in net_page_images:
                for img_name in net_page_images[qp]:
                    q_images.append(f"![题图及相关拓扑代码](../../images/network/{img_name})")
        
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

total_net_questions = 0
for fname, ch_data in chapter_files.items():
    filepath = os.path.join(BASE_DIR, fname)
    ch_q_count = sum(len(s["questions"]) for s in ch_data["sections"])
    total_net_questions += ch_q_count
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# 《王道计算机网络》· {ch_data['ch_name']}（课后选择题全解）\n\n")
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
                
                f.write(f"> **【课程】** 计算机网络\n")
                f.write(f"> **【章节】** {ch_data['ch_name']} · {sec_title}\n\n---\n\n")
                
    print(f"Generated {fname} ({ch_q_count} items)")

print(f"\nAll Computer Network chapters generated! Total questions: {total_net_questions}")
