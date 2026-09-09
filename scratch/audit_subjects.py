import os, re

def audit():
    expected = {'数据结构': 45, '计算机组成原理': 45, '操作系统': 35, '计算机网络': 25}
    for y in range(2009, 2027):
        path = f'核心真题/408/{y}年全国硕士研究生招生考试408计算机学科专业基础综合真题.md'
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            content = f.read()

        blocks = re.split(r'\n#{2,4}\s+.*?(?:第\s*\d+\s*题|【408-)', content)
        by_subj = {'数据结构': 0, '计算机组成原理': 0, '操作系统': 0, '计算机网络': 0}
        by_subj_details = {'数据结构': [], '计算机组成原理': [], '操作系统': [], '计算机网络': []}

        for b in blocks[1:]:
            m_subj = re.search(r'> \*\*【科目】\*\* (.*?)\n', b)
            m_pts = re.search(r'> \*\*【分值】\*\* (\d+)分', b)
            m_id = re.search(r'> \*\*【唯一编号】\*\* `(.*?)`', b)
            if m_subj and m_pts:
                s = m_subj.group(1).strip()
                p = int(m_pts.group(1))
                qid = m_id.group(1) if m_id else ''
                if s in by_subj:
                    by_subj[s] += p
                    by_subj_details[s].append((qid, p))
                else:
                    # check if it matches partial
                    for k in by_subj:
                        if k in s:
                            by_subj[k] += p
                            by_subj_details[k].append((qid, p))
                            break

        tot = sum(by_subj.values())
        if tot != 150:
            print(f'=== {y} 408 Total={tot} (Diff={tot-150}) ===')
            for s in expected:
                if by_subj[s] != expected[s]:
                    bigs = [x for x in by_subj_details[s] if x[1] > 2]
                    choices = [x for x in by_subj_details[s] if x[1] == 2]
                    print(f'  {s}: cur={by_subj[s]}, exp={expected[s]}, diff={by_subj[s]-expected[s]} (choices={len(choices)}*{2}={len(choices)*2}, bigs={bigs})')

if __name__ == '__main__':
    audit()
