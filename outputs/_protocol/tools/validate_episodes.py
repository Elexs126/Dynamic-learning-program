#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_episodes.py — 校验 outputs/raw_episodes/*.jsonl 是否符合 EPISODE_SPEC.md。

用法:
  python validate_episodes.py [--dir <raw_episodes 目录>] [--out <报告md>] [--json <报告json>]

检查项:
  * 每行是合法 JSON 对象
  * SPEC §6 顶层字段齐全、类型正确
  * C1–C4 额外具备 §6.2 的八个 408 字段
  * problem_id 唯一且形如 <WORKER>-NNN
  * question_id 存在（可为 null）
  * 不允许自评 E3+（notes 中出现 E3/E4/E5 视为违规）
  * operator_id / failure_type / anti-operator 是否在允许词表内
  * key_transitions 非空且含 before/after/operation
  * naive_routes 至少 1 条
  * trigger_signals 非空
退出码: 0 = 全部通过（可有 warning），1 = 存在 error。
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

# ---------------------------------------------------------------- 词表

OPERATORS = {
    'STATE_REREPRESENTATION', 'FREEDOM_REORGANIZATION', 'QUOTIENT_KERNEL',
    'RESTRICT_SLICE', 'NORMALIZE', 'SPACE_AUGMENTATION', 'AUXILIARY_OBJECT',
    'DEPENDENCY_REORGANIZATION', 'LOW_BANDWIDTH_INTERFACE',
    'INVARIANT_BLOCK_DECOMPOSITION', 'INFORMATION_AXIS_DECOMPOSITION',
    'SHARED_WORLD_EMBEDDING', 'EXACT_ELIMINATION', 'INTERFACE_RENORMALIZATION',
    'PROBE', 'CRITICAL_SCALE_PROBE', 'COUNTEREXAMPLE_PROBE', 'RIGIDIFY',
    'CERTIFICATE_PRODUCTION', 'BRIDGE_OBSERVABLE', 'CONSTRAINT_COLLISION',
    'DEFECT_CENTERING', 'DEFECT_FACTORIZATION', 'UNIFORMIZATION',
    'THICKNESS_EXTRACTION', 'SELF_IMPROVING_CLOSURE', 'ENVIRONMENT_REWEIGHTING',
    'GLUE_LOCAL_TO_GLOBAL', 'INFORMATION_PRESERVATION', 'DEPENDENCY_ORDERING',
    'REPAIR_SCALE_MATCHING', 'FRONTIER_NAVIGATION', 'STRUCTURAL_PROGRESS',
}

ANTI_OPERATORS = {
    'PREMATURE_INFORMATION_LOSS', 'PREMATURE_ABSOLUTE_VALUE',
    'PREMATURE_APPROXIMATION', 'BAD_REPRESENTATION_LOCK_IN',
    'OVER_DECOUPLING', 'MISSING_SHARED_WITNESS', 'LOCAL_REPAIR_GLOBAL_ERROR',
    'DEPTH_TUNNEL_VISION', 'BRANCH_EXPLOSION', 'TARGET_DRIFT',
    'PROXY_OBJECTIVE_DRIFT', 'SEARCH_EXHAUSTED_AS_REFUTED',
    'PROMISING_AS_PROVED', 'DEPENDENCY_CYCLE',
    'RECOMPUTE_WHOLE_FOR_LOCAL_CHANGE',
}

CONFIDENCE = {'high', 'medium', 'low', 'unknown'}

TOP_REQUIRED = [
    'problem_id', 'question_id', 'source', 'domain', 'raw_problem',
    'problem_goal', 'initial_state', 'initial_geometry', 'main_obstacle',
    'naive_routes', 'trigger_signals', 'key_transitions', 'solution_skeleton',
    'certificate_or_closure', 'anti_triggers', 'transfer_candidates',
    'existing_operator_matches', 'possible_new_operator', 'confidence',
    'evidence_excerpt', 'notes',
]

TOP_LIST = [
    'naive_routes', 'trigger_signals', 'key_transitions', 'solution_skeleton',
    'anti_triggers', 'transfer_candidates', 'existing_operator_matches',
]

