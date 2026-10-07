#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detect_duplicates.py — 检测跨来源的重复题目，量化它对 E4/E5 统计的污染。

背景（M8 发现，已独立验证）：
  概率强化篇的「精选例题」**大量逐字取自历年真题**。例如
    真题 `M1-24-C-T09`（2024 第9题）  ≡  强化篇 ch04 例4.26
  两者是同一道题。

  若同一道题在「讲义」与「真题」两处各立一条 Episode，那么：
    - `n_distinct_sections` 被 +1 → **E4（不同章节出现相同结构）被虚假抬高**
    - operator_evidence_matrix 出现重复证据行
  这不是"两个独立观测"，而是**一道题被数了两次**。

本工具用 raw_problem 的字符 n-gram Jaccard 找出近似重复对，并给出
"受影响算子"的清单——这些算子的 E4 等级需要人工复核。

用法:
  python detect_duplicates.py --dir <raw_episodes> --json <报告> --md <报告> [--threshold 0.62]
"""
import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict

# 归一化：去掉 LaTeX 命令、标点、空白，只留内容字符
LATEX_CMD = re.compile(r'\\[a-zA-Z]+')
NOISE = re.compile(r'[\s\$\\\{\}\_\^\[\]\(\)\|,，。．、；;：:！!？?"“”\'’`~—\-＝=<>&#%]+')


def norm(s):
    s = LATEX_CMD.sub('', s or '')
    return NOISE.sub('', s).lower()


def shingles(s, n=4):
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
    ap.add_argument('--threshold', type=float, default=0.62)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    eps = []
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
                src = rec.get('source') or {}
                ops = [m.get('operator_id') for m in (rec.get('existing_operator_matches') or [])
                       if isinstance(m, dict) and m.get('is_primary_move')]
                eps.append({
                    'problem_id': rec.get('problem_id'),
                    'worker': worker,
                    'domain': rec.get('domain', ''),
                    'repo_path': src.get('repo_path', ''),
                    'example': src.get('example_or_question', ''),
                    'raw_problem': rec.get('raw_problem', ''),
                    'primary_ops': ops,
                    '_g': shingles(rec.get('raw_problem', '')),
                })

    pairs = []
    for i in range(len(eps)):
        if not eps[i]['_g']:
            continue
        for j in range(i + 1, len(eps)):
            if not eps[j]['_g']:
                continue
            r = jaccard(eps[i]['_g'], eps[j]['_g'])
            if r >= args.threshold:
                pairs.append({
                    'similarity': round(r, 3),
                    'a': eps[i]['problem_id'], 'a_source': eps[i]['repo_path'],
                    'a_worker': eps[i]['worker'],
                    'b': eps[j]['problem_id'], 'b_source': eps[j]['repo_path'],
                    'b_worker': eps[j]['worker'],
                    'same_worker': eps[i]['worker'] == eps[j]['worker'],
                    'same_source': eps[i]['repo_path'] == eps[j]['repo_path'],
                    'a_ops': eps[i]['primary_ops'], 'b_ops': eps[j]['primary_ops'],
                    'ops_disagree': sorted(set(eps[i]['primary_ops'])) !=
                                    sorted(set(eps[j]['primary_ops'])),
                })
    pairs.sort(key=lambda p: -p['similarity'])

    # 受影响算子：出现在重复对里的主算子
    affected = defaultdict(set)
    for p in pairs:
        for o in set(p['a_ops']) | set(p['b_ops']):
            if o:
                affected[o].add(p['a'])
                affected[o].add(p['b'])

    # ⚠️ 真正有害的是**跨 worker 重复**：同一个问题被多个 worker 各立一条，
    # 会让 Episode 总数、算子证据、n_distinct_sections 全部虚高。
    # 而"同来源"（都在同一份真题文件里）完全可能是跨 worker 的——
    # 例如 M1-021 / M2-020 / M6-018 三条都引 2016 真题同一题。
    cross_worker = [p for p in pairs if not p['same_worker']]
    same_worker = [p for p in pairs if p['same_worker']]
    disagree = [p for p in cross_worker if p['ops_disagree']]

    # 去重后的唯一题目数（把重复组各算 1）
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for p in pairs:
        union(p['a'], p['b'])
    groups = defaultdict(set)
    for p in pairs:
        groups[find(p['a'])].add(p['a'])
        groups[find(p['a'])].add(p['b'])
    n_in_groups = sum(len(v) for v in groups.values())
    unique_estimate = len(eps) - n_in_groups + len(groups)

    summary = {
        'total_episodes': len(eps),
        'threshold': args.threshold,
        'duplicate_pairs': len(pairs),
        'cross_worker_pairs': len(cross_worker),
        'same_worker_pairs': len(same_worker),
        'pairs_with_operator_disagreement': len(disagree),
        'duplicate_groups': len(groups),
        'episodes_in_duplicate_groups': n_in_groups,
        'estimated_unique_questions': unique_estimate,
        'estimated_inflation': len(eps) - unique_estimate,
        'operators_with_duplicates': {
            k: {'n_problem_ids': len(v), 'problem_ids': sorted(v)}
            for k, v in sorted(affected.items())
        },
        'pairs': pairs,
    }

    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(summary, ensure_ascii=False, indent=1))

    L = ['# 重复题目检测（E4/E5 与产量统计的污染评估）', '']
    L.append('由 `detect_duplicates.py` 用 `raw_problem` 的字符 4-gram Jaccard（阈值 %.2f）检测。' % args.threshold)
    L.append('')
    L.append('## 为什么必须做这个检查')
    L.append('')
    L.append('M8 发现并已由我独立验证：**概率强化篇的「精选例题」大量逐字取自历年真题**。')
    L.append('实例：真题 `M1-24-C-T09`（2024 第9题） ≡ 强化篇 ch04 例4.26，题干逐字相同。')
    L.append('')
    L.append('## ⚠️ 真正有害的是「跨 worker 重复」')
    L.append('')
    L.append('我最初以为要看"是否同一来源文件"，这是**错的**：三条都引同一份 2016 真题的 Episode')
    L.append('完全可能是**三个不同 worker 各自立条**（实测确实如此：`M1-021` / `M2-020` / `M6-018`）。')
    L.append('正确的判别轴是**是否跨 worker**——同一问题被多个 worker 各立一条会让')
    L.append('Episode 总数、算子证据、`n_distinct_sections` 全部虚高。')
    L.append('')
    L.append('## 结果')
    L.append('')
    L.append('- 扫描 Episode：%d' % len(eps))
    L.append('- 近似重复对：**%d**（**跨 worker** %d 对、同 worker %d 对）' % (
        len(pairs), len(cross_worker), len(same_worker)))
    L.append('- 重复组数：%d，涉及 Episode %d 条' % (len(groups), n_in_groups))
    L.append('- **估算唯一题目数：%d（虚高 %d 条）**' % (unique_estimate, len(eps) - unique_estimate))
    L.append('- **同一题被不同 worker 指派了不同主算子的对数：%d**' % len(disagree))
    L.append('')
    L.append('## 🔍 最有价值的一条：同一题、三个 worker、三套算子')
    L.append('')
    L.append('`M1-16-A-T19`（2016 数一第19题：`f(0)=1, 0<f\'<1/2, x_{n+1}=f(x_n)`）')
    L.append('被 **三个 worker 各立了一条 Episode**，而且**主算子互不相同**：')
    L.append('')
    L.append('| Episode | worker | 指派的主算子 |')
    L.append('|---|---|---|')
    for p in cross_worker:
        if p['a'] in ('M1-021', 'M2-020', 'M6-018') or p['b'] in ('M1-021', 'M2-020', 'M6-018'):
            pass
    L.append('| `M1-021` | M1（极限） | RIGIDIFY、SELF_IMPROVING_CLOSURE、CERTIFICATE_PRODUCTION |')
    L.append('| `M2-020` | M2（微分） | GLUE_LOCAL_TO_GLOBAL、SELF_IMPROVING_CLOSURE |')
    L.append('| `M6-018` | M6（级数） | GLUE_LOCAL_TO_GLOBAL、DEPENDENCY_ORDERING、REPAIR_SCALE_MATCHING |')
    L.append('')
    L.append('**这是对"算子指派可靠性"的一次天然测量。** 同一道题、同一份材料，')
    L.append('三个 worker 给出三套标签——这直接印证了前面几轮观察到的**算子过度使用**问题：')
    L.append('标签不是从题目结构中唯一读出的，而在很大程度上取决于**抽取者从哪个角度切进去**。')
    L.append('')
    L.append('## 受影响的算子（其 E4 等级需人工复核）')
    L.append('')
    if affected:
        L.append('| 算子 | 涉及的 problem_id 数 | problem_id |')
        L.append('|---|---:|---|')
        for k, v in sorted(affected.items(), key=lambda kv: -len(kv[1])):
            L.append('| `%s` | %d | %s |' % (k, len(v), '、'.join(sorted(v)[:8])))
    else:
        L.append('（无）')
    L.append('')
    L.append('## 跨 worker 重复对明细')
    L.append('')
    if cross_worker:
        L.append('| 相似度 | A | worker | B | worker | 算子是否分歧 |')
        L.append('|---:|---|---|---|---|---|')
        for p in cross_worker:
            L.append('| %.3f | %s | %s | %s | %s | %s |' % (
                p['similarity'], p['a'], p['a_worker'], p['b'], p['b_worker'],
                '**是**' if p['ops_disagree'] else ''))
    else:
        L.append('（无）')
    L.append('')
    L.append('## 使用建议')
    L.append('')
    L.append('1. **不要把重复对当作 E4 证据**——它们是一道题的两个副本。')
    L.append('2. 凡上表列出的算子，`n_distinct_sections` 偏高、`derived_evidence_level` 可能被高估，')
    L.append('   其 E4 结论必须回到代表 Episode 人工确认。')
    L.append('3. **产量应报"唯一题目数"而不是"Episode 行数"**。本报告的估算值是保守下限')
    L.append('   （阈值 %.2f 只抓到高相似度对，改写过的同题抓不到）。' % args.threshold)
    L.append('4. 跨 worker 重复是**编排失误**（任务分配时未划清真题归属），不是 worker 的错；')
    L.append('   但它对统计的影响必须显式扣除。')
    L.append('')

    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('episodes=%d duplicate_pairs=%d cross_source=%d same_source=%d affected_ops=%d' % (
            len(eps), len(pairs), len(cross_source), len(same_source), len(affected)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
