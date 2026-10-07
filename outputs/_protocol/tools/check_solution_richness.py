#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_solution_richness.py — 测量盲测标准解的"推理文字"厚度。

背景：盲测评分要把预测的**结构性动作**与标准解对照。若标准解只有答案、
没有推理过程，评分者无从判断，只能标 UNVERIFIABLE。
本工具量化"有多少题的标准解真的含有可对照的推理文字"。

用法: python check_solution_richness.py --dir <blind_solutions> --md <报告>
"""
import argparse
import io
import os
import re
import sys

SECTION = re.compile(r'^##\s+(\S+)\s*$')
DETAILS = re.compile(r'<details>(.*?)</details>', re.S)
ANSWER_MARK = re.compile(r'【答案】|【参考答案】')
ANALYSIS_MARK = re.compile(r'【解析】')


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', '_index', 'blind_solutions')))
    ap.add_argument('--md', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    rows = []
    for fn in sorted(f for f in os.listdir(args.dir) if f.endswith('.md')):
        with io.open(os.path.join(args.dir, fn), encoding='utf-8') as f:
            text = f.read()
        # 按 ## 题号切块
        parts = re.split(r'^##\s+', text, flags=re.M)[1:]
        for p in parts:
            lines = p.split('\n')
            qid = lines[0].strip()
            body = '\n'.join(lines[1:])
            m = DETAILS.search(body)
            inner = m.group(1) if m else ''
            # 去掉标记与答案行后，剩余的"推理文字"长度
            stripped = ANSWER_MARK.sub('', ANALYSIS_MARK.sub('', inner))
            stripped = re.sub(r'\*\*|【[^】]*】|\\|[\s$]', '', stripped)
            ans = ANSWER_MARK.search(inner)
            ans_val = ''
            if ans:
                tail = inner[ans.end():].strip()
                ans_val = tail.split('\n')[0][:24]
            rows.append({
                'file': fn,
                'question_id': qid,
                'has_details': bool(m),
                'has_answer': bool(ans),
                'answer': ans_val,
                'reasoning_chars': len(stripped),
                'verdict': ('无可对照推理' if len(stripped) < 30 else
                            '推理偏薄' if len(stripped) < 120 else '推理充分'),
            })

    counts = {}
    for r in rows:
        counts[r['verdict']] = counts.get(r['verdict'], 0) + 1

    L = ['# 盲测标准解"推理厚度"测量', '']
    L.append('由 `check_solution_richness.py` 生成。')
    L.append('')
    L.append('## 为什么要测这个')
    L.append('')
    L.append('盲测评分要把预测的**结构性动作**与标准解对照。')
    L.append('若标准解只有答案、没有推理过程，评分者**无从判断**，只能标 `UNVERIFIABLE`。')
    L.append('本表量化"有多少题的标准解真的含有可对照的推理文字"。')
    L.append('')
    L.append('判据（去掉标记词与答案行后的剩余字符数）：')
    L.append('- `< 30` → **无可对照推理**（评分者必须标 UNVERIFIABLE，不得判 MISS）')
    L.append('- `30–120` → 推理偏薄（可部分对照，需谨慎）')
    L.append('- `>= 120` → 推理充分')
    L.append('')
    L.append('- 测量题数：%d' % len(rows))
    for k in ('推理充分', '推理偏薄', '无可对照推理'):
        L.append('- %s：%d' % (k, counts.get(k, 0)))
    L.append('')
    L.append('| 题号 | 有解析块 | 有答案 | 答案 | 推理字符数 | 判定 |')
    L.append('|---|---|---|---|---:|---|')
    for r in rows:
        L.append('| %s | %s | %s | %s | %d | **%s** |' % (
            r['question_id'], '是' if r['has_details'] else '否',
            '是' if r['has_answer'] else '否', r['answer'] or '',
            r['reasoning_chars'], r['verdict']))
    L.append('')
    L.append('## 给 SCORER 的强制要求')
    L.append('')
    L.append('- 判定为**无可对照推理**的题：**必须标 `UNVERIFIABLE`，不得判 MISS**。')
    L.append('  把"标准解没写过程"记成"预测者 MISS"，会**系统性低估**词表预测力。')
    L.append('- 判定为**推理偏薄**的题：可以评分，但必须在备注里说明依据薄弱。')
    L.append('- `UNVERIFIABLE` 既不是 HIT 也不是 MISS，必须在 SUMMARY 里**单列计数**。')
    L.append('')

    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('questions=%d  %s' % (len(rows), counts))
        for r in rows:
            if r['verdict'] != '推理充分':
                print('  %-16s %-14s chars=%d' % (r['question_id'], r['verdict'], r['reasoning_chars']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
