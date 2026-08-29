# -*- coding: utf-8 -*-
"""
执行全书数学语法与排版质量修复与全方位检测 (Strict Quality Audit)
"""
import os
import re
import sys
from math_quality_engine import enhance_chapter_markdown

def audit_directory(base_dir):
    files = [f for f in os.listdir(base_dir) if f.endswith('.md')]
    print(f"\n================ 正在审计与增强目录: {os.path.basename(base_dir)} ================")
    
    total_naked = 0
    total_math_blocks = 0
    total_ru = 0
    
    for fname in sorted(files):
        fpath = os.path.join(base_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        enhanced = enhance_chapter_markdown(content)
        
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(enhanced)
            
        # 严格检测：剥离所有 $$...$$ 和 $...$ 后，检查普通文本中是否还有裸露的 \cmd
        no_display = re.sub(r'\$\$.*?\$\$', '', enhanced, flags=re.DOTALL)
        no_inline = re.sub(r'\$.*?\$', '', no_display)
        naked_commands = re.findall(r'\\[a-zA-Z]+', no_inline)
        
        math_count = len(re.findall(r'\$.*?\$', enhanced)) + len(re.findall(r'\$\$.*?\$\$', enhanced))
        ru_count = len(re.findall(r'入', enhanced))
        
        total_naked += len(naked_commands)
        total_math_blocks += math_count
        total_ru += ru_count
        
        print(f"【{fname}】")
        print(f"  - 真实裸 TeX 命令数: {len(naked_commands)} (合格标准: 0)")
        print(f"  - 标准 LaTeX 数学公式块: {math_count} 处")
        print(f"  - 汉字 '入' 残留统计: {ru_count} 处")
        if naked_commands:
            print(f"  - 存在裸命令样例: {naked_commands[:5]}")
        print("----------------------------------------------------------------")
        
    print(f"【总结】全书真实裸 TeX 命令总数: {total_naked}，生成标准数学公式: {total_math_blocks} 处！\n")

def main():
    dirs = [
        r"d:\考研动态学习项目\配套讲义\李永乐复习全书基础篇-线代学习册",
        r"d:\考研动态学习项目\配套讲义\李永乐线性代数辅导讲义【强化】",
        r"d:\考研动态学习项目\配套讲义\李良概率论与数理统计辅导讲义\01_基础篇",
        r"d:\考研动态学习项目\配套讲义\李良概率论与数理统计辅导讲义\02_强化篇",
        r"d:\考研动态学习项目\配套讲义\张宇高等数学18讲",
    ]
    for d in dirs:
        if os.path.exists(d):
            audit_directory(d)

if __name__ == "__main__":
    main()
