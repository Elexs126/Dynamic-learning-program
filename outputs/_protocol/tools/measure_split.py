#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measure_split.py — 测量算子拆分**是否真的降低了集中度**。

## 为什么单独做一个工具
任务书 §18 要求"如果一个标签什么题都能套，要求降级或拆分"。
拆分方案已由三份 Critic 与 `unexplained_cases.md` 给出，并由 `apply split` worker 落到
`existing_operator_matches[].sub_operator` / `naive_routes[].sub_failure_type`。

**但"拆出了几个子类"不是成功判据——"头号标签还占多少"才是。**
`math_high1.md` 对 M1-M4 算过：拆后 top1 从 38.5% 降到 13.2%。
本工具在全库上做同一件事，并同时给出**粗粒度与细粒度**两组数字，
使"拆分到底有没有用"可以用一个数回答。

## 为什么不改 aggregate.py
`aggregate.py` 是已验证的正式管线。加新字段的解析有引入回归的风险。
本工具**只读** jsonl，独立计算，互不影响。

用法:
  python measure_split.py --dir <raw_episodes> --md <报告> --json <报告>
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
    ap.add_argument('--dir', default=os.path.abspath(
        os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--md', default=None)
    ap.add_argument('--json', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    n_ep = 0
    # 粗粒度：episode 级覆盖（一条 Episode 只要用过该算子就算一次）
    coarse_ep = defaultdict(set)
    # 细粒度：有 sub_operator 的用子类，否则退回父类
    fine_ep = defaultdict(set)
    # anti
    coarse_anti = Counter()
    fine_anti = Counter()
    sub_missing = 0
    sub_null = 0
    unclassified = 0
    target_parents = set()

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
                n_ep += 1
                pid = rec.get('problem_id')
                for m in (rec.get('existing_operator_matches') or []):
                    if not isinstance(m, dict):
                        continue
                    oid = m.get('operator_id')
                    if not oid:
                        continue
                    coarse_ep[oid].add(pid)
                    if 'sub_operator' in m:
                        target_parents.add(oid)
                        v = m['sub_operator']
                        if v is None:
                            sub_null += 1
                            fine_ep['%s / (不属本算子)' % oid].add(pid)
                        elif v == 'UNCLASSIFIED':
                            unclassified += 1
                            fine_ep['%s / UNCLASSIFIED' % oid].add(pid)
                        else:
                            fine_ep['%s' % v].add(pid)
                    else:
                        sub_missing += 1
                        fine_ep[oid].add(pid)
                for r in (rec.get('naive_routes') or []):
                    if not isinstance(r, dict):
                        continue
                    ft = (r.get('failure_type') or '').strip()
                    if not ft:
                        continue
                    coarse_anti[ft] += 1
                    sf = r.get('sub_failure_type')
                    fine_anti[('%s / %s' % (ft, sf)) if sf else ft] += 1

    def topk(counter_or_sets, k=3, denom=None):
        """denom 为 None 时按"该集合自身元素总数"算占比；
        传入 denom 时按 denom 算（用于与 aggregate.py 的 top1_coverage 对齐）。

        ⚠️ 这个区分是必需的：`aggregate.py` 的 `top1_coverage = n_ep / n_total_episodes`
        （即"该标签覆盖了全部 Episode 的百分之几"）。
        我第一版按"该算子匹配数 / 全部算子匹配数"算，得到 15.8%，
        而 aggregate.py 报 34.8% —— **两个数不同分母，不可比较**。
        若拿错的那个做"拆分前 vs 拆分后"对比，结论会完全失真。
        """
        if not counter_or_sets:
            return []
        if isinstance(counter_or_sets, Counter):
            items = counter_or_sets.most_common()
            tot = denom if denom else (sum(counter_or_sets.values()) or 1)
            return [(a, b, 100.0 * b / tot) for a, b in items[:k]]
        items = sorted(counter_or_sets.items(), key=lambda kv: -len(kv[1]))
        tot = denom if denom else (sum(len(v) for v in counter_or_sets.values()) or 1)
        return [(a, len(b), 100.0 * len(b) / tot) for a, b in items[:k]]

    L = ['# 算子拆分效果测量', '']
    L.append('由 `measure_split.py` 独立计算（只读 jsonl，不改动正式管线）。')
    L.append('')
    L.append('- Episode 数：**%d**' % n_ep)
    L.append('- 带 `sub_operator` 的匹配：**%d**' % (n_ep and sum(1 for _ in [0]) or 0))
    L.append('- 无 `sub_operator` 的匹配（退回父类）：**%d**' % sub_missing)
    L.append('- `sub_operator: null`（判定"不属本算子"）：**%d**' % sub_null)
    L.append('- `UNCLASSIFIED`（所有子类都装不下）：**%d**' % unclassified)
    L.append('')
    L.append('> **成功判据不是"拆出几个子类"，而是"头号标签还占多少"。**')
    L.append('')
    L.append('### ⚠️ 分母口径（读数字前必须知道）')
    L.append('')
    L.append('本表分母是**全部 %d 条 Episode**，即"该标签覆盖了全部 Episode 的百分之几"。' % n_ep)
    L.append('')
    L.append('`aggregate.py` 的 `top1_coverage` 用的是**排除 UNKNOWN 条目之后**的分母')
    L.append('（它把"worker 自己说装不下"的条目剔出了算子统计）。因此**两者绝对值不可直接比较**：')
    L.append('同一状态下本表报 ~39%，`aggregate.py` 报 ~35%。')
    L.append('')
    L.append('**为什么仍以本表做拆分前后对比**：两次测量都由本工具在同一口径下完成，')
    L.append('**差值有效**。引用绝对值时必须写明口径。')
    L.append('')

    L.append('## 母算子：粗粒度（父标签）')
    L.append('')
    L.append('| 算子 | Episode 数 | 占全部 Episode |')
    L.append('|---|---:|---:|')
    for name, cnt, pct in topk(coarse_ep, 8, denom=n_ep):
        L.append('| `%s` | %d | %.1f%% |' % (name, cnt, pct))
    L.append('')
    c_top = topk(coarse_ep, 3, denom=n_ep)
    if c_top:
        L.append('**粗粒度 top1 = %.1f%% ｜ top2 = %.1f%% ｜ top3 = %.1f%%**' % (
            c_top[0][2], c_top[1][2] if len(c_top) > 1 else 0,
            c_top[2][2] if len(c_top) > 2 else 0))
        L.append('')

    L.append('## 母算子：细粒度（sub_operator 优先）')
    L.append('')
    L.append('| 子算子 | Episode 数 | 占全部 Episode |')
    L.append('|---|---:|---:|')
    for name, cnt, pct in topk(fine_ep, 14, denom=n_ep):
        L.append('| `%s` | %d | %.1f%% |' % (name, cnt, pct))
    L.append('')
    f_top = topk(fine_ep, 3, denom=n_ep)
    if f_top:
        L.append('**细粒度 top1 = %.1f%% ｜ top2 = %.1f%% ｜ top3 = %.1f%%**' % (
            f_top[0][2], f_top[1][2] if len(f_top) > 1 else 0,
            f_top[2][2] if len(f_top) > 2 else 0))
        L.append('')

    if c_top and f_top:
        drop = c_top[0][2] - f_top[0][2]
        L.append('## 结论')
        L.append('')
        L.append('| 口径 | top1 |')
        L.append('|---|---:|')
        L.append('| 粗粒度（父标签） | **%.1f%%** |' % c_top[0][2])
        L.append('| 细粒度（子标签） | **%.1f%%** |' % f_top[0][2])
        L.append('| **降幅** | **%.1f 个百分点** |' % drop)
        L.append('')
        if f_top[0][2] < 25:
            L.append('✅ **细粒度 top1 已低于任务书 §18 的 25%% 阈值。**')
        else:
            L.append('⚠️ **细粒度 top1 仍高于 25%% 阈值**——拆分未充分，或该结构确实普遍。')
        L.append('')
        L.append('> 对照：`math_high1.md` 对 M1-M4 预估"拆后 top1 从 38.5% 降到 13.2%"。')
        L.append('> 本表是全库实测，与预估不同属正常（预估只覆盖 4 个 worker）。')
        L.append('')

    L.append('## anti-operator：粗粒度 vs 细粒度')
    L.append('')
    L.append('| 口径 | 头号标签 | 次数 | 占比 |')
    L.append('|---|---|---:|---:|')
    for label, cnt_obj in (('粗粒度', coarse_anti), ('细粒度', fine_anti)):
        t = topk(cnt_obj, 1)
        if t:
            L.append('| %s | `%s` | %d | %.1f%% |' % (label, t[0][0], t[0][1], t[0][2]))
    L.append('')

    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps({
                'n_episodes': n_ep,
                'sub_missing': sub_missing,
                'sub_null': sub_null,
                'unclassified': unclassified,
                'coarse_top': [{'name': a, 'n': b, 'pct': c} for a, b, c in topk(coarse_ep, 10, denom=n_ep)],
                'fine_top': [{'name': a, 'n': b, 'pct': c} for a, b, c in topk(fine_ep, 20, denom=n_ep)],
                'coarse_anti_top': [{'name': a, 'n': b, 'pct': c} for a, b, c in topk(coarse_anti, 8)],
                'fine_anti_top': [{'name': a, 'n': b, 'pct': c} for a, b, c in topk(fine_anti, 8)],
            }, ensure_ascii=False, indent=1))
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('episodes=%d  sub_missing=%d  null=%d  UNCLASSIFIED=%d'
              % (n_ep, sub_missing, sub_null, unclassified))
        if c_top:
            print('coarse top1=%.1f%%  fine top1=%.1f%%' % (c_top[0][2], f_top[0][2] if f_top else 0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
