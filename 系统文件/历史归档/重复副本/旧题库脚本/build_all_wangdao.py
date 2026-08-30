# -*- coding: utf-8 -*-
"""
Master Builder for 王道 408 Materials:
- 王道计算机组成原理 课后选择题 (7章, 595题)
- 王道操作系统 综合大题 (5章, 78题)
"""

import os
import re

BASE_DIR = r"c:\Users\HP\Documents\antigravity\delightful-salk\王道计算机考研408"
os.makedirs(BASE_DIR, exist_ok=True)

# Helper function to save a markdown file
def save_chapter(sub_dir, filename, title, intro, questions):
    out_dir = os.path.join(BASE_DIR, sub_dir)
    os.makedirs(out_dir, exist_ok=True)
    full_path = os.path.join(out_dir, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"> {intro}\n\n---\n\n")
        for q in questions:
            section_str = f" · {q['section']}" if q.get('section') else ""
            f.write(f"### 第 {q['num']} 题（P{q['page']}）\n\n")
            f.write(f"{q['stem']}\n\n")
            if q.get('options'):
                f.write(f"{q['options']}\n\n")
            f.write(f"> **【课程】** {q['course']}\n")
            f.write(f"> **【章节】** {q['chapter']}{section_str}\n\n---\n\n")
    print(f"Saved: {sub_dir}/{filename} ({len(questions)} items)")

print("Helper ready")
