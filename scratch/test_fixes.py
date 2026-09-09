import json, re
from pathlib import Path

PROJECT = Path('.')

def test_math1_fixes():
    fixes = {
        '核心真题/数学一/2011年全国硕士研究生招生考试数学一真题.md': ('M1-11-A-T22', 10, 11),
        '核心真题/数学一/2012年全国硕士研究生招生考试数学一真题.md': ('M1-12-A-T21', 10, 11),
        '核心真题/数学一/2014年全国硕士研究生招生考试数学一真题.md': [
            ('M1-14-A-T20', 10, 11),
            ('M1-14-A-T21', 10, 11),
            ('M1-14-A-T23', 10, 11),
        ],
        '核心真题/数学一/2021年全国硕士研究生招生考试数学一真题.md': [
            ('M1-21-A-T18', 10, 12),
            ('M1-21-A-T19', 10, 12),
        ],
    }
    print("Testing Math 1 fixes...")
    for fpath, items in fixes.items():
        if isinstance(items, tuple): items = [items]
        text = (PROJECT / fpath).read_text(encoding='utf-8')
        for qid, old_p, new_p in items:
            pattern = rf'(### 【{qid}】第 \d+ 题.*?分值\*\* )(\d+)分'
            m = re.search(pattern, text, re.S)
            if m:
                print(f"  Found {qid}: current {m.group(2)}, target {new_p}")
            else:
                print(f"  FAILED to find {qid} in {fpath}")

if __name__ == '__main__':
    test_math1_fixes()
