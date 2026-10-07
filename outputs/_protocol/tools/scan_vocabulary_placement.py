#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_vocabulary_placement.py — 找出被放进错误词表数组的标签。

Critic 发现（math_high1.md A3）：
  * `M2-021` 的 `existing_operator_matches[1].operator_id = "UNKNOWN"`
  * `M1-014` 的 `existing_operator_matches[2].operator_id = "MISSING_SHARED_WITNESS"`
两者都不是 SPEC §7 的母算子——`UNKNOWN` 是占位符，`MISSING_SHARED_WITNESS`
是 §8 的 **anti-operator**。把它们留在母算子数组里会让下游误以为它们是结构动作。

用法: python scan_vocabulary_placement.py --spec <EPISODE_SPEC.md> --dir <raw_episodes>
"""
import argparse
import io
import json
import os
import re
import sys


def parse_vocab(spec_text, section_header):
    """抓取某个 ## 小节里列出的词表标签。

    ⚠️ SPEC §7/§8 把标签放在**代码围栏里、纯文本、空格分列**，不是每词加反引号。
    第一版按反引号抓，只抓到 1 个标签，导致 583 条假阳性。
    现在改为：先定位小节 → 取其中的代码围栏内容 → 抓所有大写标识符。
    """
    m = re.search(re.escape(section_header) + r'(.*?)(?=\n##\s|\Z)', spec_text, re.S)
    if not m:
        return set()
    body = m.group(1)
    fences = re.findall(r'```(.*?)```', body, re.S)
    text = '\n'.join(fences) if fences else body
    # 同时兼容反引号写法（防止将来格式变化）
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

    bad = []
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
                for i, m in enumerate(rec.get('existing_operator_matches') or []):
                    if not isinstance(m, dict):
                        continue
                    oid = m.get('operator_id')
                    if not oid or oid in mother:
                        continue
                    if oid in anti:
                        kind = 'ANTI_OPERATOR_IN_MOTHER_ARRAY'
                        fix = '移入 naive_routes[].failure_type（它是 anti-operator）'
                    elif oid == 'UNKNOWN':
                        kind = 'PLACEHOLDER_IN_MOTHER_ARRAY'
                        fix = '移出数组，改由 notes / possible_new_operator 表达'
                    elif str(oid).startswith('CANDIDATE'):
                        kind = 'CANDIDATE_OK'
                        fix = 'SPEC §8 允许 CANDIDATE_NEW_OPERATOR，保留'
                    else:
                        kind = 'NOT_IN_EITHER_VOCAB'
                        fix = '词表外标签；SPEC §8 允许但应登记，请人工确认'
                    bad.append({
                        'problem_id': rec.get('problem_id'),
                        'worker': worker,
                        'index': i,
                        'operator_id': oid,
                        'kind': kind,
                        'is_primary_move': m.get('is_primary_move'),
                        'suggested_fix': fix,
                    })

    counts = {}
    for b in bad:
        counts[b['kind']] = counts.get(b['kind'], 0) + 1

    L = ['# 词表错位扫描（标签放进了错误的数组）', '']
    L.append('由 `scan_vocabulary_placement.py` 生成。母算子词表解析自 SPEC §7，'
             'anti-operator 词表解析自 §8。')
    L.append('')
    L.append('- 母算子词表：%d 个标签' % len(mother))
    L.append('- anti-operator 词表：%d 个标签' % len(anti))
    L.append('- **错位条目：%d**' % len(bad))
    L.append('')
    if counts:
        L.append('| 类型 | 条数 | 处置 |')
        L.append('|---|---:|---|')
        seen = {}
        for b in bad:
            seen.setdefault(b['kind'], b['suggested_fix'])
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
            L.append('| `%s` | %d | %s |' % (k, v, seen[k]))
        L.append('')
        L.append('## 明细')
        L.append('')
        L.append('| problem_id | worker | 数组下标 | operator_id | 类型 | is_primary_move |')
        L.append('|---|---|---:|---|---|---|')
        for b in bad:
            L.append('| %s | %s | %d | `%s` | %s | %s |' % (
                b['problem_id'], b['worker'], b['index'], b['operator_id'],
                b['kind'], b['is_primary_move']))
        L.append('')
    else:
        L.append('（无错位）')
        L.append('')
    L.append('## 为什么必须处理')
    L.append('')
    L.append('`existing_operator_matches` 的语义是"**这一步属于哪个结构动作**"。')
    L.append('把 anti-operator（描述失败）或占位符 `UNKNOWN` 放进去，会让下游：')
    L.append('')
    L.append('- 把它们当成正常的结构动作统计进覆盖率；')
    L.append('- 在按 `is_primary_move` 聚合时把"worker 承认解释不了"的条目当成证据。')
    L.append('')
    L.append('**注**：`aggregate.py` 已通过 `NON_OPERATOR_LABELS` 在统计时排除这类标签，')
    L.append('所以**统计数字是干净的**；但原始数据仍应修正，以免下游直接读 JSONL 时被误导。')
    L.append('')

    text = '\n'.join(L) + '\n'
    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps({'mother_vocab_size': len(mother),
                                'anti_vocab_size': len(anti),
                                'counts': counts, 'items': bad},
                               ensure_ascii=False, indent=1))
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('mother=%d anti=%d misplaced=%d %s' % (len(mother), len(anti), len(bad), counts))
        for b in bad:
            print('   %-10s %-12s idx=%d %-32s %s' % (
                b['problem_id'], b['worker'], b['index'], b['operator_id'], b['kind']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
