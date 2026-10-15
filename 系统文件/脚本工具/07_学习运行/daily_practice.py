#!/usr/bin/env python3
"""Close a study day and freeze two next-day HTML practice papers.

Uses the existing active question catalog, annotations, contract and real
append-only attempts. No answer keys, fabricated attempts or E metrics.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
import fcntl
import hashlib
import html
import importlib.util
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import shutil
import statistics
import sys
import tempfile
from zoneinfo import ZoneInfo

import learning_runtime as lr
import learning_actions as la
import method_reuse as mr

VERSION = 'daily-practice-v1.2.0'
CONFIG = '系统文件/系统配置/daily_practice_policy_v1.json'
SELECTOR = '系统文件/系统配置/annotation_sources_current_v1.json'
ROOT = '系统文件/学习运行/每日练习'
TZ = ZoneInfo('Asia/Shanghai')
TRACKS = ('MATH1', 'CS408')
NAMES = {'MATH1': '数学一', 'CS408': '408'}
TYPE_NAMES = {'choice': '选择题', 'fill': '填空题', 'analytical': '解答题 / 综合应用题'}
DENIED = {'FIXED_AUDIT', 'SEALED', 'ADAPTIVE_DIAGNOSTIC'}
COURSES = {c[2]: (c[0], c[1], c[3]) for c in lr.COURSES}
VENDOR_SHA = 'd4295dc33744836935c1399feece5159577b34c5c8ffb9f1c6324cd82e03a882'


def aware(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('时间必须包含时区: ' + value)
    return dt


def end_of_day(day):
    return datetime.combine(day + timedelta(days=1), time.min, TZ)


def digest(value):
    return hashlib.sha256(lr.dump(value).encode()).hexdigest()


def validate_attempts(project, rows, records):
    path = project / '系统文件/脚本工具/05_标注与规范校验/validate_attempt_log.py'
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('practice_attempt_validator', path)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    schema_class = lr.schema_runtime(project).__class__
    schemas = {'attempt-record-v1.0.0': schema_class(project / '系统文件/数据规范/attempt_record.schema.json')}
    mapping = la.load_map(project, records) if any(isinstance(r, dict) and (
        r.get('schema_version') == 'attempt-record-v1.1.0' or r.get('is_mixed')) for r in rows) else {'questions': {}}
    ids, errors, by_question, by_stem, batches = set(), [], defaultdict(list), defaultdict(list), defaultdict(list)
    for i, row in enumerate(rows, 1):
        version = row.get('schema_version') if isinstance(row, dict) else None
        if version == 'attempt-record-v1.1.0' and version not in schemas:
            schemas[version] = schema_class(project / '系统文件/数据规范/attempt_record_v1_1.schema.json')
        e = schemas[version].validate(row) if version in schemas else ['未知作答记录版本']
        if e:
            errors.extend(f'第{i}条: {x}' for x in e)
            continue
        if row['attempt_id'] in ids:
            errors.append('重复attempt_id: ' + row['attempt_id'])
        ids.add(row['attempt_id'])
        q = records.get(row['question_id'])
        if q is None or q['l0']['exam_track'] != row['exam_track']:
            errors.append('题号与学科不匹配: ' + row['question_id'])
        elif row['paper_id'] not in (None, q['l0']['paper_id']):
            errors.append('paper_id与题库不匹配: ' + row['question_id'])
        if q is not None and version == 'attempt-record-v1.1.0':
            observations = row['ability_observations']
            observed_ids = [o['ability_id'] for o in observations]
            if len(observed_ids) != len(set(observed_ids)) or any(a not in la.targets(q, mapping) for a in observed_ids):
                errors.append('能力观察重复或未关联该题: ' + row['question_id'])
            if row['target_ability_id'] not in la.targets(q, mapping):
                errors.append('目标能力未关联该题: ' + row['question_id'])
            for obs in observations:
                if not row['is_timed'] and obs['dimensions']['timed_fluency'] is not None:
                    errors.append('未限时不能观察限时流畅')
                if obs['dimensions']['delayed_retention'] is not None and row['interval_hours'] is None:
                    errors.append('延迟保持观察需要间隔')
        try:
            for k in ('attempted_at', 'verified_at', 'next_review_at'):
                aware(row[k])
            validator.validate_record(dict(row, __line_number=i), errors)
        except (ValueError, TypeError) as exc:
            errors.append(f'第{i}条: {exc}')
        by_question[row['question_id']].append(row)
        if q is not None:
            by_stem[q['l0']['question_hash_sha256']].append(row)
        if row['is_mixed']:
            batches[row['batch_id']].append(row)
    for qid, qs in by_question.items():
        ordered = sorted(qs, key=lambda a: aware(a['attempted_at']))
        if any(a['is_unseen'] for a in ordered[1:]):
            errors.append('重复题不能仍标陌生: ' + qid)
    for qs in by_stem.values():
        ordered = sorted(qs, key=lambda a: aware(a['attempted_at']))
        if len({a['question_id'] for a in qs}) > 1 and any(a['is_unseen'] for a in ordered[1:]):
            errors.append('同题干的其他题号不能再次标陌生: ' + ordered[-1]['question_id'])
    for batch, qs in batches.items():
        # Legacy labels can now be aliases of the very same capability. The
        # actual observed targets, not different spellings, define diversity.
        targets = set()
        for a in qs:
            q = records.get(a['question_id'])
            if q is not None:
                targets.add(a['target_ability_id'] if a['schema_version'] == 'attempt-record-v1.1.0'
                            else la.observations(a, q, mapping)[0]['ability_id'])
        targets.discard(None)
        if len({a['question_id'] for a in qs}) < 2 or len(targets) < 2:
            errors.append('混合题组必须含至少两题及两个目标能力: ' + str(batch))
        if len({a['exam_track'] for a in qs}) > 1:
            errors.append('混合题组必须在同一学科内检查调用: ' + str(batch))
    if errors:
        raise ValueError('作答日志校验失败: ' + '; '.join(errors[:12]))


def load_inputs(project):
    selector = lr.read(project / SELECTOR)
    snapshot = lr.inside(project, selector['runtime_snapshot'])
    report = lr.check_build(project, snapshot, lr.read(project / lr.POLICY))
    # Historical catalogs lock logs at build time. Validate their live contents
    # separately instead of demanding a new 8,022-question snapshot every day.
    allowed = {'source_changed: ' + lr.ATTEMPTS, 'source_changed: ' + lr.OFFLINE_LOG}
    errors = [e for e in report['errors'] if e not in allowed]
    if errors:
        raise ValueError('活动题库损坏或来源过期: ' + '; '.join(errors[:8]))
    records = {}
    for ap in selector['annotation_files']:
        bundle = lr.read(lr.inside(project, ap))
        records.update(lr.unique(bundle['records'], 'question_id'))
    catalog = lr.read(snapshot / 'question_catalog.json')['records']
    if set(records) != {r['question_id'] for r in catalog}:
        raise ValueError('活动标注与题库入口不一致')
    rows = lr.jsonl((project / lr.ATTEMPTS).read_text(encoding='utf-8'))
    validate_attempts(project, rows, records)
    summaries = lr.jsonl((project / lr.OFFLINE_LOG).read_text(encoding='utf-8'))
    summary_errors = lr.validate_summaries(summaries, lr.schema_runtime(project))
    if summary_errors:
        raise ValueError('整科反馈校验失败: ' + str(summary_errors))
    return records, rows, summaries, lr.read(snapshot / 'course_navigation.json'), selector


def knowledge(q):
    return la.knowledge(q)


def scope(q):
    return q['l1']['official_scope_coarse']


def derive_state(records, rows, summaries, as_of, threshold, mapping=None):
    mapping = mapping or {'abilities': {}, 'questions': {}, 'mechanisms': {}}
    cutoff = end_of_day(as_of)
    usable = [a for a in rows if aware(a['attempted_at']) < cutoff and aware(a['verified_at']) < cutoff]
    usable.sort(key=lambda a: (aware(a['attempted_at']), a['attempt_id']))
    groups, latest = defaultdict(list), {}
    for a in usable:
        latest[a['question_id']] = a
        if a['usage_role'] not in {'TRAIN', 'AUX_OFFPOLICY'}:
            continue
        for observation in la.observations(a, records[a['question_id']], mapping):
            groups[observation['ability_id']].append((a, observation))
    abilities = {}
    for kid, attempts in groups.items():
        dims = {k: None for k in lr.DIMENSIONS}
        successes = set()
        successes_qids = set()
        for a, observation in attempts:
            for k, v in observation['dimensions'].items():
                if v is not None:
                    dims[k] = v
            failed = observation['first_score_pct'] < threshold or any(v in {'fail', 'partial'} for v in observation['dimensions'].values())
            if failed:
                successes.clear()
                successes_qids.clear()
            if (not failed and a['is_unseen'] and a['highest_hint_level_used'] == 'L0'
                    and observation['first_score_pct'] >= threshold
                    and a['attempt_kind'] in {'near_variant', 'cold_test'}
                    and a['usage_role'] in {'TRAIN', 'AUX_OFFPOLICY'}):
                successes.add(records[a['question_id']]['l0']['question_hash_sha256'])
                successes_qids.add(a['question_id'])
        last, last_observation = attempts[-1]
        q = records[last['question_id']]
        recent_fail = last_observation['first_score_pct'] < threshold or any(v in {'fail', 'partial'} for v in dims.values())
        abilities[kid] = {
            'knowledge_id': kid, 'name': mapping['abilities'].get(kid, {}).get('name', (q.get('l2') or {}).get('main_knowledge', {}).get('name', scope(q))),
            'exam_track': last['exam_track'], 'scope': scope(q),
            'stage': '工作掌握' if len(successes) >= 2 and not kid.startswith('scope:') else '已接触',
            'independent_certification': 'unverified',
            'weak': recent_fail, 'dimensions': dims, 'attempt_count': len(attempts),
            'last_score_pct': last_observation['first_score_pct'], 'last_attempted_at': last['attempted_at'],
            'primary_error_code': last_observation['error_code'],
            'successful_question_ids': sorted(successes_qids),
            'ordinary_cold_test_passed': any(a['attempt_kind'] == 'cold_test' and a['question_id'] in successes_qids for a, _ in attempts),
            'next_review_at': last['next_review_at'],
            'due': aware(last['next_review_at']) < end_of_day(as_of + timedelta(days=1))
        }
    return {'version': VERSION, 'as_of': str(as_of), 'attempt_count': len(usable),
            'unobserved_ability_status': None, 'abilities': abilities,
            'latest_questions': latest, 'capability_map': mapping,
            'review_tasks': la.review_queue(records, usable, mapping, end_of_day(as_of + timedelta(days=1)), threshold),
            'whole_exam_summaries': [s for s in summaries if aware(s['verified_at']) < cutoff],
            'E_metrics': None,
            'notes': ['整科总分不推导单项掌握；训练反馈不自动激活独立认证；未观察五维保持null。']}, usable


def validate_teacher_plan(plan, records, mapping=None, methods=None):
    mapping = mapping or {'abilities': {}, 'questions': {}}
    methods = methods or {'methods': {}}
    if not isinstance(plan, dict) or set(plan) - {'version', 'effective_week_start', 'weekly_allocation', 'subjects'}:
        raise ValueError('Teacher计划只接受版本、预算周、周分配及subjects')
    if plan.get('version') != 'daily-teacher-plan-v1':
        raise ValueError('Teacher计划version应为daily-teacher-plan-v1')
    if set(plan.get('subjects', {})) - set(TRACKS):
        raise ValueError('未知学科')
    known = {knowledge(q): q['l0']['exam_track'] for q in records.values()}
    known.update({aid: a['exam_track'] for aid, a in mapping['abilities'].items()})
    scopes = {scope(q): q['l0']['exam_track'] for q in records.values()}
    fields = {'priority_knowledge_ids', 'required_knowledge_ids', 'working_knowledge_ids',
              'frontier_scopes', 'exclude_question_ids', 'practice_minutes', 'mode',
              'priority_ability_ids', 'required_ability_ids', 'working_ability_ids', 'preferred_method_ids'}
    for track, subject in plan.get('subjects', {}).items():
        if not isinstance(subject, dict) or set(subject) - fields:
            raise ValueError('未知Teacher学科计划字段')
        for key, values in subject.items():
            if key == 'mode':
                if values not in la.MODES:
                    raise ValueError('mode必须为repair、maintenance或exam')
                continue
            if key == 'practice_minutes':
                if not lr.finite(values, 1):
                    raise ValueError('practice_minutes必须为正数')
                continue
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                raise ValueError(key + '必须为字符串数组')
            if key == 'preferred_method_ids':
                if len(set(values)) != len(values) or any(mid not in methods['methods'] or
                        methods['methods'][mid]['exam_track'] != track for mid in values):
                    raise ValueError('优先方法重复、未知或跨科')
                continue
            universe = scopes if key == 'frontier_scopes' else records if key == 'exclude_question_ids' else known
            if any(v not in universe for v in values):
                raise ValueError(key + '含未知题号/知识点/章节')
            if key != 'exclude_question_ids' and any(universe[v] != track for v in values):
                raise ValueError('Teacher计划知识点/章节学科不匹配')


def time_budgets(contract, policy, teacher, target):
    budget = contract['time_budget']
    allocation = {k: budget['initial_weekly_allocation'][k] for k in TRACKS}
    if 'weekly_allocation' in teacher:
        allocation = teacher['weekly_allocation']
        monday = target - timedelta(days=target.weekday())
        if teacher.get('effective_week_start') != str(monday):
            raise ValueError('周时间配置必须属于目标日期所在的冻结预算周')
    if set(allocation) != set(TRACKS) or not all(lr.finite(v, 0) for v in allocation.values()):
        raise ValueError('两科时间配置无效')
    if sum(allocation.values()) != budget['net_weekly_hours']:
        raise ValueError('周分配之和必须等于合同净时间')
    if any(allocation[k] < budget['minimum_weekly_hours'][k] for k in TRACKS):
        raise ValueError('周分配未满足两科最低保障')
    weekday = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')[target.weekday()]
    total = budget['reported_daily_hours_for_math1_and_cs408'][weekday] * 60
    result = {}
    for track in TRACKS:
        net = total * allocation[track] / sum(allocation.values())
        practice = teacher.get('subjects', {}).get(track, {}).get('practice_minutes', net * policy['practice_share'])
        if not lr.finite(practice, 1) or practice > net:
            raise ValueError('作答时间必须在当天该科净预算以内')
        result[track] = {'net_minutes': round(net, 2), 'practice_minutes': round(practice, 2),
                         'reserved_minutes': round(net - practice, 2), 'weekly_hours': allocation[track]}
    return result


def estimate_speed(records, attempts, track, policy):
    result = {}
    for kind, default in policy['default_minutes'][track].items():
        # Comparable first-pass, independent timed episodes; hints/review repeats
        # do not distort the ordinary working speed of unseen paper questions.
        comparable = [a['duration_seconds'] / 60 for a in attempts
                      if a['exam_track'] == track and a['is_timed'] and a['is_unseen']
                      and a['highest_hint_level_used'] == 'L0'
                      and records[a['question_id']]['l0']['question_type'] == kind]
        personal = len(comparable) >= policy['personal_speed_min_samples']
        result[kind] = {'minutes': round(statistics.median(comparable[-30:]), 2) if personal else default,
                        'basis': 'personal_median' if personal else 'cold_start_estimate',
                        'sample_count': len(comparable)}
    return result


def proportional_counts(total, base):
    values = {k: total * n / sum(base.values()) for k, n in base.items()}
    counts = {k: math.floor(v) for k, v in values.items()}
    order = sorted(base, key=lambda k: (-(values[k] - counts[k]), list(base).index(k)))
    for k in order[:total - sum(counts.values())]:
        counts[k] += 1
    return counts


def role_exclusions(project, attempts):
    excluded = {a['question_id'] for a in attempts if a['usage_role'] in DENIED}
    blocked_papers = set()
    # The current shared project has no active role bundle. If one is supplied
    # later, respect the latest public events without discovering hidden pools.
    path = project / '系统文件/系统配置/usage_roles_current_v1.json'
    if path.exists():
        data = lr.read(path)
        schema = lr.schema_runtime(project).__class__(project / '系统文件/数据规范/usage_roles_bundle.schema.json')
        errors = schema.validate(data)
        if errors:
            raise ValueError('角色历史校验失败: ' + str(errors))
        for key, identity, dest in [('question_events', 'question_id', excluded), ('paper_events', 'paper_id', blocked_papers)]:
            events = sorted(data[key], key=lambda e: aware(e['assigned_at']))
            for event in events:
                role = event['role']
                if role in DENIED and event['retired_at'] is None:
                    dest.add(event[identity])
                if not event['teacher_visible'] and event['retired_at'] is None:
                    dest.add(event[identity])
    return excluded, blocked_papers


def scope_order(navigation, records):
    order = {}
    for course in navigation['courses']:
        roots = [s for s in course['scopes'] if s['parent_scope'] is None]
        for q in records.values():
            if q['l0']['subject_area'] != course['subject_area']:
                continue
            chapter = scope(q).split(' > ')[-1]
            canonical = re.sub(r'[、，,与和及（）()\s]', '', chapter)
            matches = [(i, re.sub(r'[、，,与和及（）()\s]', '', s['scope_name'])) for i, s in enumerate(roots)]
            matches = [(i, name) for i, name in matches if canonical in name or name in canonical]
            index = min(matches, key=lambda item: (item[1] != canonical, -len(item[1]), item[0]))[0] if matches else len(roots)
            order[scope(q)] = index
    return order


def prepare_candidates(project, records, state, attempts, navigation, track, teacher, methods=None):
    subject = teacher.get('subjects', {}).get(track, {})
    method_index = mr.checked_index(methods, records) if methods else {}
    preferred_methods = set(subject.get('preferred_method_ids', []))
    excluded, blocked_papers = role_exclusions(project, attempts)
    excluded.update(subject.get('exclude_question_ids', []))
    abilities, latest = state['abilities'], state['latest_questions']
    mapping = state['capability_map']
    aliases = la.aliases(records, mapping)
    def normalize(values):
        return {aliases.get(k, k) for k in values}
    due_tasks = [t for t in state['review_tasks'] if t['due'] and t['exam_track'] == track]
    due_abilities = {t['ability_id'] for t in due_tasks}
    seen = set(latest)
    seen_hashes = {records[q]['l0']['question_hash_sha256'] for q in seen}
    due = {q for t in due_tasks for q in t['question_ids'] if q in latest and q not in excluded
           and records[q]['l0']['paper_id'] not in blocked_papers}
    weak = {k for k, a in abilities.items() if a['exam_track'] == track and a['weak']}
    weak_scopes = {a['scope'] for a in abilities.values() if a['exam_track'] == track and a['weak']}
    working = {k for k, a in abilities.items() if a['stage'] == '工作掌握' and not a['weak']} | normalize(subject.get('working_knowledge_ids', []) + subject.get('working_ability_ids', []))
    priority = normalize(subject.get('priority_knowledge_ids', []) + subject.get('priority_ability_ids', []))
    required = normalize(subject.get('required_knowledge_ids', []) + subject.get('required_ability_ids', []))
    order = scope_order(navigation, records)
    covered = {scope(records[q]) for q in seen}
    frontier = set(subject.get('frontier_scopes', []))
    if not frontier:
        for area, (_, _, exam) in COURSES.items():
            if exam != track:
                continue
            scopes = {scope(q) for q in records.values() if q['l0']['subject_area'] == area}
            observed = scopes & covered
            if observed:
                # A single attempt never completes an entire chapter. Keep the
                # observed course frontier unless Teacher supplies the next one.
                frontier.add(max(observed, key=lambda s: (order.get(s, -1), s)))
            elif scopes:
                frontier.add(min(scopes, key=lambda s: (order.get(s, 999), s)))
    candidates = []
    for qid, q in records.items():
        l0, l2, l3 = q['l0'], q.get('l2') or {}, q.get('l3') or {}
        ids, sc = set(la.targets(q, mapping)), scope(q)
        matches = ids & (due_abilities | required | priority | weak)
        kid = min(matches, key=lambda k: (0 if k in due_abilities else 1 if k in required else 2 if k in priority else 3, k)) if matches else la.primary(q, mapping)
        if l0['exam_track'] != track or qid in excluded or l0['paper_id'] in blocked_papers:
            continue
        if l0['question_type'] not in TYPE_NAMES or (track == 'CS408' and l0['question_type'] == 'fill'):
            continue
        if (qid in seen or l0['question_hash_sha256'] in seen_hashes) and qid not in due:
            continue
        if qid not in due and kid not in due_abilities | required | priority | weak and sc not in covered | frontier:
            continue
        prereqs = l2.get('prerequisites') or {}
        missing = [p for p in prereqs.get('hard_prerequisite', []) if aliases.get(p['id'], p['id']) not in working]
        # Missing observations are not failed prerequisites. At the initial
        # frontier, unknown prerequisites become explicit preparation tasks;
        # observed insufficient prerequisites do block new downstream work.
        blocked = [p for p in missing if aliases.get(p['id'], p['id']) in abilities]
        if blocked and qid not in due and kid not in due_abilities:
            continue
        if kid in working and not blocked:
            missing = []  # reuse demonstrated ability; do not infer separate prerequisite mastery
        dependency = l3.get('inter_question_dependency') or {}
        if dependency.get('unresolved_legacy_note'):
            continue
        if any(r['from_question_id'].split('#')[0] != qid or r['to_question_id'].split('#')[0] != qid
               for r in dependency.get('relations', [])):
            continue  # keep internally dependent subparts intact; no orphan cross-question context
        if qid in due or kid in due_abilities:
            reason, rank = '到期复习', 0
        elif kid in required:
            reason, rank = '必要前置 / 预定核心任务', 1
        elif kid in priority:
            reason, rank = 'Teacher既有优先判断', 2
        elif kid in weak:
            reason, rank = '薄弱知识点的陌生变式', 3
        elif sc in weak_scopes:
            reason, rank = '薄弱章节巩固', 4
        elif kid in working:
            reason, rank = '工作掌握后的混合维护', 6
        else:
            reason, rank = '学习前沿 / 核心覆盖', 5
        difficulty = {'basic': 0, 'intermediate': 1, 'advanced': 2}.get(l2.get('difficulty_band'), 1)
        preferred_source = (l0['source_file'].startswith(('配套习题/张宇基础30讲/', '配套习题/张宇1000题/'))
                            if track == 'MATH1' else l0['source_file'].startswith('核心真题/'))
        seed = hashlib.sha256((str(state['as_of']) + qid).encode()).hexdigest()
        matched_methods = sorted({link['method_id'] for link in method_index.get(qid, [])} & preferred_methods)
        # Current repaired mathematical sources are preferred within an equal
        # learning need. Source preference never overrides due/Teacher priorities.
        candidates.append({'question_id': qid, 'q': q, 'knowledge_id': kid, 'reason': reason,
                           'preparation': missing,
                           'ability_ids': sorted(ids),
                           'preferred_method_ids': matched_methods,
                           'review_tasks': [t for t in due_tasks if t['ability_id'] == kid],
                           'rank': (rank, 1 if qid in seen else 0, 0 if matched_methods else 1, order.get(sc, 999), difficulty,
                                    0 if preferred_source else 1, seed)})
    return sorted(candidates, key=lambda c: c['rank']), due, order


def question_body(project, q):
    source = lr.inside(project, q['l0']['source_file'])
    text = source.read_text(encoding='utf-8')
    pattern = r'^#{3,6}\s+【' + re.escape(q['l0']['source_locator']) + r'】[^\n]*\n'
    matches = list(re.finditer(pattern, text, re.M))
    if len(matches) != 1:
        raise ValueError('原题定位不是唯一题头: ' + q['question_id'])
    start = matches[0].end()
    stop = re.search(r'^#{3,6}\s+【[^】]+】', text[start:], re.M)
    fragment = text[start:start + stop.start()] if stop else text[start:]
    # Never send answers/solutions to the browser, including collapsed details.
    fragment = re.split(r'<details\b|^>\s*\*\*【|^\s*\*\*【(?:参考答案|答案|解析)】|^\s*#{1,6}\s*(?:参考答案|答案|解析)', fragment,
                        maxsplit=1, flags=re.M | re.I)[0]
    fragment = re.sub(r'\n---\s*$', '', fragment).strip()
    if not fragment or re.search(r'参考答案|正确答案|【解析】|<script', fragment, re.I):
        raise ValueError('题干为空或含答案/脚本: ' + q['question_id'])
    if re.search(r'^\s*第\s*[零一二三四五六七八九十0-9]+\s*章\s*$', fragment, re.M):
        raise ValueError('题目切片混入下一章内容，需先核对边界: ' + q['question_id'])
    if q['l0']['question_type'] == 'choice' and not all(re.search(r'\b' + letter + r'\s*[.．、:：]', fragment) for letter in 'ABCD'):
        raise ValueError('选择题选项不完整: ' + q['question_id'])
    if q['l0']['question_type'] == 'choice':
        options = re.findall(r'^\s*[-*]\s*\*\*[ABCD][.．、:：]\*\*\s*([\s\S]*?)(?=^\s*[-*]\s*\*\*[ABCD][.．、:：]\*\*|\Z)', fragment, re.M)
        normalized = [re.sub(r'\s+', '', x) for x in options]
        if len(normalized) == 4 and len(set(normalized)) < 4:
            raise ValueError('存在重复选项，需先核对原稿: ' + q['question_id'])
    math_texts = re.findall(r'\$\$([\s\S]*?)\$\$|(?<!\$)\$(?!\$)((?:\\.|[^$])*?)\$', fragment)
    for parts in math_texts:
        formula = ''.join(parts)
        if re.search(r'[∑∫∂]|(?<!\\)\b(?:lim|sin|cos|tan|ln)\b', formula):
            raise ValueError('疑似公式OCR压平，先核对原稿: ' + q['question_id'])
        if formula.count('{') != formula.count('}'):
            raise ValueError('公式花括号不平衡: ' + q['question_id'])
    return fragment, source


def render_markdown(text, source, project):
    """Escaped Markdown subset: math, images, lists, tables, fenced code.

    Protect TeX before emphasis handling; no raw HTML execution or external URLs.
    """
    tokens = []
    text = re.sub(r'<br\s*/?>', '\n\n', text, flags=re.I)

    def token(value):
        tokens.append(value)
        return f'PRACTICETOKEN{len(tokens)-1}END'

    def image_match(m):
        relative = m.group(2).strip().split(' "')[0]
        asset = (source.parent / relative).resolve()
        if not asset.is_relative_to(project.resolve()) or not asset.is_file():
            raise ValueError('题目配图缺失或越界: ' + relative)
        mime = mimetypes.guess_type(asset.name)[0]
        if mime not in {'image/png', 'image/jpeg', 'image/gif', 'image/svg+xml', 'image/webp'}:
            raise ValueError('不支持的题目配图: ' + relative)
        encoded = base64.b64encode(asset.read_bytes()).decode()
        return token(f'<img alt="{html.escape(m.group(1), quote=True)}" src="data:{mime};base64,{encoded}">')

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', image_match, text)
    text = re.sub(r'```[^\n]*\n([\s\S]*?)```', lambda m: token('<pre><code>' + html.escape(m.group(1)) + '</code></pre>'), text)
    commands = r'begin|end|frac|dfrac|tfrac|sqrt|sin|cos|tan|ln|log|lim|sum|prod|int|iint|iiint|partial|le|ge|neq|ne|in|notin|infty|left|right|alpha|beta|gamma|delta|lambda|mu|sigma|theta|varphi|phi|pi|cdot|times|overline|underline|text|mathrm|mathbf|mathbb|hspace|quad|qquad|to|max|min'
    def math_match(m):
        # Some source Markdown retains JSON-style doubled command escapes.
        # Normalize command prefixes for display, preserving TeX row breaks.
        value = re.sub(r'\\\\(?=(?:' + commands + r')\b)', lambda _: '\\', m.group(0))
        return token(html.escape(value))
    text = re.sub(r'\$\$[\s\S]*?\$\$|(?<!\$)\$(?!\$)(?:\\.|[^$])*?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)', math_match, text)
    text = re.sub(r'`([^`]+)`', lambda m: token('<code>' + html.escape(m.group(1)) + '</code>'), text)
    text = html.escape(text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    parts = []
    for block in re.split(r'\n\s*\n', text):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if all(l.startswith('|') for l in lines):
            table = []
            for line in lines:
                cells = [c.strip() for c in line.strip('|').split('|')]
                if all(re.fullmatch(r':?-+:?', c) for c in cells):
                    continue
                table.append('<tr>' + ''.join('<td>' + c + '</td>' for c in cells) + '</tr>')
            parts.append('<table>' + ''.join(table) + '</table>')
        elif re.match(r'^[-*]\s+', lines[0]):
            items = re.split(r'\n(?=[-*]\s+)', block)
            parts.append('<ul>' + ''.join('<li>' + re.sub(r'^[-*]\s+', '', item).replace('\n', ' ') + '</li>' for item in items) + '</ul>')
        elif all(re.match(r'^[A-D][.．、:：]\s', line) for line in lines):
            parts.append('<ul class="plain-options">' + ''.join('<li>' + line + '</li>' for line in lines) + '</ul>')
        else:
            parts.append('<p>' + block.replace('\n', ' ') + '</p>')
    rendered = ''.join(parts)
    for i, value in enumerate(tokens):
        rendered = rendered.replace(f'PRACTICETOKEN{i}END', value)
    return rendered


def select_paper(project, candidates, due, order, track, budget, speed, policy, mode='exam'):
    blueprint = policy['blueprints'][track]
    unavailable, bodies = {}, {}
    limit = math.floor(sum(blueprint['counts'].values()) * policy['maximum_paper_scale'])

    def eligible(c, hashes, clusters):
        qid, q = c['question_id'], c['q']
        fingerprint = q['l0']['question_hash_sha256']
        relation = (q.get('l3') or {}).get('isomorphic_relation') or {}
        cluster = relation.get('cluster_id') if relation.get('status') == 'verified' else None
        if fingerprint in hashes or (cluster and cluster in clusters and mode != 'repair') or qid in unavailable:
            return False
        try:
            if qid not in bodies:
                body, source = question_body(project, q)
                bodies[qid] = render_markdown(body, source, project)
        except ValueError as error:
            unavailable[qid] = str(error)
            return False
        hashes.add(fingerprint)
        if cluster:
            clusters.add(cluster)
        return True

    best = None
    if mode != 'exam':
        selected, hashes, clusters, focus, task_ids = [], set(), set(), set(), set()
        counts = {k: 0 for k in blueprint['counts']}
        estimate = 0
        for c in candidates:
            kid, kind = c['knowledge_id'], c['q']['l0']['question_type']
            tasks = {t['task_id'] for t in c.get('review_tasks', [])}
            if tasks and tasks <= task_ids:
                continue  # one probe per ability/error task; completion still needs real feedback
            if mode == 'repair' and kid not in focus and len(focus) >= policy.get('focus_ability_limit', 3):
                continue
            cost = speed[kind]['minutes']
            if len(selected) >= limit or estimate + cost > budget['practice_minutes']:
                continue
            if not eligible(c, hashes, clusters):
                continue
            selected.append(c)
            focus.add(kid)
            task_ids.update(tasks)
            counts[kind] += 1
            estimate += cost
        if selected:
            best = selected, counts, estimate
    else:
        for total in range(limit, policy['minimum_questions'][track] - 1, -1):
            counts = proportional_counts(total, blueprint['counts'])
            if not all(counts.values()):
                continue
            estimate = sum(counts[k] * speed[k]['minutes'] for k in counts)
            if estimate > budget['practice_minutes']:
                continue
            selected, hashes, clusters, remaining = [], set(), set(), dict(counts)
            for c in candidates:
                kind = c['q']['l0']['question_type']
                if not remaining.get(kind) or not eligible(c, hashes, clusters):
                    continue
                selected.append(c)
                remaining[kind] -= 1
            if not any(remaining.values()):
                best = selected, counts, estimate
                break
    if best is None:
        return {'exam_track': track, 'mode': mode, 'status': 'insufficient_eligible_questions_or_time', 'questions': [],
                'counts': {k: 0 for k in blueprint['counts']}, 'budget': budget, 'speed': speed,
                'warnings': ['当前用途下可用题干或时间不足；保留教学和到期任务，补充学习前沿或预算后再生成。'],
                'unplaced_due_question_ids': sorted(due), 'unavailable_questions': unavailable}
    selected, counts, estimate = best
    if mode == 'exam':
        selected.sort(key=lambda c: (list(blueprint['counts']).index(c['q']['l0']['question_type']), c['rank']))
    questions, slots, planned_tasks = [], Counter(), set()
    for number, c in enumerate(selected, 1):
        q, qid = c['q'], c['question_id']
        l0, kind = q['l0'], q['l0']['question_type']
        points, training = l0['original_points'], blueprint['points'][kind]
        if points is None:
            points = training[slots[kind] % len(training)] if isinstance(training, list) else training
        slots[kind] += 1
        tasks = c.get('review_tasks', [])
        planned_tasks.update(t['task_id'] for t in tasks)
        questions.append({'number': number, 'question_id': qid, 'paper_id': l0['paper_id'],
                          'question_type': kind, 'points': points,
                          'point_basis': 'original' if l0['original_points'] is not None else 'training_assignment',
                          'estimated_minutes': speed[kind]['minutes'],
                          'source_file': l0['source_file'], 'source_locator': l0['source_locator'],
                          'source_sha256': lr.sha(lr.inside(project, l0['source_file'])),
                          'scope': scope(q), 'knowledge_id': knowledge(q),
                          'target_ability_id': c['knowledge_id'], 'ability_ids': c.get('ability_ids', [c['knowledge_id']]),
                          'preferred_method_ids': c.get('preferred_method_ids', []),
                          'reason': c['reason'], 'preparation': c.get('preparation', []),
                          'review_task_ids': [t['task_id'] for t in tasks],
                          'review_error_codes': sorted({t['error_code'] for t in tasks if t['error_code']}),
                          'was_attempted': qid in due,
                          'usage_role': 'TRAIN' if l0['source_file'].startswith('核心真题/') else 'AUX_OFFPOLICY',
                          'body_html': bodies[qid]})
    due_task_map = {t['task_id']: t for c in candidates for t in c.get('review_tasks', [])}
    represented = {qid for tid in planned_tasks for qid in due_task_map[tid]['question_ids']}
    outstanding = sorted(due - represented - {q['question_id'] for q in questions})
    warnings = (['考试练习按真题题型数量比例取整，保留原分值；这是训练反馈，独立审计仍按原隔离要求执行。'] if mode == 'exam'
                else ['按当前障碍或已学能力选题，允许只有一种题型；完整大题及考试节奏由周期练习检查。'])
    if outstanding:
        warnings.append(f'{len(outstanding)}道题关联的到期任务尚未安排探针，继续保留债务。')
    return {'exam_track': track, 'mode': mode, 'status': 'ready', 'counts': counts, 'reference_counts': blueprint['counts'],
            'estimated_minutes': round(estimate, 2), 'budget': budget, 'speed': speed,
            'maximum_points': sum(q['points'] for q in questions), 'questions': questions,
            'focus_scopes': list(dict.fromkeys(q['scope'] for q in questions)),
            'warnings': warnings, 'unplaced_due_question_ids': outstanding,
            'planned_review_task_ids': sorted(planned_tasks), 'unavailable_questions': unavailable}


def build_day(project, as_of, teacher=None, new_rows=None):
    records, rows, summaries, navigation, selector = load_inputs(project)
    teacher = teacher or {'version': 'daily-teacher-plan-v1', 'subjects': {}}
    mapping = la.load_map(project, records)
    methods = mr.load_library(project, records)
    validate_teacher_plan(teacher, records, mapping, methods)
    if new_rows:
        rows = rows + new_rows
        validate_attempts(project, rows, records)
        if any(aware(a['verified_at']) >= end_of_day(as_of) for a in new_rows):
            raise ValueError('新增反馈的自核日期不能晚于本次日结')
    policy = lr.read(project / CONFIG)
    target = as_of + timedelta(days=1)
    state, usable = derive_state(records, rows, summaries, as_of, policy['score_threshold_pct'], mapping)
    budgets = time_budgets(lr.read(project / '系统文件/系统配置/execution_contract_v1.json'), policy, teacher, target)
    papers = {}
    for track in TRACKS:
        speed = estimate_speed(records, usable, track, policy)
        scheduled = 'exam' if target.weekday() in policy.get('exam_weekdays', []) else 'maintenance' if target.weekday() in policy.get('maintenance_weekdays', []) else policy.get('default_mode', 'repair')
        mode = teacher.get('subjects', {}).get(track, {}).get('mode', scheduled)
        observed = {k for k, a in state['abilities'].items() if a['exam_track'] == track}
        if mode == 'maintenance' and not observed:
            mode = 'repair'  # no invented learner baseline
        candidates, due, order = prepare_candidates(project, records, state, usable, navigation, track,
                                                    teacher, methods if mode == 'repair' else None)
        if mode == 'maintenance':
            candidates = [c for c in candidates if c['knowledge_id'] in observed and not c['preparation']]
        if mode == 'exam':
            candidates = [c for c in candidates if not c['preparation']]
        papers[track] = select_paper(project, candidates, due, order, track, budgets[track], speed, policy, mode)
        paper = papers[track]
        for q in paper['questions']:
            q['was_attempted'] = q['question_id'] in state['latest_questions']
            fine_name = (records[q['question_id']].get('l2') or {}).get('main_knowledge', {}).get('name', q['scope'])
            q['ability_names'] = {aid: mapping['abilities'].get(aid, {}).get('name', fine_name) for aid in q['ability_ids']}
            link = mapping['questions'].get(q['question_id'], {})
            q['score_supports_primary'] = link.get('score_supports_primary', True)
            q['ordinary_cold_test_eligible'] = (mode == 'maintenance' and not q['was_attempted'] and not q['preparation'])
            q['last_learning_at'] = state['abilities'].get(q['target_ability_id'], {}).get('last_attempted_at')
        paper['learning_blocks'] = la.learning_blocks(paper, state, mapping)
        paper['method_blocks'] = mr.learning_blocks(paper, methods, records)
        paper['unplaced_review_tasks'] = [t for t in state['review_tasks'] if t['exam_track'] == track and t['due'] and t['task_id'] not in paper.get('planned_review_task_ids', [])]
    result = {'version': VERSION, 'as_of': str(as_of), 'target_date': str(target),
              'learner_feedback_count': state['attempt_count'], 'state': state, 'papers': papers,
              'teacher_plan': teacher, 'policy': policy,
              'catalog_snapshot': selector['runtime_snapshot'],
              'input_digest': digest({'attempts': rows, 'summaries': summaries, 'teacher': teacher,
                                     'policy': policy, 'capability_map': mapping, 'method_library': methods})}
    return result, rows, new_rows or []


def public_plan(day):
    value = json.loads(lr.dump(day))
    for paper in value['papers'].values():
        for q in paper['questions']:
            q.pop('body_html', None)
    return value


def html_paper(day, track):
    paper = day['papers'][track]
    vendor = Path(__file__).parent / 'vendor/tex-svg.js'
    if lr.sha(vendor) != VENDOR_SHA:
        raise ValueError('公式渲染库哈希不匹配')
    content, kind = [], None
    for q in paper['questions']:
        if q['question_type'] != kind:
            kind = q['question_type']
            content.append('<h2>' + TYPE_NAMES[kind] + '</h2>')
        basis = '原题分值' if q['point_basis'] == 'original' else '训练配分'
        ability_feedback = ('<label><input class="primary-observed" type="checkbox"' + (' checked' if q['score_supports_primary'] else '') + '>本题得分率能可靠反映目标能力：' + html.escape(q['ability_names'][q['target_ability_id']]) + '</label>')
        if not q['score_supports_primary'] or len(q['ability_ids']) > 1:
            ability_feedback += '<details><summary>能分别核对的能力（未观察留空）</summary>' + ''.join(
                '<label>' + html.escape(q['ability_names'][aid]) + '<input class="ability-score" data-ability="' + html.escape(aid, quote=True) + '" type="number" min="0" max="100" placeholder="该能力得分率 %"></label>' for aid in q['ability_ids']) + '</details>'
        ability_feedback += ''.join('<label><input class="checked-error" type="checkbox" value="' + html.escape(code, quote=True) + '">本题确实检查了既往误区：' + html.escape(code) + '</label>' for code in q['review_error_codes'])
        if q['ordinary_cold_test_eligible']:
            ability_feedback += '<label><input class="cold" type="checkbox">本次实际为间隔至少48小时的陌生、无提示、限时、混合冷测</label>'
        content.append(f'<article id="q{q["number"]}"><div class="qheading"><b>第{q["number"]}题 · {q["points"]}分</b><small>{basis} · 预计{q["estimated_minutes"]}分钟</small></div>'
                       + '<div class="stem">' + q['body_html'] + '</div><button class="question-start">开始本题</button> <button class="question-finish">完成第一遍</button><label class="response">答题区<textarea placeholder="在这里记录作答，或在纸上完成"></textarea></label>'
                       + f'<details class="feedback"><summary>完成第一遍并用外部答案自核后，填写反馈</summary><div class="fields">'
                       + '<label>本题作答开始时间<input class="attempted" type="datetime-local" step="1"></label>'
                       + '<label>第一遍得分率 %<input class="score" type="number" min="0" max="100"></label>'
                       + '<label>用时（分钟）<input class="duration" type="number" min="0.02" step="0.1"></label>'
                       + '<label>最高提示等级<select class="hint"><option>L0</option><option>L1</option><option>L2</option><option>L3</option><option>L4</option></select></label>'
                       + '<label><input class="unseen" type="checkbox">题目陌生</label><label><input class="timed" type="checkbox">限时完成</label>'
                       + '<label>距离上次学习（小时，记录估算可改）<input class="interval" type="number" min="0"></label>'
                       + '<label>复习间隔（天）<input class="review" type="number" min="1" value="2"></label>'
                       + '<label>主要障碍（可空）<select class="error"><option value="">尚未确定 / 无错误</option>' + ''.join('<option value="' + code + '">' + label + '</option>' for code, label in [('concept','概念或条件不清'),('method','方法选择'),('procedure','步骤执行'),('transfer','条件变化'),('speed','超时'),('retention','延迟遗忘')]) + '</select></label>'
                       + ''.join(f'<label>{label}<select class="dim" data-dim="{dim}"><option value="">未观察</option><option value="pass">通过</option><option value="partial">部分通过</option><option value="fail">失败</option></select></label>' for dim, label in zip(lr.DIMENSIONS, ['独立辨型', '步骤执行', '综合迁移', '限时流畅', '延迟保持']))
                       + '</div>' + ability_feedback + '<label><input class="confirmed" type="checkbox">已完成第一遍作答，并用外部权威答案自行核对分数</label></details></article>')
    meta = {'track': track, 'date': day['target_date'], 'mode': paper['mode'], 'questions': [dict({k: q[k] for k in ('number', 'question_id', 'paper_id', 'target_ability_id', 'usage_role', 'was_attempted', 'ordinary_cold_test_eligible', 'last_learning_at')}, requires_preparation=bool(q['preparation'])) for q in paper['questions']]}
    payload = json.dumps(meta, ensure_ascii=False).replace('<', '\\u003c')
    scopes = ('；'.join(paper.get('focus_scopes', [])) or '暂无足够可用题目') if paper['mode'] == 'repair' else '混合调用时不给章节或方法提示'
    counts = ' · '.join(f'{TYPE_NAMES[k]} {n}题' for k, n in paper['counts'].items())
    warnings = ''.join('<li>' + html.escape(w) + '</li>' for w in paper['warnings'])
    title = day['target_date'] + ' · ' + NAMES[track] + '明日练习卷'
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + title + '</title><style>' + CSS + '</style>' + '<script>window.MathJax={tex:{inlineMath:[["$","$"],["\\\\(","\\\\)"]],displayMath:[["$$","$$"],["\\\\[","\\\\]"]]},svg:{fontCache:"local"},options:{enableMenu:false}};</script><script>' + vendor.read_text(encoding='utf-8').replace('</script', '<\\/script') + '</script></head><body><header><div class="eyebrow">每日学习 · 按当天反馈安排</div><h1>' + title + '</h1><p>' + counts + '</p><div class="metrics"><span>作答预算 <b>' + str(paper['budget']['practice_minutes']) + ' 分钟</b></span><span>预计作答 <b>' + str(paper.get('estimated_minutes', 0)) + ' 分钟</b></span><span>本卷 <b>' + str(paper.get('maximum_points', 0)) + ' 分</b></span><span>教学 / 自核 / 复盘预留 <b>' + str(paper['budget']['reserved_minutes']) + ' 分钟</b></span></div><p class="focus">重点章节：' + html.escape(scopes) + '</p><ul class="notes">' + warnings + '</ul><p class="notes">' + ('当前没有真实逐题反馈，本卷按教材顺序生成，尚未推定你的掌握度。' if not day['learner_feedback_count'] else f'依据截至{day["as_of"]}的{day["learner_feedback_count"]}条真实反馈。') + '</p><label><input id="mixed" type="checkbox">本次实际按混合题组作答（导出至少两题、两个能力时有效）</label></header><nav><button id="start">开始计时</button><span id="timer">00:00</span><button onclick="window.print()">打印试卷</button><button id="save">保存本机草稿</button><button id="export">导出自核反馈</button><span id="status" role="status"></span></nav><main>' + ''.join(content) + '</main><footer>卷内不含答案。自核后导出反馈，交给日结流程更新学习情况并生成下一天试卷。草稿只保存在本机浏览器；导出的正式反馈不含作答文字。</footer><script>const META=' + payload + ';</script><script>' + JS + '</script></body></html>'


CSS = '''
:root{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;color:#1c2837;background:#f3f5f8;font-size:16px}*{box-sizing:border-box}body{max-width:1100px;margin:auto;padding:32px}header,article{background:#fff;border:1px solid #dce3eb;border-radius:14px;padding:30px;margin-bottom:24px}.eyebrow{color:#456780;letter-spacing:2px;font-size:13px}h1{font-size:30px;line-height:1.5;margin:12px 0}h2{font-size:22px;padding-left:12px;border-left:4px solid #315976;margin:32px 0 20px}.metrics{display:flex;gap:18px;flex-wrap:wrap;padding:18px 0;border-block:1px solid #e6ecf2}.metrics span{font-size:13px;color:#5c6b7a}.metrics b{display:block;font-size:21px;color:#233f55;margin-top:6px}.notes{color:#647383;font-size:13px;line-height:1.8}.focus{font-size:14px;line-height:1.8}nav{position:sticky;top:0;background:#f3f5f8ed;padding:12px 0;display:flex;align-items:center;gap:10px;flex-wrap:wrap;z-index:10}button{cursor:pointer;color:#fff;background:#315976;border:0;border-radius:7px;padding:10px 15px}#timer{font-variant-numeric:tabular-nums}.qheading{display:flex;gap:12px;justify-content:space-between;align-items:center;border-bottom:1px solid #e6ecf2;padding-bottom:14px}.qheading small{color:#6c7b89}.stem{line-height:1.9;margin:22px 0;overflow-wrap:break-word}.stem img{display:block;max-width:100%;max-height:440px;margin:18px auto}.stem table{border-collapse:collapse;max-width:100%}.stem td{border:1px solid #bbc9d6;padding:6px 12px}.stem pre{white-space:pre-wrap;background:#f3f5f8;padding:14px}.stem mjx-container[display="true"]{overflow-x:auto;overflow-y:hidden}textarea{width:100%;height:160px;margin-top:10px;resize:vertical;font:inherit;padding:12px;border:1px solid #c8d4df;border-radius:6px}.response{font-size:13px;color:#687987}.feedback{margin-top:20px;border-top:1px dashed #dce3eb;padding-top:14px;font-size:14px}.feedback summary{cursor:pointer;color:#315976}.fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;padding:20px 0}.fields label{display:block}.fields input:not([type=checkbox]),select{width:100%;font:inherit;padding:7px;margin-top:5px;border:1px solid #b9c8d5;border-radius:5px}footer{text-align:center;font-size:13px;color:#647383;line-height:1.8;padding:24px}#status{font-size:13px;color:#315976}li{margin:8px 0}
@media(max-width:650px){body{padding:12px}header,article{padding:20px}h1{font-size:23px}.qheading{align-items:flex-start;flex-direction:column}.metrics b{font-size:18px}}
@media print{body{background:white;padding:0;color:black}header,article{border:0;border-radius:0;padding:10px 0;box-shadow:none}nav,.feedback,.notes,footer{display:none}.response textarea{height:150px;border:0;border-bottom:1px solid #ddd}.qheading{break-after:avoid}h2{break-after:avoid}.stem img{max-height:300px}.focus{display:none}}
'''

JS = '''
const status=document.querySelector('#status'), key='daily-practice:'+META.date+':'+META.track;
const cards=[...document.querySelectorAll('article')];
let verificationTimes={};try{verificationTimes=JSON.parse(localStorage.getItem(key+':verified'))||{};}catch(e){}
const downloadLink=document.createElement('a');downloadLink.textContent='保存反馈文件';downloadLink.hidden=true;document.querySelector('nav').appendChild(downloadLink);
const copyBox=document.createElement('details');copyBox.hidden=true;copyBox.innerHTML='<summary>下载不可用时，复制自核反馈交给AI</summary><textarea readonly aria-label="可复制的自核反馈"></textarea>';document.querySelector('nav').after(copyBox);
function controls(card){return [...card.querySelectorAll('input,select,textarea')];}
function save(){try{localStorage.setItem(key,JSON.stringify(cards.map(c=>controls(c).map(e=>e.type==='checkbox'?e.checked:e.value))));status.textContent='草稿已保存在本机';}catch(e){status.textContent='浏览器未允许保存草稿，请导出反馈';}}
try{const stored=JSON.parse(localStorage.getItem(key));if(stored)cards.forEach((c,i)=>controls(c).forEach((e,j)=>{if(stored[i]&&stored[i][j]!==undefined){if(e.type==='checkbox')e.checked=stored[i][j];else e.value=stored[i][j];}}));}catch(e){}
document.querySelector('#save').onclick=save;
cards.forEach((c,i)=>{c.querySelector('.question-start').onclick=()=>{const now=new Date();const local=new Date(now.getTime()-now.getTimezoneOffset()*60000).toISOString().slice(0,19);c.querySelector('.attempted').value=local;const prior=META.questions[i].last_learning_at;if(prior)c.querySelector('.interval').value=Math.max(0,(now-new Date(prior))/3600000).toFixed(2);save();};c.querySelector('.question-finish').onclick=()=>{const start=new Date(c.querySelector('.attempted').value);if(isNaN(start.getTime())||start>new Date()){status.textContent='请先记录本题实际开始时间';return;}c.querySelector('.duration').value=Math.max(0.02,(Date.now()-start.getTime())/60000).toFixed(2);save();status.textContent='已记录第一遍用时，再用外部答案自核';};});
let started=null;document.querySelector('#start').onclick=()=>{if(started)return;started=Date.now();document.querySelector('#start').textContent='计时中';setInterval(()=>{const s=Math.floor((Date.now()-started)/1000);document.querySelector('#timer').textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');},1000);};
document.querySelector('#export').onclick=()=>{
 try{
 const now=new Date(), batch='practice-'+META.date+'-'+META.track;
 const mixed=META.questions.length>=2&&new Set(META.questions.map(q=>q.target_ability_id)).size>=2;
 const rows=META.questions.flatMap((q,i)=>{
  const c=cards[i], field=s=>c.querySelector(s), score=field('.score').value;
  let duration=field('.duration').value;
  if(score===''&&duration==='')return [];
  if(score===''||duration===''||!field('.confirmed').checked)throw Error('第'+q.number+'题请补齐分数、用时和自核确认');
  const attempted=new Date(field('.attempted').value);if(!field('.attempted').value||isNaN(attempted.getTime())||attempted>now)throw Error('第'+q.number+'题请填写实际作答开始时间，或使用开始本题按钮');
  if(!Number.isFinite(Number(score))||Number(score)<0||Number(score)>100||!Number.isFinite(Number(duration))||Number(duration)<=0)throw Error('第'+q.number+'题分数或用时无效');
  const timed=field('.timed').checked, unseen=field('.unseen').checked;
  if(q.was_attempted&&unseen)throw Error('第'+q.number+'题有既往作答，不能再标陌生');
  const interval=field('.interval').value===''?null:Number(field('.interval').value);
  if(interval!==null&&(!Number.isFinite(interval)||interval<0))throw Error('学习间隔无效');
  const dimensions=Object.fromEntries([...c.querySelectorAll('.dim')].map(e=>[e.dataset.dim,e.value||null]));
  if(!timed&&dimensions.timed_fluency!==null)throw Error('第'+q.number+'题未限时，请保留限时流畅为未观察');
  if(dimensions.delayed_retention!==null&&interval===null)throw Error('第'+q.number+'题延迟保持需填写间隔');
  const review=Number(field('.review').value);if(!Number.isFinite(review)||review<1)throw Error('复习间隔至少1天');
  const verified=new Date(verificationTimes[q.question_id]||now.toISOString());if(attempted>verified)throw Error('第'+q.number+'题开始时间晚于此前自核时间，请核对实际时间');
  verificationTimes[q.question_id]=verified.toISOString();const next=new Date(verified.getTime()+review*86400000);
  const checked=[...c.querySelectorAll('.checked-error:checked')].map(e=>e.value);
  const observations=[];
  if(field('.primary-observed').checked)observations.push({ability_id:q.target_ability_id,first_score_pct:Number(score),dimensions,error_code:field('.error').value||null,checked_error_codes:checked});
  [...c.querySelectorAll('.ability-score')].forEach(e=>{if(e.value==='')return;const value=Number(e.value);if(!Number.isFinite(value)||value<0||value>100)throw Error('能力得分率无效');const primary=e.dataset.ability===q.target_ability_id;const obs={ability_id:e.dataset.ability,first_score_pct:value,dimensions:primary?dimensions:Object.fromEntries(Object.keys(dimensions).map(k=>[k,null])),error_code:primary?(field('.error').value||null):null,checked_error_codes:primary?checked:[]};const old=observations.findIndex(o=>o.ability_id===obs.ability_id);if(old>=0)observations[old]=obs;else observations.push(obs);});
  const cold=field('.cold')?.checked||false;
  if(cold&&(!q.ordinary_cold_test_eligible||!unseen||!timed||interval===null||interval<48||field('.hint').value!=='L0'))throw Error('普通冷测需陌生、无提示、限时，且间隔至少48小时');
  return [{schema_version:'attempt-record-v1.1.0',attempt_id:'practice-'+META.date+'-'+META.track+'-'+q.question_id,
   attempted_at:attempted.toISOString(),verified_at:verified.toISOString(),question_id:q.question_id,paper_id:q.paper_id,exam_track:META.track,
   usage_role:q.usage_role,attempt_kind:cold?'cold_test':q.was_attempted?'review_probe':q.requires_preparation?'initial':'near_variant',target_ability_id:observations[0]?.ability_id||q.target_ability_id,ability_observations:observations,
   batch_id:mixed?batch:null,first_score_pct:Number(score),duration_seconds:Math.max(1,Math.round(Number(duration)*60)),
   highest_hint_level_used:field('.hint').value,is_unseen:unseen,is_timed:timed,is_mixed:false,
   interval_hours:interval,primary_error_code:field('.error').value||null,dimensions,next_review_at:next.toISOString(),
   student_verification:{mode:'external_authoritative_self_check',score_confirmed_by_student:true,answer_checked_after_first_pass:true,teacher_answer_access:false},notes:''}];
 });
 if(!rows.length)throw Error('请先填写至少一题自核反馈');
 if(document.querySelector('#mixed').checked){if(rows.length<2||new Set(rows.map(r=>r.target_ability_id)).size<2)throw Error('混合反馈必须包含至少两题、两个能力');rows.forEach(r=>{r.is_mixed=true;});}
 if(rows.some(r=>r.attempt_kind==='cold_test'&&!r.is_mixed))throw Error('普通冷测还需确认实际混合调用，并导出至少两题、两个能力');
 const serialized=rows.map(r=>JSON.stringify(r)).join('\\n')+'\\n';
 const blob=new Blob([serialized],{type:'application/x-ndjson'});
 if(downloadLink.href.startsWith('blob:'))URL.revokeObjectURL(downloadLink.href);
 downloadLink.href=URL.createObjectURL(blob);downloadLink.download=META.date+'-'+META.track+'-feedback.jsonl';downloadLink.hidden=false;
 copyBox.querySelector('textarea').value=serialized;copyBox.hidden=false;
 try{localStorage.setItem(key+':verified',JSON.stringify(verificationTimes));}catch(e){}
 downloadLink.click();save();status.textContent='已生成'+rows.length+'题自核反馈，可保存文件或复制';
 }catch(e){status.textContent=e.message;}
};
'''


def write_artifacts(day, destination):
    destination.mkdir(parents=True)
    (destination / '学习状态与明日计划.json').write_text(lr.dump(public_plan(day)), encoding='utf-8')
    for track in TRACKS:
        (destination / (NAMES[track] + '.html')).write_text(html_paper(day, track), encoding='utf-8')
    links = ''.join(f'<li><a href="{NAMES[t]}.html">{NAMES[t]}练习卷</a> · {sum(day["papers"][t]["counts"].values())}题</li>' for t in TRACKS)
    blocks, shown = [], set()
    for track, paper in day['papers'].items():
        blocks.append('<section><h2>' + NAMES[track] + ' · ' + la.MODES[paper['mode']] + '</h2>')
        for item in paper['learning_blocks']:
            blocks.append('<p><b>' + html.escape(item['ability_name']) + '</b>：' + html.escape(item['action']) + '</p><p>先确认：' + html.escape(item['diagnostic_question']) + '</p>')
            if item['mechanism'] and item['mechanism_id'] not in shown:
                shown.add(item['mechanism_id'])
                blocks.append('<p>' + html.escape(item['mechanism']['model']) + '</p><p>适用边界：' + html.escape(item['mechanism']['boundaries']) + '</p>')
            blocks.append('<p>要看到的改变：' + html.escape(item['expected_change']) + '。' + html.escape(item['verification']) + '。</p>')
        for item in paper.get('method_blocks', []):
            uses = '；'.join(q['question_id'] + ('（子步骤）' if q['extent'] == 'step' else '（完整路线）')
                            for q in item['questions'])
            blocks.append('<p><b>本次复用：' + html.escape(item['name']) + '</b>。' + html.escape(uses) + '</p>'
                          + '<p>' + html.escape(item['principle']) + '</p><p>适用条件：'
                          + html.escape(item['conditions']) + '</p><p>适用边界：'
                          + html.escape(item['boundaries']) + '</p><p>' + html.escape(item['verification']) + '</p>')
        if paper['unplaced_review_tasks']:
            blocks.append('<p>仍有' + str(len(paper['unplaced_review_tasks'])) + '个到期能力或误区任务未安排；明日建议中保留清单。</p>')
        blocks.append('</section>')
    (destination / 'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>明日练习</title><style>' + CSS + '</style><body><header><h1>' + day['target_date'] + ' 明日练习</h1><ul>' + links + '</ul><p>完成后用外部答案自核，导出反馈进行日结。</p>' + ''.join(blocks) + '</header></body></html>', encoding='utf-8')
    report = [f'# {day["target_date"]} 明日学习建议', '', f'截至{day["as_of"]}收到{day["learner_feedback_count"]}条真实反馈。', '']
    if not day['learner_feedback_count']:
        report += ['没有真实逐题反馈，个人掌握度保持未知；本卷按教材顺序及核心覆盖生成。', '']
    for track in TRACKS:
        p = day['papers'][track]
        report += [f'## {NAMES[track]}', '', f'净时间{p["budget"]["net_minutes"]}分钟，作答预算{p["budget"]["practice_minutes"]}分钟，教学/自核/复盘预留{p["budget"]["reserved_minutes"]}分钟。',
                   '用途：' + la.MODES[p['mode']], '题型：' + '、'.join(f'{TYPE_NAMES[k]}{v}题' for k, v in p['counts'].items()), '', '[打开试卷](' + NAMES[track] + '.html)', '']
        for item in p['learning_blocks']:
            report += ['- ' + item['ability_name'] + '：' + item['action'], '  先确认：' + item['diagnostic_question'], '  预期改变：' + item['expected_change'], '  检查方式：' + item['verification']]
        for item in p.get('method_blocks', []):
            report += ['', '本次复用方法：' + item['name'], item['principle'],
                       '适用条件：' + item['conditions'], '边界：' + item['boundaries'],
                       '关联：' + '；'.join(q['question_id'] + ('（子步骤）' if q['extent'] == 'step' else '（完整路线）')
                                        for q in item['questions']), item['verification'], '']
        for q in p['questions']:
            report.append(f'- {q["question_id"]}：{q["reason"]}；{q["scope"]}')
        preparation = {item['id']: item['name'] for q in p['questions'] for item in q['preparation']}
        if preparation:
            report += ['', '作答前先在预留时间内核对/学习这些尚无可靠观察的前置；这类题用于教学后训练，不能当作前置已掌握或冷测认证：', '', *['- ' + name for name in preparation.values()]]
        if p['unplaced_review_tasks']:
            report += ['', '未安排的到期能力 / 误区任务（保留债务，不机械重做所有原题）：', ''] + ['- ' + t['ability_id'] + '；误区：' + (t['error_code'] or '一般保持') for t in p['unplaced_review_tasks']]
        report += ['', '已安排探针也不等于复习完成；只由真实反馈更新实际覆盖的能力和明确核查的误区。']
        report += ['', *p['warnings'], '']
    (destination / '明日建议.md').write_text('\n'.join(report), encoding='utf-8')
    manifest = {'version': VERSION, 'target_date': day['target_date'], 'input_digest': day['input_digest'],
                'output_sha256': {p.name: lr.sha(p) for p in sorted(destination.iterdir())}}
    (destination / 'manifest.json').write_text(lr.dump(manifest), encoding='utf-8')


def verify_frozen(destination):
    manifest = lr.read(destination / 'manifest.json')
    for name, expected in manifest['output_sha256'].items():
        p = lr.inside(destination, name)
        if lr.sha(p) != expected:
            raise ValueError('已冻结的练习卷损坏: ' + name)
    return manifest


def generate(project, as_of, output=None, teacher=None, feedback=None):
    """Validate, prepare artifacts, append supplied real feedback, then publish.

    Stable attempt ids make an interrupted retry idempotent. Differing payloads
    under an existing id are rejected. A day is frozen after publication.
    """
    log = project / lr.ATTEMPTS
    target = as_of + timedelta(days=1)
    destination = output or project / ROOT / str(target)
    with log.open('r+' if feedback else 'r', encoding='utf-8') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        current = lr.jsonl(lock.read())
        proposed = []
        by_id = {r['attempt_id']: r for r in current}
        for row in feedback or []:
            if row['attempt_id'] in by_id:
                if row != by_id[row['attempt_id']]:
                    raise ValueError('已有attempt_id的反馈内容不同，不能覆盖日志')
                continue
            proposed.append(row)
            by_id[row['attempt_id']] = row
        if destination.exists():
            manifest = verify_frozen(destination)
            if manifest['target_date'] != str(target):
                raise ValueError('输出目录属于另一目标日期，请为新的学习日使用新目录')
            if proposed:
                raise ValueError('明日卷已经冻结，新增反馈请用于下一次日结，不覆盖已有卷')
            return {'status': 'REUSED_FROZEN', 'target_date': str(target), 'output': str(destination), 'appended_attempts': 0, 'manifest': manifest}
        day, _, proposed = build_day(project, as_of, teacher, proposed)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix='.practice-', dir=destination.parent))
        shutil.rmtree(temp)
        try:
            write_artifacts(day, temp)
            if proposed:
                lock.seek(0, os.SEEK_END)
                if lock.tell():
                    lock.seek(lock.tell() - 1)
                    if lock.read(1) != '\n':
                        lock.seek(0, os.SEEK_END)
                        lock.write('\n')
                lock.seek(0, os.SEEK_END)
                lock.write(''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in proposed))
                lock.flush()
                os.fsync(lock.fileno())
            temp.rename(destination)
        finally:
            if temp.exists():
                shutil.rmtree(temp)
    return {'status': 'PASS' if all(p['status'] == 'ready' for p in day['papers'].values()) else 'PARTIAL',
            'target_date': str(target), 'output': str(destination),
            'appended_attempts': len(proposed),
            'papers': {t: {'status': p['status'], 'counts': p['counts'], 'estimated_minutes': p.get('estimated_minutes'),
                           'practice_minutes': p['budget']['practice_minutes']} for t, p in day['papers'].items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    for cmd in ('recommend', 'daily-close'):
        p = sub.add_parser(cmd)
        p.add_argument('--as-of', type=date.fromisoformat, default=datetime.now(TZ).date())
        p.add_argument('--teacher-plan', type=Path)
        p.add_argument('--output', type=Path)
        if cmd == 'daily-close':
            p.add_argument('--feedback', type=Path, action='append', default=[])
    check = sub.add_parser('check')
    check.add_argument('--output', type=Path, required=True)
    validate = sub.add_parser('validate-feedback')
    validate.add_argument('--feedback', type=Path, action='append', required=True)
    methods = sub.add_parser('method-report', help='只读查询知识点与方法的多对多关系，不生成最优解')
    methods.add_argument('--question')
    methods.add_argument('--method')
    methods.add_argument('--knowledge')
    args = parser.parse_args()
    try:
        project = args.project.resolve()
        if args.command == 'check':
            result = {'status': 'PASS', 'manifest': verify_frozen(args.output.resolve())}
        elif args.command == 'method-report':
            records, rows, _, _, _ = load_inputs(project)
            library = mr.load_library(project, records)
            excluded, blocked = role_exclusions(project, rows)
            visible = {qid: q for qid, q in records.items() if qid not in excluded and q['l0']['paper_id'] not in blocked}
            result = mr.report(library, visible, args.question, args.method, args.knowledge)
        elif args.command == 'validate-feedback':
            records, current, _, _, _ = load_inputs(project)
            supplied = [r for p in args.feedback for r in lr.jsonl(p.read_text(encoding='utf-8'))]
            existing = {r['attempt_id']: r for r in current}
            for row in supplied:
                if row['attempt_id'] in existing and existing[row['attempt_id']] != row:
                    raise ValueError('已有attempt_id的反馈内容不同')
                existing[row['attempt_id']] = row
            validate_attempts(project, list(existing.values()), records)
            result = {'status': 'PASS', 'supplied_attempts': len(supplied), 'writes': 0}
        else:
            feedback = [r for p in getattr(args, 'feedback', []) for r in lr.jsonl(p.read_text(encoding='utf-8'))]
            teacher = lr.read(args.teacher_plan) if args.teacher_plan else None
            result = generate(project, args.as_of, args.output.resolve() if args.output else None, teacher, feedback)
        print(lr.dump(result), end='')
        return int(result['status'] == 'PARTIAL')
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(lr.dump({'status': 'FAIL', 'error': str(error)}), end='')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
