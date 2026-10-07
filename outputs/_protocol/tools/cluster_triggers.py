#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cluster_triggers.py — 对 trigger_signals 做机械预聚类，供 Trigger Index worker 精修。

为什么需要：全库有 300+ 条 trigger 信号，让 worker 从零聚类既慢又不一致。
本工具用字符 n-gram Jaccard 相似度做贪心聚类，产出一份**草稿**。

⚠️ 草稿不是结论。与 family_seeds 的教训一样，机械聚类可能过细或把不同的东西
   凑在一起。worker 必须逐组核对语义，允许合并、拆分、丢弃。

用法:
  python cluster_triggers.py --dir <raw_episodes> --json <报告> --md <报告>
"""
import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict

NOISE = re.compile(r'[\s，。、；：（）()【】\[\]「」“”"\'`$\\{}_^|~!?！？,.;:]+')


def norm(s):
    return NOISE.sub('', s or '')


def grams(s, n=3):
    s = norm(s)
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--json', default=None)
    ap.add_argument('--md', default=None)
    ap.add_argument('--threshold', type=float, default=0.34,
                    help='Jaccard 相似度阈值（默认 0.34）')
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    signals = []
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
                matches = rec.get('existing_operator_matches') or []
                primary = None
                for m in matches:
                    if isinstance(m, dict) and m.get('is_primary_move'):
                        primary = m.get('operator_id')
                        break
                for i, t in enumerate(rec.get('trigger_signals') or []):
                    signals.append({
                        'problem_id': rec.get('problem_id'),
                        'worker': worker,
                        'domain': rec.get('domain', ''),
                        'index': i,
                        'signal': t,
                        'primary_operator': primary,
                        '_g': grams(t),
                    })

    # ---------------------------------------------------------------- 方法一：词面聚类
    # 实测结论：**失败**。484 条信号在 Jaccard 0.34 下聚成 482 组（480 个单例）。
    # 原因是这些信号"结构相近但用词极不相同"——例如
    #   "待证式可整理为 f'+φ'f=0 → 乘积求导指纹 → 构造 F=f·e^φ"
    #   "(II) 目标 f''+f'=1 形如 g'+g=0 → 见到 f'+f 型 → 乘 e^x"
    # 二者是同一个结构动作，字面重合却极低。
    # 因此词面聚类在本数据集上不可用，工具改为按主算子分组（见方法二），
    # 并把这次失败作为**负结果**记录下来——它说明 trigger 信号必须靠语义聚类，
    # 没有任何词面捷径，这本身是对数据质量的一个正面证据（表面形式足够多样）。
    order = sorted(range(len(signals)), key=lambda i: -len(signals[i]['signal']))
    assigned = [False] * len(signals)
    lexical_clusters = []
    for i in order:
        if assigned[i]:
            continue
        assigned[i] = True
        members = [i]
        for j in order:
            if assigned[j]:
                continue
            if jaccard(signals[i]['_g'], signals[j]['_g']) >= args.threshold:
                assigned[j] = True
                members.append(j)
        lexical_clusters.append(members)

    # ---------------------------------------------------------------- 方法二：按主算子分组
    # 这是**可靠**的分组：主算子是 worker 已判定的结构动作标签，
    # 按它分组得到语义上一致的桶（29 个算子 → ~29 组），
    # 供 Trigger Index worker 逐算子精修。
    by_op = defaultdict(list)
    for idx, s in enumerate(signals):
        by_op[s['primary_operator'] or '(未标主算子)'].append(idx)

    groups = []
    for op, idxs in sorted(by_op.items(), key=lambda kv: -len(kv[1])):
        doms = sorted({signals[i]['domain'] for i in idxs})
        groups.append({
            'group_id': 'G-' + (op if op != '(未标主算子)' else 'NONE'),
            'primary_operator': op,
            'size': len(idxs),
            'domains': doms,
            'cross_domain': len(doms) >= 2,
            'members': [{
                'problem_id': signals[i]['problem_id'],
                'worker': signals[i]['worker'],
                'domain': signals[i]['domain'],
                'signal': signals[i]['signal'],
            } for i in idxs],
        })

    clusters = lexical_clusters
    clusters.sort(key=lambda m: -len(m))

    out = []
    for k, members in enumerate(clusters):
        ops = defaultdict(int)
        doms = defaultdict(int)
        for i in members:
            if signals[i]['primary_operator']:
                ops[signals[i]['primary_operator']] += 1
            doms[signals[i]['domain']] += 1
        rep = max((signals[i] for i in members), key=lambda s: len(s['signal']))
        out.append({
            'draft_id': 'D-%03d' % (k + 1),
            'size': len(members),
            'representative': rep['signal'],
            'members': [{
                'problem_id': signals[i]['problem_id'],
                'worker': signals[i]['worker'],
                'domain': signals[i]['domain'],
                'signal': signals[i]['signal'],
                'primary_operator': signals[i]['primary_operator'],
            } for i in members],
            'operator_hint': dict(ops),
            'domains': sorted(doms),
        })

    sizes = [c['size'] for c in out]
    summary = {
        'total_signals': len(signals),
        'lexical_clustering': {
            'threshold': args.threshold,
            'clusters': len(lexical_clusters),
            'singletons': sum(1 for m in lexical_clusters if len(m) == 1),
            'verdict': ('FAILED — 词面聚类在本数据集上不可用；信号结构相近但用词极不相同。'
                        '这本身是正面证据：trigger 的表面形式足够多样，'
                        '不存在可以绕开语义聚类的词面捷径。'),
        },
        'by_primary_operator': {
            'groups': len(groups),
            'cross_domain_groups': sum(1 for g in groups if g['cross_domain']),
            'note': '这是可靠分组：主算子是 worker 已判定的结构动作标签。',
        },
        'draft_clusters': len(out),
        'clusters_ge2': sum(1 for x in sizes if x >= 2),
        'singletons': sum(1 for x in sizes if x == 1),
        'largest': max(sizes) if sizes else 0,
        'groups': groups,
        'clusters': out,
    }

    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(summary, ensure_ascii=False, indent=1))

    L = ['# trigger_signals 分组草稿', '']
    L.append('由 `cluster_triggers.py` 生成。本文件包含**两个**结果，一负一正。')
    L.append('')
    L.append('## ⚠️ 负结果：词面聚类失败了')
    L.append('')
    L.append('用字符 3-gram Jaccard（阈值 %.2f）对 **%d** 条 trigger 信号做贪心聚类：' % (
        args.threshold, len(signals)))
    L.append('得到 **%d 组，其中 %d 个是单例**。' % (
        len(lexical_clusters), summary['lexical_clustering']['singletons']))
    L.append('')
    L.append('原因：这些信号**结构相近但用词极不相同**。例如下面两条是同一个结构动作，字面重合却极低：')
    L.append('')
    L.append('- `"待证式可整理为 f\'+φ\'f=0 的形状 → 这是乘积求导公式逆用的指纹 → 提示存在 F(x)=f(x)e^{φ(x)}"`')
    L.append('- `"(II) 目标 f\'\'+f\'=1 形如 g\'+g=0 → 见到 f\'+f 型 → 乘 e^x"`')
    L.append('')
    L.append('**所以 trigger 聚类没有任何词面捷径，必须靠语义。** 这同时是一个**正面**证据：')
    L.append('trigger 的表面形式足够多样，说明抽取者没有套模板。')
    L.append('')
    L.append('（这与 `family_seeds.json` 的教训一致：机械签名曾把 91 条切成 51 个桶、36 个是单例。）')
    L.append('')
    L.append('## ✅ 正结果：按主算子分组')
    L.append('')
    L.append('主算子是 worker 已判定的结构动作标签，按它分组得到语义上一致的桶：')
    L.append('**%d 组，其中 %d 组跨领域。**' % (
        len(groups), summary['by_primary_operator']['cross_domain_groups']))
    L.append('')
    L.append('**Trigger Index worker 应逐组精修**：每组内把结构相同的信号合并成一条主条目，')
    L.append('把结构不同的拆开。目标 **25–45 条**主条目（任务书 §13）。')
    L.append('')
    L.append('| 组 | 主算子 | 信号数 | 领域 | 跨领域 |')
    L.append('|---|---|---:|---|---|')
    for g in groups:
        L.append('| %s | `%s` | %d | %s | %s |' % (
            g['group_id'], g['primary_operator'], g['size'],
            '、'.join(g['domains']), '是' if g['cross_domain'] else ''))
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 各组明细')
    L.append('')
    for g in groups:
        L.append('### `%s`（%d 条，%s）' % (
            g['primary_operator'], g['size'], '、'.join(g['domains'])))
        L.append('')
        for m in g['members']:
            L.append('- `%s`（%s, %s）%s' % (
                m['problem_id'], m['worker'], m['domain'],
                m['signal'].replace('\n', ' ')[:240]))
        L.append('')

    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print(text[:4000])
    return 0


if __name__ == '__main__':
    sys.exit(main())
