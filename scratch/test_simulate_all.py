import os, re
from pathlib import Path

PROJECT = Path('.')

def simulate():
    # Map of question_id -> new_points
    overrides = {
        # Math 1 (7 questions)
        'M1-11-A-T22': 11,
        'M1-12-A-T21': 11,
        'M1-14-A-T20': 11,
        'M1-14-A-T21': 11,
        'M1-14-A-T23': 11,
        'M1-21-A-T18': 12,
        'M1-21-A-T19': 12,

        # 408
        '408-09-A-T44': 13,
        '408-10-A-T42': 13, '408-10-A-T43': 13,
        '408-11-A-T42': 13, '408-11-A-T43': 13,
        '408-13-A-T42': 10, '408-13-A-T43': 13,
        '408-14-A-T42': 13,
        '408-15-A-T42': 13, '408-15-A-T43': 13,
        '408-18-A-T42': 13, '408-18-A-T43': 13,
        '408-19-A-T42': 13, '408-19-A-T43': 7, '408-19-A-T44': 8, '408-19-A-T45': 13, '408-19-A-T46': 10,
        '408-20-A-T42': 13, '408-20-A-T43': 13,
        '408-21-A-T42': 13, '408-21-A-T43': 13,
        '408-22-A-T42': 13, '408-22-A-T43': 13,
        '408-23-A-T42': 13, '408-23-A-T43': 13,
        '408-24-A-T44': 10,
        '408-25-A-T42': 10, '408-25-A-T43': 13,
    }

    print("=== Simulating Math 1 ===")
    m1_bad = []
    for y in range(2008, 2027):
        path = PROJECT / f'核心真题/数学一/{y}年全国硕士研究生招生考试数学一真题.md'
        text = path.read_text(encoding='utf-8')
        total = 0
        blocks = re.split(r'\n#{2,4}\s+.*?【(M1-[^】]+)】', text)
        # blocks has [header, id1, body1, id2, body2, ...]
        for i in range(1, len(blocks), 2):
            qid = blocks[i]
            body = blocks[i+1]
            m = re.search(r'> \*\*【分值】\*\* (\d+)分', body)
            if not m:
                print(f"Missing points for {qid}")
                continue
            pt = overrides.get(qid, int(m.group(1)))
            total += pt
        if total != 150:
            print(f"  {y} Math 1 total = {total} (diff {total-150})")
            m1_bad.append(y)
    if not m1_bad:
        print("  All 19 Math 1 papers (2008-2026) are EXACTLY 150 points!")

    print("\n=== Simulating 408 ===")
    c408_bad = []
    for y in range(2009, 2027):
        path = PROJECT / f'核心真题/408/{y}年全国硕士研究生招生考试408计算机学科专业基础综合真题.md'
        text = path.read_text(encoding='utf-8')
        total = 0
        by_subj = {'数据结构': 0, '计算机组成原理': 0, '操作系统': 0, '计算机网络': 0}
        blocks = re.split(r'\n#{2,4}\s+.*?【(408-[^】]+)】', text)
        for i in range(1, len(blocks), 2):
            qid = blocks[i]
            body = blocks[i+1]
            m = re.search(r'> \*\*【分值】\*\* (\d+)分', body)
            s_m = re.search(r'> \*\*【科目】\*\* (.*?)\n', body)
            if not m:
                continue
            pt = overrides.get(qid, int(m.group(1)))
            total += pt
            if s_m:
                s = s_m.group(1).strip()
                for k in by_subj:
                    if k in s:
                        by_subj[k] += pt
                        break
        expected = {'数据结构': 45, '计算机组成原理': 45, '操作系统': 35, '计算机网络': 25}
        if total != 150 or any(by_subj[k] != expected[k] for k in expected):
            print(f"  {y} 408 total = {total}: DS={by_subj['数据结构']}, CO={by_subj['计算机组成原理']}, OS={by_subj['操作系统']}, CN={by_subj['计算机网络']}")
            c408_bad.append(y)
    if not c408_bad:
        print("  All 18 CS408 papers (2009-2026) are EXACTLY 150 points and 100% MATCH official subject targets (45, 45, 35, 25)!")

if __name__ == '__main__':
    simulate()
