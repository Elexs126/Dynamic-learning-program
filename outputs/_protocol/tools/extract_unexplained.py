#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_unexplained.py — 为 unexplained_cases.md 抽取原始材料。

任务书 §16 要求 unexplained_cases.md 只收录两类问题：
  1. 现有问题空间语言解释起来别扭的；
  2. 标准解里出现了明显的新型结构变换、现有母算子都不贴的。
并且要求判断"是否值得新增母算子"——其中出现次数是关键依据。

本工具机械地做三件事，供 Unexplained worker 在此基础上撰写：
  A. 汇总全部 possible_new_operator 候选，按名称分组计数
  B. 汇总全部被标 UNKNOWN / UNEXPLAINED 的 Episode
  C. 按"出现次数 >= 3"的阈值给出**升级建议**（这是可机械判定的部分，
     语义上是否真该升级仍由 worker 判断）

用法:
  python extract_unexplained.py --dir <raw_episodes> --json <报告> --md <报告>
"""
import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict

PROMOTION_THRESHOLD = 3


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--json', default=None)
    ap.add_argument('--md', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    new_ops = defaultdict(list)      # name -> [ {problem_id, domain, why, definition} ]
    unknowns = []                    # 标 UNKNOWN/UNEXPLAINED 的 Episode
    no_match = []                    # existing_operator_matches 为空或只含 UNKNOWN
    total = 0

    for fn in sorted(f for f in os.listdir(args.dir)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        worker = os.path.splitext(fn)[0]
        with io.open(os.path.join(args.dir, fn), encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception:
                    continue
                total += 1
                pid = rec.get('problem_id')
                dom = rec.get('domain', '')
                notes = rec.get('notes') or ''

                pno = rec.get('possible_new_operator')
                if isinstance(pno, dict) and pno.get('name'):
                    new_ops[pno['name']].append({
                        'problem_id': pid, 'worker': worker, 'domain': dom,
                        'why_existing_fails': pno.get('why_existing_fails', ''),
                        'definition': pno.get('definition', ''),
                        'confidence': rec.get('confidence', ''),
                    })

                if re.search(r'UNKNOWN|UNEXPLAINED', notes) or \
                   rec.get('confidence') == 'unknown':
                    unknowns.append({
                        'problem_id': pid, 'worker': worker, 'domain': dom,
                        'main_obstacle': rec.get('main_obstacle', '')[:300],
                        'existing_operator_matches': rec.get('existing_operator_matches') or [],
                        'notes_excerpt': notes[:400],
                    })

                matches = rec.get('existing_operator_matches') or []
                real = [m for m in matches if isinstance(m, dict)
                        and m.get('operator_id') not in (None, '', 'UNKNOWN', 'UNEXPLAINED')]
                if not real:
                    no_match.append({
                        'problem_id': pid, 'worker': worker, 'domain': dom,
                        'main_obstacle': rec.get('main_obstacle', '')[:300],
                    })

    candidates = []
    for name, items in sorted(new_ops.items(), key=lambda kv: -len(kv[1])):
        candidates.append({
            'name': name,
            'occurrences': len(items),
            'domains': sorted({i['domain'] for i in items}),
            'recommend_promotion': len(items) >= PROMOTION_THRESHOLD,
            'instances': items,
        })

    summary = {
        'total_episodes': total,
        'candidate_new_operators': len(candidates),
        'candidates_recommended_for_promotion': sum(
            1 for c in candidates if c['recommend_promotion']),
        'promotion_threshold': PROMOTION_THRESHOLD,
        'unknown_episodes': len(unknowns),
        'episodes_without_operator_match': len(no_match),
        'candidates': candidates,
        'unknowns': unknowns,
        'no_match': no_match,
    }

    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(summary, ensure_ascii=False, indent=1))

    L = ['# unexplained_cases.md 原始材料（机械抽取）', '']
    L.append('由 `extract_unexplained.py` 生成，供 Unexplained worker 在此基础上撰写。')
    L.append('**本文件只做机械汇总，不做语义判断。**')
    L.append('')
    L.append('- 扫描 Episode：%d' % total)
    L.append('- 候选新母算子：%d（其中出现 >= %d 次、**建议升级**的：%d）' % (
        len(candidates), PROMOTION_THRESHOLD,
        summary['candidates_recommended_for_promotion']))
    L.append('- 标 UNKNOWN / UNEXPLAINED 的 Episode：%d' % len(unknowns))
    L.append('- 无任何母算子命中的 Episode：%d' % len(no_match))
    L.append('')
    L.append('## A. 候选新母算子（按出现次数排序）')
    L.append('')
    L.append('| 候选名 | 出现次数 | 领域 | 建议升级 |')
    L.append('|---|---:|---|---|')
    for c in candidates:
        L.append('| `%s` | %d | %s | %s |' % (
            c['name'], c['occurrences'], '、'.join(c['domains']),
            '**是**' if c['recommend_promotion'] else '待定（<3 次）'))
    L.append('')
    for c in candidates:
        L.append('### `%s`（%d 次）' % (c['name'], c['occurrences']))
        L.append('')
        for inst in c['instances']:
            L.append('- **%s**（%s, %s）' % (inst['problem_id'], inst['worker'], inst['domain']))
            if inst['why_existing_fails']:
                L.append('  - 现有标签为何不自然：%s' % inst['why_existing_fails'])
            if inst['definition']:
                L.append('  - 定义：%s' % inst['definition'])
        L.append('')
    L.append('## B. 标 UNKNOWN / UNEXPLAINED 的 Episode')
    L.append('')
    if unknowns:
        L.append('| problem_id | worker | 领域 | 主障碍摘要 |')
        L.append('|---|---|---|---|')
        for u in unknowns:
            L.append('| %s | %s | %s | %s |' % (
                u['problem_id'], u['worker'], u['domain'],
                u['main_obstacle'].replace('|', '/').replace('\n', ' ')[:160]))
        L.append('')
    else:
        L.append('（无）')
        L.append('')
    L.append('## C. 无任何母算子命中的 Episode')
    L.append('')
    if no_match:
        L.append('| problem_id | worker | 领域 | 主障碍摘要 |')
        L.append('|---|---|---|---|')
        for u in no_match:
            L.append('| %s | %s | %s | %s |' % (
                u['problem_id'], u['worker'], u['domain'],
                u['main_obstacle'].replace('|', '/').replace('\n', ' ')[:160]))
        L.append('')
    else:
        L.append('（无）')
        L.append('')
    L.append('---')
    L.append('')
    L.append('**给 Unexplained worker 的提醒**：')
    L.append('- "出现 >= 3 次"只是**机械阈值**，不等于语义上真该升级。')
    L.append('  必须回到实例核对它们是否真的共享同一结构，否则会把三个不同的东西硬凑成一个母算子。')
    L.append('- 反之，出现 1–2 次但结构新颖的，也可能值得升级——不要只看次数。')
    L.append('- 任务书要求至少收录 8 条；若材料不足，如实说明实际条数。')
    L.append('- **不得**把"其实能解释"的题塞进来充数。')

    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
