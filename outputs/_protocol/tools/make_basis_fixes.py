#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_basis_fixes.py — 由分诊结果生成整改清单（不直接改数据）。

## 为什么用"标记事实"而不是"下判决"
`excerpt ⊂ raw_problem` 是一个**可测量的事实**，但它**不等于**
"这条 Episode 的题面是假的"——题面很短、或题面本身就是陈述句式时也会命中。
所以清单里写入的是**事实字段** `basis_flag`，而不是判决字段 `episode_basis`：

    "basis_flag": "evidence_excerpt_within_raw_problem"

下游看到这个标记，就知道**该条需要人工判断题面性质**，
而不是被告知"这条已经判定为讲义正文型"。

这与本项目一贯的做法一致：**机械工具报事实，判断留给人**。

用法: python make_basis_fixes.py --triage <episode_basis.json> --out <fixes.json>
"""
import argparse
import io
import json
import os
import sys

REASON = ('408 组 Critic（c2c3c4m7.md A-1）发现：部分条目的 evidence_excerpt '
          '与 raw_problem 大面积重合，即"题面"与"证据"是同一段文字，'
          '会使 E2（材料明确陈述该思路）退化为自证，并使 trigger 的题面可观察性不可判定。'
          '本字段只记录**可测量的事实**（excerpt 落在 raw_problem 内），不判定题面真伪。')


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--triage', default=os.path.abspath(
        os.path.join(here, '..', '..', '_index', 'episode_basis.json')))
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    d = json.load(io.open(args.triage, encoding='utf-8'))
    fixes = []
    for s in d.get('suspects') or []:
        if not s.get('excerpt_in_raw_problem'):
            continue
        fixes.append({
            'worker': s['worker'],
            'problem_id': s['problem_id'],
            'kind': 'set_field',
            'field': 'basis_flag',
            'new': 'evidence_excerpt_within_raw_problem',
            'reason': REASON,
            'source': 'critic/c2c3c4m7.md A-1 + _index/episode_basis.md',
        })

    spec = {
        'purpose': ('把"evidence_excerpt 落在 raw_problem 内"这一**可测量事实**写入条目，'
                    '使下游能筛出需要人工判断题面性质的条目。'),
        'not_a_verdict': ('本清单**不判定**题面真伪。命中该标记不等于"题面是假的"——'
                          '题面很短或本身是陈述句式时也会命中。'),
        'fixes': fixes,
        'deferred': [
            'C3 的 14–20 条"讲义正文型"条目是否应重做题面：需人工回读原文判断，'
            '不在机械清单范围内。',
            '这些条目的 trigger_signals 是否应从"题面可观察性"统计中剔除：'
            '已由 check_episode_basis.py 标出，聚合阶段可据此排除。',
            'M3 的 2 条 excerpt⊂raw_problem 与其余数学侧 0 条，'
            '未纳入本清单（数量少且已由 Critic 单独处理）。',
        ],
    }
    with io.open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(spec, ensure_ascii=False, indent=1))
    sys.stdout.reconfigure(encoding='utf-8')
    from collections import Counter
    print('fixes=%d  by worker: %s' % (len(fixes), dict(Counter(f['worker'] for f in fixes))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
