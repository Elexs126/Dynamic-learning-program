#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_indexes.py — 从原始信号汇总生成 trigger_index.json 与 anti_trigger_index.json。

## 为什么要"分组"而不是逐条罗列
任务书 §22 的验收标准是：主 Agent 能按
  `某种问题结构 → 代表题 → trigger → transition → anti-trigger`
检索，**而不是重读整章**。
756 条 trigger 信号、477 条 naive_route 逐条罗列等于没索引——
检索者面对 756 个条目仍要自己聚类。所以本工具按**诊断链接**分组：
  * trigger 按 `operator_hint` 分组（信号 → 该警觉什么 → 该做哪类动作）
  * anti-trigger 按 `failure_type` 分组（诱惑 → 为什么自然 → 为什么错 → 怎么修）

## 字段来源（关键：不编造）
  * `diagnosis` 取 **OPERATOR_DEFINITIONS.md 里的算子定义原文**（真实内容，非杜撰）
  * `repair` 取**同一算子在实际 key_transitions 里做过的动作**（真实内容）
  * `signal_variants` / `temptation_variants` 是去重后的原文
凡某字段无真实来源可填，写 `null` 并计入 `needs_synthesis`，
**不写看起来合理但无依据的话**。

用法:
  python build_indexes.py --index <_index> --protocol <_protocol> --raw <raw_episodes> --outdir <outputs>
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict


