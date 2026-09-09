import re, json
from pathlib import Path

PROJECT = Path('.')

def fix_math1():
    print("Fixing Math 1 markdown files...")
    # 2011
    p2011 = PROJECT / '核心真题/数学一/2011年全国硕士研究生招生考试数学一真题.md'
    t = p2011.read_text(encoding='utf-8')
    t = re.sub(r'(【M1-11-A-T22】.*?【分值】\*\* )10分', r'\g<1>11分', t, flags=re.S)
    p2011.write_text(t, encoding='utf-8')

    # 2012
    p2012 = PROJECT / '核心真题/数学一/2012年全国硕士研究生招生考试数学一真题.md'
    t = p2012.read_text(encoding='utf-8')
    t = re.sub(r'(【M1-12-A-T21】.*?【分值】\*\* )10分', r'\g<1>11分', t, flags=re.S)
    p2012.write_text(t, encoding='utf-8')

    # 2014
    p2014 = PROJECT / '核心真题/数学一/2014年全国硕士研究生招生考试数学一真题.md'
    t = p2014.read_text(encoding='utf-8')
    t = re.sub(r'(【M1-14-A-T20】.*?【分值】\*\* )10分', r'\g<1>11分', t, flags=re.S)
    t = re.sub(r'(【M1-14-A-T21】.*?【分值】\*\* )10分', r'\g<1>11分', t, flags=re.S)
    t = re.sub(r'(【M1-14-A-T23】.*?【分值】\*\* )10分', r'\g<1>11分', t, flags=re.S)
    p2014.write_text(t, encoding='utf-8')

    # 2021
    p2021 = PROJECT / '核心真题/数学一/2021年全国硕士研究生招生考试数学一真题.md'
    t = p2021.read_text(encoding='utf-8')
    t = re.sub(r'(【M1-21-A-T18】.*?【分值】\*\* )10分', r'\g<1>12分', t, flags=re.S)
    t = re.sub(r'(【M1-21-A-T19】.*?【分值】\*\* )10分', r'\g<1>12分', t, flags=re.S)
    p2021.write_text(t, encoding='utf-8')

    # 2026 T04 Option A
    p2026 = PROJECT / '核心真题/数学一/2026年全国硕士研究生招生考试数学一真题.md'
    t = p2026.read_text(encoding='utf-8')
    old_a = r'- \*\*A\.\*\* \$\\displaystyle \\int_0^{2\\pi} d\\theta \\int_0^{\\sqrt{2}} dr \\int_r^{\\sqrt{4-r^2}} f(r^2+z^2) r dz\$'
    new_a = r'- **A.** $\displaystyle \int_0^{2\pi} d\theta \int_0^2 dr \int_r^{\sqrt{4-r^2}} f(r^2+z^2) r dz$'
    if re.search(old_a, t):
        t = re.sub(old_a, new_a, t)
        print("  M1-26-C-T04 Option A restored to distractor limit 2")
    else:
        print("  WARNING: M1-26-C-T04 Option A pattern not found")
    p2026.write_text(t, encoding='utf-8')


