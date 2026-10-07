#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_operation_labels.py — 校验 `key_transitions[].operation` 是否真的描述了结构动作。

## 为什么需要这道闸门
408 组 Critic（c2c3c4m7.md A-2 / A-3）发现两类缺陷，**都会直接污染下游检索**：

1. **无算子标签**（C2 23/54 条）：`operation` 填的是"转变前的假设/提问/观察"，
   而不是动作。例：`C2-024 T1 operation = "就近贪心的局部最优无法保证全局公平"`
   ——真动作被挤到 `after_state` 里。下游按 `operation` 检索"这题做了什么结构动作"，
   会检索到一句**什么都没做的事**。
   对照：C3 为 0/24、M7 为 1/60 → **C2 的 42.6% 是异常值**。

2. **anti-operator 出现在动作位置**（C3-012 / C3-015）：
   `operation` 里写着 `STRUCTURAL_PROGRESS`（已建议废弃）或
   `PROXY_OBJECTIVE_DRIFT`（anti-operator，描述**失败**）。
   在"动作"位置描述"失败模式"，方向是反的。

## 判据（机械可复算）
对每条 transition 的 `operation`：
  * 抽取其中的 `UPPER_SNAKE` 词元
  * **不含任何 SPEC §7 母算子** → `NO_OPERATOR_LABEL`
  * **含 SPEC §8 anti-operator** → `ANTI_OPERATOR_IN_ACTION`
  * 含已建议废弃的标签 → `DEPRECATED_LABEL_IN_ACTION`

⚠️ 这是**分诊**：`operation` 用自然语言描述动作而没写标签，本身可能是写法差异，
不一定是错误。必须回读原文判断"它到底有没有描述一个动作"。

用法:
  python check_operation_labels.py --spec <EPISODE_SPEC.md> --dir <raw_episodes>
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

TOKEN_RE = re.compile(r'\b([A-Z][A-Z0-9_]{3,})\b')
# 已由 Critic / OPERATOR_DEFINITIONS 判定"语义过泛、建议废弃"的标签
DEPRECATED = {'STRUCTURAL_PROGRESS'}