TOP_STR = [
    'problem_id', 'domain', 'raw_problem', 'problem_goal', 'main_obstacle',
    'certificate_or_closure', 'confidence', 'evidence_excerpt', 'notes',
]

SOURCE_REQUIRED = ['repo_path', 'section', 'example_or_question', 'year']

INITIAL_STATE_REQUIRED = [
    'objects', 'constraints', 'free_variables', 'known_relations', 'target_form',
]

GEOMETRY_AXES = [
    'representation_issue', 'redundant_freedom', 'coupling',
    'scale_competition', 'dependency_structure', 'information_risk',
    'state_transition_structure', 'resource_or_bottleneck_structure',
]

F408_REQUIRED = [
    'system_state', 'resources', 'agents_or_components', 'invariants',
    'state_transition', 'bottleneck', 'local_vs_global_effect', 'layer_interface',
]

TRANSITION_REQUIRED = [
    'before_state', 'operation', 'after_state', 'why_triggered',
    'preserved_information', 'discarded_information', 'new_structure_exposed',
]

NAIVE_REQUIRED = ['route', 'why_natural', 'why_bad_or_expensive', 'failure_type']

E3PLUS_RE = re.compile(r'\bE[345]\b')


def is_nonempty_str(v):
    return isinstance(v, str) and v.strip() != ''