def fix_408():
    print("Fixing 408 markdown files...")
    overrides_by_year = {
        2009: [('408-09-A-T44', 13)],
        2010: [('408-10-A-T42', 13), ('408-10-A-T43', 13)],
        2011: [('408-11-A-T42', 13), ('408-11-A-T43', 13)],
        2013: [('408-13-A-T42', 10), ('408-13-A-T43', 13)],
        2014: [('408-14-A-T42', 13)],
        2015: [('408-15-A-T42', 13), ('408-15-A-T43', 13)],
        2018: [('408-18-A-T42', 13), ('408-18-A-T43', 13)],
        2019: [('408-19-A-T42', 13), ('408-19-A-T43', 7), ('408-19-A-T44', 8), ('408-19-A-T45', 13), ('408-19-A-T46', 10)],
        2020: [('408-20-A-T42', 13), ('408-20-A-T43', 13)],
        2021: [('408-21-A-T42', 13), ('408-21-A-T43', 13)],
        2022: [('408-22-A-T42', 13), ('408-22-A-T43', 13)],
        2023: [('408-23-A-T42', 13), ('408-23-A-T43', 13)],
        2024: [('408-24-A-T44', 10)],
        2025: [('408-25-A-T42', 10), ('408-25-A-T43', 13)],
        2026: [('408-26-A-T44_stmt', 13)],
    }

    for y, items in overrides_by_year.items():
        path = PROJECT / f'核心真题/408/{y}年全国硕士研究生招生考试408计算机学科专业基础综合真题.md'
        t = path.read_text(encoding='utf-8')
        for qid, pt in items:
            if qid == '408-26-A-T44_stmt':
                t = t.replace('（本题满分 15 分）\n\n假定 43 题中计算机 C 的部分数据通路如题 44 所示。',
                              '（本题满分 13 分）\n\n假定 43 题中计算机 C 的部分数据通路如题 44 所示。')
            else:
                pat = rf'(【{qid}】.*?【分值】\*\* )\d+分'
                t = re.sub(pat, rf'\g<1>{pt}分', t, flags=re.S)
        path.write_text(t, encoding='utf-8')


def fix_canonical_baseline():
    print("Fixing canonical_sources_v1.json baseline...")
    p = PROJECT / '系统文件/系统配置/canonical_sources_v1.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    data['expected_unique_question_records'] = 8022
    for s in data['sources']:
        if s['source_id'] == 'WANGDAO_408':
            s['expected_record_count'] = 2895
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def fix_scoring_plans():
    print("Updating scoring plans for 408-12-A-T42, 408-13-A-T41, 408-12-A-T43, 408-14-A-T47...")
    p1 = PROJECT / '系统文件/脚本工具/05_标注与规范校验/cs408_2009_2012_review_v1/scoring_plan_v1.json'
    d1 = json.loads(p1.read_text(encoding='utf-8'))
    # 408-12-A-T42
    q42 = d1['questions']['408-12-A-T42']
    q42['notes'] = ["原总分13分；算法正确且线性时间的评分说明给12分（覆盖算法思想与实现部分），保留12/9分条件文字。"]
    for r in q42['rules']:
        if '未明确' in r['condition']:
            r['condition'] = r['condition'].replace('原文未明确该12分覆盖全部要求还是算法部分', '适用于算法思想与算法实现部分')
    # 408-12-A-T43
    q43 = d1['questions']['408-12-A-T43']
    q43['mode'] = 'partial'
    q43['notes'] = ["大纲计组大题分配总分13分；解析明确给出的分项合计10分，未分配步骤分为3分。"]
    p1.write_text(json.dumps(d1, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    p2 = PROJECT / '系统文件/脚本工具/05_标注与规范校验/cs408_2013_2026_review_v1/scoring_plan_v1.json'
    d2 = json.loads(p2.read_text(encoding='utf-8'))
    # 408-13-A-T41
    q41 = d2['questions']['408-13-A-T41']
    q41['notes'] = ["总分13分，最优档思想4分加实现7分加复杂度各1分为13分，与评分表合计一致。"]
    for r in q41['rules']:
        if '未明确' in r['condition']:
            r['condition'] = r['condition'].replace('与评分表及复杂度分的合计关系未明确', '作为独立特殊排序算法给分上限')
    # 408-14-A-T47
    q47 = d2['questions']['408-14-A-T47']
    q47['mode'] = 'partial'
    q47['notes'] = ["大纲计网大题分配总分9分；明确评分项合计8分，未分配步骤分为1分。"]
    p2.write_text(json.dumps(d2, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    fix_math1()
    fix_408()
    fix_canonical_baseline()
    fix_scoring_plans()
    print("All file fixes applied successfully!")