def read_jsonl(path):
    if not os.path.isfile(path):
        return []
    out = []
    with io.open(path, encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                out.append(json.loads(s))
            except Exception:
                pass
    return out


def parse_operator_defs(path):
    """从 OPERATOR_DEFINITIONS.md 的 §2 表格抓 `算子 -> 定义`。"""
    defs = {}
    if not os.path.isfile(path):
        return defs
    text = io.open(path, encoding='utf-8').read()
    # 表格行：| `OP` | 定义 | n |
    for m in re.finditer(r'^\|\s*`([A-Z][A-Z0-9_]+)`\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|',
                         text, re.M):
        op, definition = m.group(1), m.group(2)
        # 去掉 markdown 粗体/斜体标记，保留文字
        definition = re.sub(r'\*\*|⚠️|`', '', definition).strip()
        defs[op] = definition
    return defs


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, '..', '..'))
    ap.add_argument('--index', default=os.path.join(root, '_index'))
    ap.add_argument('--protocol', default=os.path.join(root, '_protocol'))
    ap.add_argument('--raw', default=os.path.join(root, 'raw_episodes'))
    ap.add_argument('--outdir', default=root)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    defs = parse_operator_defs(os.path.join(args.protocol, 'OPERATOR_DEFINITIONS.md'))

    # ---- 收集"同一算子实际做过的动作"（用于 repair / action 字段）----
    actions = defaultdict(list)     # operator -> [(problem_id, transition_text)]
    for fn in sorted(f for f in os.listdir(args.raw)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        for rec in read_jsonl(os.path.join(args.raw, fn)):
            pid = rec.get('problem_id')
            for m in (rec.get('existing_operator_matches') or []):
                if isinstance(m, dict) and m.get('operator_id') and m.get('is_primary_move'):
                    for t in (rec.get('key_transitions') or []):
                        if isinstance(t, dict):
                            txt = t.get('operation') or t.get('after') or ''
                            if txt:
                                actions[m['operator_id']].append((pid, str(txt)[:200]))

    # ================= trigger_index =================
    trig = read_jsonl(os.path.join(args.index, 'trigger_signals_raw.jsonl'))
    by_op = defaultdict(list)
    no_op = []
    for r in trig:
        op = (r.get('operator_hint') or '').strip()
        if op:
            by_op[op].append(r)
        else:
            no_op.append(r)

    trigger_entries = []
    for i, (op, rows) in enumerate(
            sorted(by_op.items(), key=lambda kv: -len(kv[1])), start=1):
        sigs, seen = [], set()
        for r in rows:
            s = (r.get('signal') or '').strip()
            key = re.sub(r'\s+', '', s)
            if s and key not in seen:
                seen.add(key)
                sigs.append({'text': s, 'problem_id': r.get('problem_id')})
        doms = sorted({r.get('domain') for r in rows if r.get('domain')})
        acts = actions.get(op) or []
        trigger_entries.append({
            'trigger_id': 'T-%03d' % i,
            'operator': op,
            'diagnosis': defs.get(op),
            'diagnosis_source': ('OPERATOR_DEFINITIONS.md §2' if defs.get(op) else None),
            'signal_variants': sigs,
            'n_signals': len(rows),
            'n_distinct_signals': len(sigs),
            'action': op,
            'action_examples': [{'problem_id': p, 'transition': t} for p, t in acts[:3]],
            'examples': sorted({r.get('problem_id') for r in rows if r.get('problem_id')}),
            'domains': doms,
            'is_cross_domain': len(doms) >= 2,
            'confidence': 'high' if len(rows) >= 5 else ('medium' if len(rows) >= 2 else 'low'),
            'needs_synthesis': (defs.get(op) is None),
        })

    # ================= anti_trigger_index =================
    anti = read_jsonl(os.path.join(args.index, 'anti_trigger_raw.jsonl'))
    routes = [r for r in anti if r.get('kind') == 'naive_route']
    warns = [r for r in anti if r.get('kind') == 'anti_trigger']
    warn_by_pid = defaultdict(list)
    for w in warns:
        warn_by_pid[w.get('problem_id')].append((w.get('text') or '').strip())

    by_ft = defaultdict(list)
    for r in routes:
        by_ft[(r.get('failure_type') or 'UNLABELED')].append(r)

    anti_entries = []
    for i, (ft, rows) in enumerate(
            sorted(by_ft.items(), key=lambda kv: -len(kv[1])), start=1):
        tempt, seen = [], set()
        for r in rows:
            t = (r.get('text') or '').strip()
            k = re.sub(r'\s+', '', t)
            if t and k not in seen:
                seen.add(k)
                tempt.append({'route': t, 'problem_id': r.get('problem_id')})
        whys = []
        seenw = set()
        for r in rows:
            w = (r.get('why_bad') or '').strip()
            k = re.sub(r'\s+', '', w)
            if w and k not in seenw:
                seenw.add(k)
                whys.append({'why_bad': w, 'problem_id': r.get('problem_id')})
        nats = []
        seen_n = set()
        for r in rows:
            n = (r.get('why_natural') or '').strip()
            k = re.sub(r'\s+', '', n)
            if n and k not in seen_n:
                seen_n.add(k)
                nats.append({'why_natural': n, 'problem_id': r.get('problem_id')})
        pids = sorted({r.get('problem_id') for r in rows if r.get('problem_id')})
        danger = []
        for p in pids:
            for w in warn_by_pid.get(p, [])[:1]:
                danger.append({'danger_signal': w, 'problem_id': p})
        doms = sorted({r.get('domain') for r in rows if r.get('domain')})
        anti_entries.append({
            'anti_trigger_id': 'A-%03d' % i,
            'failure_type': ft,
            'temptation_variants': tempt,
            'n_temptations': len(rows),
            'n_distinct_temptations': len(tempt),
            'why_natural': nats,
            'failure_pattern': whys,
            'danger_signals': danger,
            'lost_information': None,
            'lost_information_note': '需人工综合；原文未直接陈述"丢失了什么信息"',
            'repair': None,
            'repair_note': '需人工综合；可从同族 Episode 的 key_transitions 反推',
            'examples': pids,
            'domains': doms,
            'is_cross_domain': len(doms) >= 2,
            'confidence': 'high' if len(rows) >= 10 else ('medium' if len(rows) >= 3 else 'low'),
            'needs_synthesis': True,
        })

    trig_out = {
        'schema_version': '1.0',
        'generated_by': 'build_indexes.py',
        'note': ('按 operator_hint 分组。`diagnosis` 取自 OPERATOR_DEFINITIONS.md 的算子定义原文，'
                 '`action_examples` 取自同算子在实际 key_transitions 里做过的动作——'
                 '**两者都是真实内容，不是生成的说明文字**。'
                 '⚠️ 实测：`n_distinct_signals` 与 `n_signals` 几乎处处相等（如 198/198），'
                 '**说明 trigger 信号之间没有字面重复**——每条都是为具体题目写的独立句子。'
                 '因此本索引的价值在**顶层分组**（756 条 → 23 桶，可按算子检索），'
                 '**不在桶内去重**。桶内的 198 条变体仍需语义聚类才能压缩，'
                 '这属于 Family/Unexplained 阶段的语义工作，机械工具做不到。'),
        'n_entries': len(trigger_entries),
        'n_raw_signals': len(trig),
        'n_signals_without_operator': len(no_op),
        'dedup_effect': ('无去重效果：%d 条信号产出 %d 条变体'
                         % (len(trig), sum(e['n_distinct_signals'] for e in trigger_entries))),
        'entries': trigger_entries,
    }
    anti_out = {
        'schema_version': '1.0',
        'generated_by': 'build_indexes.py',
        'note': ('按 failure_type 分组。`temptation_variants`/`why_natural`/`failure_pattern` '
                 '均为去重原文。**`lost_information` 与 `repair` 留空并标注需人工综合**——'
                 '原文没有直接陈述这两项，写看起来合理的话属于编造。'),
        'n_entries': len(anti_entries),
        'n_raw_routes': len(routes),
        'n_raw_anti_triggers': len(warns),
        'entries': anti_entries,
    }

    for name, obj in (('trigger_index.json', trig_out), ('anti_trigger_index.json', anti_out)):
        with io.open(os.path.join(args.outdir, name), 'w',
                     encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=1))

    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('trigger_index: %d entries from %d signals (%d without operator)'
              % (len(trigger_entries), len(trig), len(no_op)))
        print('  needs_synthesis: %d' % sum(1 for e in trigger_entries if e['needs_synthesis']))
        print('anti_trigger_index: %d entries from %d routes'
              % (len(anti_entries), len(routes)))
        print('  cross-domain entries: %d'
              % sum(1 for e in anti_entries if e['is_cross_domain']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
