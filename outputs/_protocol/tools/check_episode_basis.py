#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_episode_basis.py — 核验"raw_problem 是否真的是题面"。

背景：408 组 Critic（c2c3c4m7.md A-1）发现 C3 有 14/24 条的 `raw_problem`
不是题面，而是讲义说明性正文/答案解析。后果两条：
  1. `evidence_excerpt` 与 `raw_problem` 大面积重合 → "题面"与"证据"是同一段文字
     → E2 判定退化为自证；
  2. `trigger_signals` 的"题面可观察性"不可判定。

本工具用两个可复算的机械代理指标来定位这类条目：
  A. `evidence_excerpt` 是 `raw_problem` 的子串（重合）
  B. `raw_problem` 末尾 260 字内不含任何问句特征词

两个指标都不是判决，只是**分诊**——必须回读原文才能定性。
"""
import argparse
import io
import json
import os
import re
import sys

NOISE = re.compile(r'[\s\$\\\{\}\_\^\[\]\(\)\|,，。．、；;：:！!？?"“”\'’`~—\-＝=<>&#%]+')
ASK = re.compile(r'[？?]|求|试|证明|说明|设计|简述|为什么|多少|计算|判断|比较|指出|写出')


def norm(s):
    return NOISE.sub('', s or '')


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(
        os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--json', default=None)
    ap.add_argument('--md', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    per_worker = {}
    suspects = []
    for fn in sorted(f for f in os.listdir(args.dir)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        w = os.path.splitext(fn)[0]
        n = overlap = noq = 0
        with io.open(os.path.join(args.dir, fn), encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception:
                    continue
                n += 1
                rp_raw = rec.get('raw_problem') or ''
                rp = norm(rp_raw)
                ex = norm(rec.get('evidence_excerpt'))
                ov = bool(ex and rp and (ex in rp or (len(ex) > 40 and ex[:60] in rp)))
                # 末尾是否无问句特征
                tail = rp_raw[-260:]
                nq = not bool(ASK.search(tail))
                if ov:
                    overlap += 1
                if nq:
                    noq += 1
                if ov or nq:
                    suspects.append({
                        'problem_id': rec.get('problem_id'),
                        'worker': w,
                        'excerpt_in_raw_problem': ov,
                        'tail_has_no_question_marker': nq,
                        'raw_problem_tail': tail[-120:].replace('\n', ' '),
                    })
        per_worker[w] = {'n': n, 'overlap': overlap, 'no_question_tail': noq}

    L = ['# "raw_problem 是否真的是题面"分诊', '']
    L.append('由 `check_episode_basis.py` 生成。')
    L.append('')
    L.append('## 背景')
    L.append('')
    L.append('408 组 Critic（`c2c3c4m7.md` A-1）发现 C3 有 14/24 条的 `raw_problem`')
    L.append('**不是题面**，而是讲义说明性正文/答案解析。后果：')
    L.append('')
    L.append('1. `evidence_excerpt` 与 `raw_problem` 重合 → **"题面"与"证据"是同一段文字**')
    L.append('   → E2 判定（"材料明确陈述了该思路"）**退化为自证**；')
    L.append('2. `trigger_signals` 的"题面可观察性"**不可判定**。')
    L.append('')
    L.append('## ⚠️ 这是分诊，不是判决')
    L.append('')
    L.append('两个指标都是机械代理，都会误伤（例如题面很短、或题面本身是陈述句式的填空题）。')
    L.append('**必须回读原文**才能定性。')
    L.append('')
    L.append('## 各 worker 命中率')
    L.append('')
    L.append('| worker | Episode | excerpt⊂raw_problem | 末尾无问句特征 |')
    L.append('|---|---:|---:|---:|')
    for w in sorted(per_worker):
        d = per_worker[w]
        L.append('| %s | %d | **%d** | %d |' % (w, d['n'], d['overlap'], d['no_question_tail']))
    L.append('')
    L.append('> 读法：`excerpt⊂raw_problem` 高 = "题面即证据"，是最强的信号；')
    L.append('> `末尾无问句特征` 高 = 可能是陈述性正文，但也可能是填空题或短题面。')
    L.append('')
    L.append('## 明细（%d 条）' % len(suspects))
    L.append('')
    L.append('| problem_id | worker | 题面即证据 | 末尾无问句 | raw_problem 结尾 |')
    L.append('|---|---|---|---|---|')
    for s in suspects:
        L.append('| %s | %s | %s | %s | %s |' % (
            s['problem_id'], s['worker'],
            '✅' if s['excerpt_in_raw_problem'] else '',
            '✅' if s['tail_has_no_question_marker'] else '',
            s['raw_problem_tail'].replace('|', '/')[:90]))
    L.append('')
    L.append('## 建议处置')
    L.append('')
    L.append('1. 对 `excerpt⊂raw_problem` 为真的条目：**它们不是"题目型"Episode**，')
    L.append('   而是"讲义正文型"轨迹。应显式标注（如 `episode_basis: "lecture_prose"`），')
    L.append('   使下游不会把它们当成有可观察 trigger 的题目。')
    L.append('2. 这类条目的 `trigger_signals` **不得**用于"题面可观察性"统计。')
    L.append('3. **不要删除它们**——推理内容本身有价值，删掉是损失；')
    L.append('   但必须让它们**不能冒充**题目型 Episode。')
    L.append('')

    text = '\n'.join(L) + '\n'
    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps({'per_worker': per_worker, 'suspects': suspects},
                               ensure_ascii=False, indent=1))
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        for w in sorted(per_worker):
            d = per_worker[w]
            print('%-4s n=%-4d overlap=%-4d no_question_tail=%d'
                  % (w, d['n'], d['overlap'], d['no_question_tail']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
