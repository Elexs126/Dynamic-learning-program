#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_remediation.py — 按一份**显式整改清单**修正 Episode 数据，并留下可审计的变更日志。

设计原则（为什么不做成"自动理解 Critic 报告"）：
  Critic 的判定里既有**机械可判**的（词表错位、字段与自身 notes 矛盾），
  也有**需要判断**的（"这条 E2 该不该降 E1"）。若让脚本去"理解"报告，
  它必然会在需要判断的地方乱猜。因此本工具只执行**清单里逐条写明**的改动，
  清单本身是数据文件，可复核、可回滚、可复跑。

用法:
  python apply_remediation.py --fixes fixes.json --dir <raw_episodes> [--apply]
  缺省只预览（dry-run），传 --apply 才写盘。
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
from datetime import datetime


def load_fixes(path):
    with io.open(path, encoding='utf-8') as f:
        return json.load(f)


def find_record(path, problem_id):
    """返回 (行号, 原始行, 解析后的 dict)。"""
    with io.open(path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            s = line.strip()
            if not s:
                continue
            try:
                rec = json.loads(s)
            except Exception:
                continue
            if rec.get('problem_id') == problem_id:
                return i, line, rec
    return None, None, None


def apply_one(rec, fix):
    """在内存里施加一条改动，返回 (是否真的改了, 说明)。"""
    kind = fix['kind']
    if kind == 'set_field':
        cur = rec.get(fix['field'])
        if cur == fix['new']:
            return False, '已是目标值'
        rec[fix['field']] = fix['new']
        return True, '%s: %r -> %r' % (fix['field'], cur, fix['new'])

    if kind == 'drop_operator_match':
        arr = rec.get('existing_operator_matches') or []
        before = len(arr)
        oid = fix['operator_id']
        arr = [m for m in arr if not (isinstance(m, dict) and m.get('operator_id') == oid)]
        rec['existing_operator_matches'] = arr
        if len(arr) == before:
            return False, '未找到该标签'
        return True, '移除母算子数组中的 %s（%d -> %d 条）' % (oid, before, len(arr))

    if kind == 'set_operator_primary':
        arr = rec.get('existing_operator_matches') or []
        changed = 0
        for m in arr:
            if isinstance(m, dict) and m.get('operator_id') == fix['operator_id']:
                if m.get('is_primary_move') != fix['new']:
                    m['is_primary_move'] = fix['new']
                    changed += 1
        return (changed > 0), ('%s.is_primary_move -> %s' % (fix['operator_id'], fix['new'])
                               if changed else '无需改动')

    if kind == 'strip_token_from_operation':
        # 从 key_transitions[].operation 里删掉一个不该出现在"动作"位置的标签
        # （anti-operator 或已废弃标签）。保留其余动作描述文字。
        token = fix['token']
        arr = rec.get('key_transitions') or []
        changed = 0
        for t in arr:
            if not isinstance(t, dict):
                continue
            op = str(t.get('operation') or '')
            if token not in op:
                continue
            # 删掉 token 及其后的连接符（如 " + "、"："/"（…）" 残片）
            new = op.replace(token, '')
            new = re.sub(r'^\s*[+＋、,，:：]\s*', '', new)
            new = re.sub(r'\s*[+＋]\s*$', '', new)
            new = re.sub(r'\s{2,}', ' ', new).strip()
            # 若删除后剩下的不是空串，才写回
            if new and new != op:
                t['operation'] = new
                changed += 1
        return (changed > 0), ('从 operation 中移除 %s（%d 处）' % (token, changed)
                               if changed else '未找到该 token')

    if kind == 'set_notes_evidence_level':
        # evidence_level 存放在 notes 文本里（`evidence_level: E2`），不是顶层字段
        notes = rec.get('notes') or ''
        m = re.search(r'(evidence_level\s*[:：]\s*)(E\d)', notes)
        if not m:
            return False, 'notes 里找不到 evidence_level'
        if m.group(2) == fix['new']:
            return False, '已是 %s' % fix['new']
        old = m.group(2)
        notes = notes[:m.start(2)] + fix['new'] + notes[m.end(2):]
        # 附一句可追溯的说明，避免"文档与数据不一致"
        notes += ('\n[remediation] evidence_level 由 %s 改为 %s：%s'
                  % (old, fix['new'], fix.get('reason', '')))
        rec['notes'] = notes
        return True, 'evidence_level %s -> %s' % (old, fix['new'])

    raise ValueError('未知 kind: %s' % kind)


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--fixes', required=True)
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--apply', action='store_true', help='真正写盘；缺省只预览')
    ap.add_argument('--log', default=None)
    args = ap.parse_args()

    spec = load_fixes(args.fixes)
    fixes = spec.get('fixes') or []

    # 按 worker 分组，便于一次性重写文件
    by_worker = {}
    for f in fixes:
        by_worker.setdefault(f['worker'], []).append(f)

    log = []
    total_changed = 0
    for worker, items in sorted(by_worker.items()):
        path = os.path.join(args.dir, worker + '.jsonl')
        if not os.path.isfile(path):
            log.append({'worker': worker, 'error': '文件不存在'})
            continue
        # 读全部行
        with io.open(path, encoding='utf-8') as fh:
            lines = fh.read().split('\n')

        for f in items:
            pid = f['problem_id']
            hit = None
            for i, line in enumerate(lines):
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception:
                    continue
                if rec.get('problem_id') == pid:
                    hit = (i, rec)
                    break
            if hit is None:
                log.append({'worker': worker, 'problem_id': pid,
                            'error': '未找到该 problem_id'})
                continue
            i, rec = hit
            try:
                changed, note = apply_one(rec, f)
            except Exception as e:
                log.append({'worker': worker, 'problem_id': pid, 'error': str(e)})
                continue
            entry = {
                'worker': worker,
                'problem_id': pid,
                'kind': f['kind'],
                'reason': f.get('reason', ''),
                'source': f.get('source', ''),
                'changed': changed,
                'note': note,
            }
            log.append(entry)
            if changed:
                total_changed += 1
                lines[i] = json.dumps(rec, ensure_ascii=False)

        if args.apply:
            # 备份一次，便于回滚
            bak = path + '.pre_remediation.bak'
            if not os.path.isfile(bak):
                shutil.copy2(path, bak)
            with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write('\n'.join(lines))

    summary = {
        'applied': bool(args.apply),
        'fixes_in_spec': len(fixes),
        'records_changed': total_changed,
        'log': log,
    }

    L = ['# 整改变更日志', '']
    L.append('清单：`%s`' % os.path.basename(args.fixes))
    L.append('')
    L.append('**模式**：%s' % ('已写盘（原文件已备份为 `*.pre_remediation.bak`）'
                              if args.apply else '预览（未写盘）'))
    L.append('')
    L.append('- 清单条目：%d' % len(fixes))
    L.append('- **实际改动的记录数：%d**' % total_changed)
    L.append('')
    L.append('| worker | problem_id | 改动类型 | 结果 | 依据 |')
    L.append('|---|---|---|---|---|')
    for e in log:
        if 'error' in e:
            L.append('| %s | %s | — | ⚠️ %s | — |' % (
                e.get('worker'), e.get('problem_id', '?'), e['error']))
        else:
            L.append('| %s | %s | `%s` | %s | %s |' % (
                e['worker'], e['problem_id'], e['kind'],
                ('✅ ' + e['note']) if e['changed'] else ('— ' + e['note']),
                e.get('source', '')))
    L.append('')
    L.append('## 为什么用清单而不是"自动理解报告"')
    L.append('')
    L.append('Critic 的判定里既有**机械可判**的（词表错位、字段与自身 notes 矛盾），')
    L.append('也有**需要判断**的（"这条 E2 该不该降 E1"）。')
    L.append('若让脚本去"理解"报告，它必然会在需要判断的地方乱猜。')
    L.append('因此本工具只执行**清单里逐条写明**的改动——清单是数据文件，可复核、可回滚。')
    L.append('')
    L.append('**未纳入本清单的整改项**（需要判断或需要 worker 回改）：')
    L.append('')
    for x in (spec.get('deferred') or []):
        L.append('- %s' % x)
    L.append('')

    text = '\n'.join(L) + '\n'
    if args.log:
        with io.open(args.log, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
        with io.open(args.log.replace('.md', '.json'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(json.dumps(summary, ensure_ascii=False, indent=1))
    sys.stdout.reconfigure(encoding='utf-8')
    print('applied=%s fixes=%d changed=%d' % (args.apply, len(fixes), total_changed))
    for e in log:
        if 'error' in e:
            print('  ERROR %-8s %s' % (e.get('problem_id', '?'), e['error']))
        elif e['changed']:
            print('  %-8s %-10s %s' % (e['worker'], e['problem_id'], e['note']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