def check_record(rec, worker, lineno, errors, warnings):
    tag = '%s:%d' % (worker, lineno)

    def err(m):
        errors.append('%s  ERROR  %s' % (tag, m))

    def warn(m):
        warnings.append('%s  WARN   %s' % (tag, m))

    # ---- 顶层字段
    for f in TOP_REQUIRED:
        if f not in rec:
            err('缺少字段 %s' % f)
    for f in TOP_LIST:
        if f in rec and not isinstance(rec[f], list):
            err('%s 必须是数组' % f)
    for f in TOP_STR:
        if f in rec and not isinstance(rec[f], str):
            err('%s 必须是字符串' % f)

    # ---- problem_id
    pid = rec.get('problem_id', '')
    if not re.match(r'^%s-\d{3}$' % re.escape(worker), str(pid)):
        warn('problem_id=%r 不符合 %s-NNN 约定' % (pid, worker))

    # ---- confidence
    if rec.get('confidence') not in CONFIDENCE:
        err('confidence=%r 不在 %s' % (rec.get('confidence'), sorted(CONFIDENCE)))

    # ---- source
    src = rec.get('source')
    if not isinstance(src, dict):
        err('source 必须是对象')
    else:
        for f in SOURCE_REQUIRED:
            if f not in src:
                err('source 缺少 %s' % f)
        rp = src.get('repo_path', '')
        if is_nonempty_str(rp):
            if '\\' in rp:
                err('source.repo_path 应使用正斜杠: %r' % rp)
            if re.match(r'^[A-Za-z]:', rp):
                err('source.repo_path 不应是绝对路径: %r' % rp)

    # ---- initial_state
    st = rec.get('initial_state')
    if not isinstance(st, dict):
        err('initial_state 必须是对象')
    else:
        for f in INITIAL_STATE_REQUIRED:
            if f not in st:
                err('initial_state 缺少 %s' % f)

    # ---- initial_geometry
    geo = rec.get('initial_geometry')
    if not isinstance(geo, dict):
        err('initial_geometry 必须是对象')
    else:
        for f in GEOMETRY_AXES:
            if f not in geo:
                err('initial_geometry 缺少 %s' % f)
        if not any(is_nonempty_str(geo.get(f, '')) for f in GEOMETRY_AXES):
            warn('initial_geometry 八个轴全空——确认这题真的没有结构可描述')

    # ---- 空值审计：字段"存在"不等于"有内容"
    # 本检查是补上的——首轮 179 条里只有 3 处空值问题，但此前完全没有闸门覆盖它。
    for f in ('raw_problem', 'problem_goal', 'main_obstacle',
              'certificate_or_closure', 'evidence_excerpt'):
        v = rec.get(f)
        if v in ('', None):
            err('%s 为空——字段存在但无内容' % f)
    st_chk = rec.get('initial_state')
    if isinstance(st_chk, dict):
        for k in ('objects', 'constraints', 'known_relations'):
            if st_chk.get(k) in ('', None, []):
                warn('initial_state.%s 为空列表——确认这题真的没有对应内容' % k)
    if worker.startswith('C') and worker[1:].isdigit():
        for f in F408_REQUIRED:
            if rec.get(f) in ('', None, [], {}):
                warn('408 专属字段 %s 存在但为空——SPEC §6.2 要求填实质内容' % f)

    # ---- main_obstacle 质量
    mo = rec.get('main_obstacle', '')
    if not is_nonempty_str(mo):
        err('main_obstacle 为空')
    else:
        bad = ['不会', '不熟悉', '没掌握', '计算错误', '粗心']
        for b in bad:
            if b in mo:
                warn('main_obstacle 疑似能力描述而非问题结构（含 %r）: %s' % (b, mo[:60]))

    # ---- trigger_signals
    ts = rec.get('trigger_signals')
    if isinstance(ts, list):
        if len(ts) == 0:
            err('trigger_signals 为空——每条 Episode 至少要有一个可观察信号')
        for i, s in enumerate(ts):
            if not is_nonempty_str(s):
                err('trigger_signals[%d] 为空' % i)

    # ---- key_transitions
    kts = rec.get('key_transitions')
    if isinstance(kts, list):
        if len(kts) == 0:
            err('key_transitions 为空——这是数据集最重要的字段')
        for i, kt in enumerate(kts):
            if not isinstance(kt, dict):
                err('key_transitions[%d] 必须是对象' % i)
                continue
            for f in TRANSITION_REQUIRED:
                if f not in kt:
                    err('key_transitions[%d] 缺少 %s' % (i, f))
            if is_nonempty_str(kt.get('before_state', '')) and \
               kt.get('before_state') == kt.get('after_state'):
                warn('key_transitions[%d] before_state 与 after_state 相同——未发生结构变化' % i)

    # ---- naive_routes
    nr = rec.get('naive_routes')
    if isinstance(nr, list):
        if len(nr) == 0:
            warn('naive_routes 为空——SPEC 要求至少 1 条（材料能判断时）')
        for i, r in enumerate(nr):
            if not isinstance(r, dict):
                err('naive_routes[%d] 必须是对象' % i)
                continue
            for f in NAIVE_REQUIRED:
                if f not in r:
                    err('naive_routes[%d] 缺少 %s' % (i, f))
            ft = r.get('failure_type', '')
            if is_nonempty_str(ft) and ft not in ANTI_OPERATORS and not ft.startswith('CANDIDATE_'):
                warn('naive_routes[%d].failure_type=%r 不在 anti-operator 词表内' % (i, ft))

    # ---- existing_operator_matches
    eom = rec.get('existing_operator_matches')
    if isinstance(eom, list):
        for i, m in enumerate(eom):
            if not isinstance(m, dict):
                err('existing_operator_matches[%d] 必须是对象' % i)
                continue
            oid = m.get('operator_id', '')
            if is_nonempty_str(oid) and oid not in OPERATORS and not oid.startswith('CANDIDATE_'):
                warn('existing_operator_matches[%d].operator_id=%r 不在母算子词表内' % (i, oid))
    else:
        if eom is not None and not isinstance(eom, list):
            err('existing_operator_matches 必须是数组')

    # ---- possible_new_operator
    pno = rec.get('possible_new_operator')
    if pno is not None:
        if not isinstance(pno, dict):
            err('possible_new_operator 必须是 null 或对象')
        else:
            for f in ('name', 'why_existing_fails', 'definition'):
                if not is_nonempty_str(pno.get(f, '')):
                    err('possible_new_operator 缺少 %s（SPEC §6.1 要求说明为何现有标签不自然）' % f)

    # ---- 408 专属字段
    if worker.startswith('C') and worker[1:].isdigit():
        for f in F408_REQUIRED:
            if f not in rec:
                err('408 记录缺少专属字段 %s' % f)

    # ---- 自评 E3+（只解析 evidence_level 字段本身，不要扫整个 notes 正文，
    #      否则公式里的 E3/E4/E5 会造成误报）
    notes = rec.get('notes', '') or ''
    m_lvl = re.search(r'evidence_level\s*[:：]\s*(E\d)', notes)
    if m_lvl:
        if m_lvl.group(1) in ('E3', 'E4', 'E5'):
            err('notes 中 evidence_level=%s —— worker 只允许标 E0–E2'
                % m_lvl.group(1))
    else:
        warn('notes 未包含 evidence_level')


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    default_dir = os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes'))
    ap.add_argument('--dir', default=default_dir)
    ap.add_argument('--out', default=None)
    ap.add_argument('--json', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(args.dir)
                   if f.endswith('.jsonl') and not f.startswith('_'))
    if not files:
        print('no .jsonl found in %s' % args.dir)
        return 1

    errors, warnings = [], []
    per_worker = {}
    seen_ids = defaultdict(list)
    conf_all = Counter()
    ev_all = Counter()
    unknown_count = 0
    newop_count = 0
    total = 0

    for fn in files:
        worker = os.path.splitext(fn)[0]
        path = os.path.join(args.dir, fn)
        recs = []
        with io.open(path, encoding='utf-8') as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception as e:
                    errors.append('%s:%d  ERROR  JSON 解析失败: %s' % (worker, lineno, e))
                    continue
                if not isinstance(rec, dict):
                    errors.append('%s:%d  ERROR  行内容不是 JSON 对象' % (worker, lineno))
                    continue
                recs.append(rec)
                total += 1
                seen_ids[rec.get('problem_id')].append('%s:%d' % (worker, lineno))
                check_record(rec, worker, lineno, errors, warnings)
                conf_all[rec.get('confidence', '(missing)')] += 1
                m = re.search(r'evidence_level:\s*(E\d)', rec.get('notes', '') or '')
                ev_all[m.group(1) if m else '(missing)'] += 1
                blob = json.dumps(rec, ensure_ascii=False)
                if 'UNKNOWN' in blob or 'UNEXPLAINED' in blob:
                    unknown_count += 1
                if rec.get('possible_new_operator'):
                    newop_count += 1
        per_worker[worker] = len(recs)

    # 重复 problem_id
    for pid, locs in seen_ids.items():
        if pid and len(locs) > 1:
            errors.append('重复 problem_id %r 出现在 %s' % (pid, ', '.join(locs)))

    summary = {
        'total_episodes': total,
        'workers': per_worker,
        'worker_count': len(per_worker),
        'confidence': dict(conf_all),
        'evidence_level': dict(ev_all),
        'episodes_mentioning_unknown': unknown_count,
        'episodes_with_new_operator': newop_count,
        'error_count': len(errors),
        'warning_count': len(warnings),
        'errors': errors,
        'warnings': warnings,
    }

    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(summary, ensure_ascii=False, indent=1))

    lines = ['# Raw Episodes 校验报告', '']
    lines.append('- Episode 总数：**%d**' % total)
    lines.append('- worker 数：%d' % len(per_worker))
    lines.append('- ERROR：%d ｜ WARNING：%d' % (len(errors), len(warnings)))
    lines.append('')
    lines.append('## 各 worker 产量')
    lines.append('')
    lines.append('| worker | episodes |')
    lines.append('|---|---:|')
    for k in sorted(per_worker):
        lines.append('| %s | %d |' % (k, per_worker[k]))
    lines.append('')
    lines.append('## confidence 分布')
    lines.append('')
    for k, v in conf_all.most_common():
        lines.append('- %s: %d' % (k, v))
    lines.append('')
    lines.append('## evidence_level 分布')
    lines.append('')
    for k in sorted(ev_all):
        lines.append('- %s: %d' % (k, ev_all[k]))
    lines.append('')
    lines.append('- 提及 UNKNOWN/UNEXPLAINED 的 Episode：%d' % unknown_count)
    lines.append('- 带 possible_new_operator 的 Episode：%d' % newop_count)
    lines.append('')
    if errors:
        lines.append('## ERROR（前 80 条）')
        lines.append('')
        for e in errors[:80]:
            lines.append('- %s' % e)
        lines.append('')
    if warnings:
        lines.append('## WARNING（前 80 条）')
        lines.append('')
        for w in warnings[:80]:
            lines.append('- %s' % w)
        lines.append('')

    text = '\n'.join(lines) + '\n'
    if args.out:
        with io.open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print(text)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
