#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anti_operator_usage.py — 汇总 anti-operator（failure_type）的实际用法，供撰写定义与检查一致性。

背景：母算子曾有"只有裸标签、没有定义"的问题（盲测预测者指出，已通过
OPERATOR_DEFINITIONS.md 修复）。anti-operator 从未做过同样的检查——
但它的集中度更低（top3 45.7% vs 母算子 90.4%），值得核实是"真的更一致"
还是"只是标签更多、每个用得更少"。

用法: python anti_operator_usage.py --dir <raw_episodes> --out <md>
"""
import argparse
import io
import json
import os
import sys
from collections import Counter, defaultdict


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--out', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    ft = defaultdict(list)      # failure_type -> [(pid, route, why_bad)]
    no_type = []
    total_routes = 0

    for fn in sorted(f for f in os.listdir(args.dir)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        with io.open(os.path.join(args.dir, fn), encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception:
                    continue
                for r in (rec.get('naive_routes') or []):
                    if not isinstance(r, dict):
                        continue
                    total_routes += 1
                    t = (r.get('failure_type') or '').strip()
                    item = (rec.get('problem_id'), r.get('route', ''), r.get('why_bad_or_expensive', ''))
                    if t:
                        ft[t].append(item)
                    else:
                        no_type.append(item)

    L = ['# anti-operator（failure_type）实际用法证据', '']
    L.append('由 `anti_operator_usage.py` 从全部 Episode 的 `naive_routes` 汇总。')
    L.append('')
    L.append('## 用途')
    L.append('')
    L.append('母算子曾有"只有裸标签、没有定义"的问题（盲测预测者实测指出，已由')
    L.append('`OPERATOR_DEFINITIONS.md` 修复）。**anti-operator 从未做过同样的检查。**')
    L.append('')
    L.append('它的集中度更低（top3 45.7% vs 母算子 90.4%），值得核实：')
    L.append('这是**真的更一致**，还是**只是标签更多、每个用得更少**？')
    L.append('')
    L.append('## 统计')
    L.append('')
    L.append('- naive_routes 总数：%d' % total_routes)
    L.append('- 带 failure_type 的：%d' % (total_routes - len(no_type)))
    L.append('- **未标 failure_type 的：%d**' % len(no_type))
    L.append('- 不同 failure_type 数：%d' % len(ft))
    L.append('')
    counts = Counter({k: len(v) for k, v in ft.items()})
    tot = sum(counts.values()) or 1
    L.append('| failure_type | 次数 | 占比 |')
    L.append('|---|---:|---:|')
    for k, v in counts.most_common():
        L.append('| `%s` | %d | %.1f%% |' % (k, v, 100.0 * v / tot))
    L.append('')
    L.append('## 各标签的实际用法（判断是否一致使用）')
    L.append('')
    L.append('> 读法：若同一标签下的"为什么差"高度相似 → 定义清晰、使用一致；')
    L.append('> 若五花八门 → 该标签是筐，需要拆分或补定义。')
    L.append('')
    for k, v in counts.most_common():
        L.append('### `%s`（%d 次）' % (k, len(ft[k])))
        L.append('')
        for pid, route, why in ft[k][:8]:
            L.append('- `%s` — **路线**：%s' % (pid, (route or '')[:110].replace('\n', ' ')))
            if why:
                L.append('  - 为什么差：%s' % why[:190].replace('\n', ' '))
        L.append('')
    if no_type:
        L.append('## ⚠️ 未标 failure_type 的 naive_routes')
        L.append('')
        L.append('SPEC §6.1 要求 `naive_routes[].failure_type` 填 anti-operator 标签。以下未填：')
        L.append('')
        for pid, route, _ in no_type[:30]:
            L.append('- `%s` — %s' % (pid, (route or '')[:110].replace('\n', ' ')))
        L.append('')

    text = '\n'.join(L) + '\n'
    if args.out:
        with io.open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('routes=%d typed=%d untyped=%d distinct=%d' % (
            total_routes, total_routes - len(no_type), len(no_type), len(ft)))
        for k, v in counts.most_common(10):
            print('   %-38s %d' % (k, v))
    return 0


if __name__ == '__main__':
    sys.exit(main())
