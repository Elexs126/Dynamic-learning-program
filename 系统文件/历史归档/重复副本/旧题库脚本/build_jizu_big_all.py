# -*- coding: utf-8 -*-
"""
Builder for 王道计算机组成原理 综合大题 (7 Chapters, 77 Questions)
"""

import os
import re
from jizu_big_img_map import jizu_big_page_images

BASE_DIR = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408\07_计算机组成原理_综合大题"
os.makedirs(BASE_DIR, exist_ok=True)

with open("scripts/jizu_big_full_text.txt", "r", encoding="utf-8") as f:
    raw_content = f.read()

def clean_text(text):
    text = text.replace("\uf001", "")
    text = text.replace("\uf0ee", "")
    text = text.replace("公众号：做题本最 TOP", "")
    text = text.replace("公众号：做题本最TOP", "")
    text = text.replace("公众号：做题本集结地", "")
    text = re.sub(r'王道课后题计组综合题·[^\n]+', '', text)
    text = re.sub(r'·\s*第\s*\d+\s*页[，,]\s*共\s*\d+\s*页\s*·', '', text)
    text = re.sub(r'第\s*\d+\s*页[，,]\s*共\s*\d+\s*页', '', text)
    text = re.sub(r'^\s*\d\.\s*(?:计算机系统概述|数据的表示和运算|存储系统|指令系统|中央处理器|总线|输入/输出系统|IO系统)\s*$', '', text, flags=re.MULTILINE)
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
    {"ch": "第1章 计算机系统概述", "file": "第01章_计算机系统概述.md", "sec": "1.3 计算机的性能指标", "regex": r"1\.3\s*计算机的性能指标"},
    # Chapter 2
    {"ch": "第2章 数据的表示和运算", "file": "第02章_数据的表示和运算.md", "sec": "2.2 运算方法和运算电路", "regex": r"2\.2\s*运算方法和运算电路"},
    {"ch": "第2章 数据的表示和运算", "file": "第02章_数据的表示和运算.md", "sec": "2.3 浮点数的表示与运算", "regex": r"2\.3\s*浮点数的表示与运算"},
    # Chapter 3
    {"ch": "第3章 存储系统", "file": "第03章_存储系统.md", "sec": "3.2 主存储器", "regex": r"3\.2\s*主存储器"},
    {"ch": "第3章 存储系统", "file": "第03章_存储系统.md", "sec": "3.3 主存储器与CPU的连接", "regex": r"3\.3\s*主存储器与\s*CPU\s*的连接"},
    {"ch": "第3章 存储系统", "file": "第03章_存储系统.md", "sec": "3.4 外部存储器", "regex": r"3\.4\s*外部存储器"},
    {"ch": "第3章 存储系统", "file": "第03章_存储系统.md", "sec": "3.5 高速缓冲存储器", "regex": r"3\.5\s*高速缓冲存储器"},
    {"ch": "第3章 存储系统", "file": "第03章_存储系统.md", "sec": "3.6 虚拟存储器", "regex": r"3\.6\s*虚拟存储器"},
    # Chapter 4
    {"ch": "第4章 指令系统", "file": "第04章_指令系统.md", "sec": "4.1 指令系统", "regex": r"4\.1\s*指令系统"},
    {"ch": "第4章 指令系统", "file": "第04章_指令系统.md", "sec": "4.2 指令的寻址方式", "regex": r"4\.2\s*指令的寻址方式"},
    {"ch": "第4章 指令系统", "file": "第04章_指令系统.md", "sec": "4.3 程序的机器级代码表示", "regex": r"4\.3\s*程序的机器级代码表示"},
    # Chapter 5
    {"ch": "第5章 中央处理器", "file": "第05章_中央处理器.md", "sec": "5.3 数据通路的功能和基本结构", "regex": r"5\.3\s*数据通路的功能和基本结构"},
    {"ch": "第5章 中央处理器", "file": "第05章_中央处理器.md", "sec": "5.4 控制器的功能和工作原理", "regex": r"5\.4\s*控制器的功能和工作原理"},
    {"ch": "第5章 中央处理器", "file": "第05章_中央处理器.md", "sec": "5.6 指令流水线", "regex": r"5\.6\s*指令流水线"},
    # Chapter 6
    {"ch": "第6章 总线", "file": "第06章_总线.md", "sec": "6.1 总线概述", "regex": r"6\.1\s*总线概述"},
    # Chapter 7
    {"ch": "第7章 输入/输出系统", "file": "第07章_输入输出系统.md", "sec": "7.3 I/O方式", "regex": r"7\.3\s*I/O\s*方式"},
]

sec_spans = []
for i, s in enumerate(sections_info):
    m = re.search(s["regex"], full_body)
    if m:
        sec_spans.append((m.start(), s))
    else:
        print(f"WARNING: Section not found: {s['sec']}")

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
        
        if len(q_clean) < 15 and any(kw in q_clean for kw in ["计算机", "运算", "存储", "指令", "中央处理器", "总线", "输入"]):
            continue
            
        q_images = []
        for qp in sorted(set(all_pages)):
            if qp in jizu_big_page_images:
                for img_name in jizu_big_page_images[qp]:
                    q_images.append(f"![题图及相关图表代码](../../images/jizu_big/{img_name})")
        
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

total_jizu_big_questions = 0
for fname, ch_data in chapter_files.items():
    filepath = os.path.join(BASE_DIR, fname)
    ch_q_count = sum(len(s["questions"]) for s in ch_data["sections"])
    total_jizu_big_questions += ch_q_count
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# 《王道计算机组成原理》· {ch_data['ch_name']}（综合应用大题全解）\n\n")
        f.write(f"> 本章共包含 {len(ch_data['sections'])} 个小节，共计 {ch_q_count} 道核心综合应用与设计大题。\n\n---\n\n")
        
        for s in ch_data["sections"]:
            sec_title = s["sec_title"]
            f.write(f"## {sec_title}\n\n")
            
            for q in s["questions"]:
                f.write(f"### 第 {q['num']} 题（P{q['page']}）\n\n")
                f.write(f"{q['content']}\n\n")
                
                if q["images"]:
                    for img_md in sorted(set(q["images"])):
                        f.write(f"{img_md}\n\n")
                
                f.write(f"> **【课程】** 计算机组成原理\n")
                f.write(f"> **【章节】** {ch_data['ch_name']} · {sec_title}\n\n---\n\n")
                
    print(f"Generated {fname} ({ch_q_count} items)")

print(f"\nAll Jizu BIG chapters generated! Total questions: {total_jizu_big_questions}")