def parse_vocab(spec_text, header):
    m = re.search(re.escape(header) + r'(.*?)(?=\n##\s|\Z)', spec_text, re.S)
    if not m:
        return set()
    body = m.group(1)
    fences = re.findall(r'```(.*?)```', body, re.S)
    text = '\n'.join(fences) if fences else body
    labels = set(re.findall(r'\b([A-Z][A-Z0-9_]{2,})\b', text))
    labels |= set(re.findall(r'`([A-Z][A-Z0-9_]{2,})`', body))
    return labels


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--spec', default=os.path.abspath(
        os.path.join(here, '..', '..', 'EPISODE_SPEC.md')))
    ap.add_argument('--dir', default=os.path.abspath(
        os.path.join(here, '..', '..', '..', 'raw_episodes')))
    ap.add_argument('--json', default=None)
    ap.add_argument('--md', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    spec = io.open(args.spec, encoding='utf-8').read()
    mother = parse_vocab(spec, '## 7.')
    anti = parse_vocab(spec, '## 8.')

    per_worker = defaultdict(lambda: Counter())
    issues = []
    for fn in sorted(f for f in os.listdir(args.dir)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        w = os.path.splitext(fn)[0]
        with io.open(os.path.join(args.dir, fn), encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception:
                    continue
                for i, t in enumerate(rec.get('key_transitions') or []):
                    if not isinstance(t, dict):
                        continue
                    op = str(t.get('operation') or '')
                    per_worker[w]['transitions'] += 1
                    toks = set(TOKEN_RE.findall(op))
                    has_mother = bool(toks & mother)
                    bad_anti = sorted(toks & anti)
                    bad_dep = sorted(toks & DEPRECATED)
                    if bad_anti:
                        kind = 'ANTI_OPERATOR_IN_ACTION'
                    elif bad_dep:
                        kind = 'DEPRECATED_LABEL_IN_ACTION'
                    elif not has_mother:
                        kind = 'NO_OPERATOR_LABEL'
                    else:
                        continue
                    per_worker[w][kind] += 1
                    issues.append({
                        'problem_id': rec.get('problem_id'),
                        'worker': w,
                        'transition_index': i,
                        'kind': kind,
                        'operation_head': op[:110].replace('\n', ' '),
                        'tokens_found': sorted(toks)[:8],
                    })

    L = ['# `key_transitions[].operation` 是否描述了结构动作', '']
    L.append('由 `check_operation_labels.py` 生成。母算子词表解析自 SPEC §7，'
             'anti-operator 解析自 §8。')
    L.append('')
    L.append('- 母算子词表：%d 个 ｜ anti-operator 词表：%d 个' % (len(mother), len(anti)))
    L.append('- **命中问题条目：%d**' % len(issues))
    L.append('')
    L.append('## 为什么这道闸门重要')
    L.append('')
    L.append('下游按 `operation` 检索"这题做了什么结构动作"。')
    L.append('若 `operation` 填的是"转变前的假设/提问"，或填了描述**失败**的 anti-operator，')
    L.append('检索结果就会指向**什么都没做的事**，或指向**反方向**。')
    L.append('')
    L.append('## ⚠️ 这是分诊，不是判决')
    L.append('')
    L.append('`operation` 用自然语言描述动作而没写标签，**本身可能是写法差异，不一定是错误**。')
    L.append('必须回读原文判断"它到底有没有描述一个动作"。')
    L.append('')
    L.append('## 各 worker 命中率')
    L.append('')
    L.append('| worker | transition 数 | 无算子标签 | anti 在动作位 | 已废弃标签 | 问题占比 |')
    L.append('|---|---:|---:|---:|---:|---:|')
    for w in sorted(per_worker):
        d = per_worker[w]
        tot = d['transitions'] or 1
        bad = d['NO_OPERATOR_LABEL'] + d['ANTI_OPERATOR_IN_ACTION'] + d['DEPRECATED_LABEL_IN_ACTION']
        L.append('| %s | %d | %d | %d | %d | %.0f%% |' % (
            w, d['transitions'], d['NO_OPERATOR_LABEL'],
            d['ANTI_OPERATOR_IN_ACTION'], d['DEPRECATED_LABEL_IN_ACTION'],
            100.0 * bad / tot))
    L.append('')
    if issues:
        L.append('## 明细（%d 条）' % len(issues))
        L.append('')
        L.append('| problem_id | worker | T# | 类型 | operation 开头 |')
        L.append('|---|---|---:|---|---|')
        for it in issues[:120]:
            L.append('| %s | %s | %d | `%s` | %s |' % (
                it['problem_id'], it['worker'], it['transition_index'],
                it['kind'], it['operation_head'].replace('|', '/')[:80]))
        if len(issues) > 120:
            L.append('')
            L.append('（其余 %d 条见 JSON）' % (len(issues) - 120))
        L.append('')
    L.append('## 建议处置')
    L.append('')
    L.append('1. `ANTI_OPERATOR_IN_ACTION` / `DEPRECATED_LABEL_IN_ACTION`：**机械可改**——')
    L.append('   从 `operation` 里删掉该标签（保留动作描述），或换成对应的母算子。')
    L.append('2. `NO_OPERATOR_LABEL`：需回读——若 `operation` 确实是"假设/提问/观察"，')
    L.append('   应把真动作从 `after_state` 移回 `operation`，原假设移入 `why_triggered`。')
    L.append('3. **不应删除这些条目**：缺陷在字段落位，不在内容本身。')
    L.append('')

    text = '\n'.join(L) + '\n'
    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps({'per_worker': {k: dict(v) for k, v in per_worker.items()},
                                'issues': issues}, ensure_ascii=False, indent=1))
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('issues=%d' % len(issues))
        for w in sorted(per_worker):
            d = per_worker[w]
            bad = d['NO_OPERATOR_LABEL'] + d['ANTI_OPERATOR_IN_ACTION'] + d['DEPRECATED_LABEL_IN_ACTION']
            print('  %-4s T=%-4d no_label=%-4d anti=%-3d deprecated=%-3d (%d%%)' % (
                w, d['transitions'], d['NO_OPERATOR_LABEL'],
                d['ANTI_OPERATOR_IN_ACTION'], d['DEPRECATED_LABEL_IN_ACTION'],
                round(100.0 * bad / max(1, d['transitions']))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
