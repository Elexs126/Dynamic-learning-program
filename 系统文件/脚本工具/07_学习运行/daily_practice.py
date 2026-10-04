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

VERSION = 'daily-practice-v1.0.0'
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
    schema = lr.schema_runtime(project).__class__(project / '系统文件/数据规范/attempt_record.schema.json')
    ids, errors, by_question, batches = set(), [], defaultdict(list), defaultdict(list)
    for i, row in enumerate(rows, 1):
        e = schema.validate(row)
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
        try:
            for k in ('attempted_at', 'verified_at', 'next_review_at'):
                aware(row[k])
            validator.validate_record(dict(row, __line_number=i), errors)
        except (ValueError, TypeError) as exc:
            errors.append(f'第{i}条: {exc}')
        by_question[row['question_id']].append(row)
        if row['is_mixed']:
            batches[row['batch_id']].append(row)
    for qid, qs in by_question.items():
        ordered = sorted(qs, key=lambda a: aware(a['attempted_at']))
        if any(a['is_unseen'] for a in ordered[1:]):
            errors.append('重复题不能仍标陌生: ' + qid)
    for batch, qs in batches.items():
        if len({a['question_id'] for a in qs}) < 2 or len({a['target_ability_id'] for a in qs if a['target_ability_id']}) < 2:
            errors.append('混合题组必须含至少两题及两个目标能力: ' + str(batch))
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
    l2 = q.get('l2') or {}
    if l2.get('main_knowledge') and l2.get('review_status_by_field', {}).get('main_knowledge') == 'verified':
        return l2['main_knowledge']['id']
    return 'scope:' + q['l1']['official_scope_coarse']


def scope(q):
    return q['l1']['official_scope_coarse']


def derive_state(records, rows, summaries, as_of, threshold):
    cutoff = end_of_day(as_of)
    usable = [a for a in rows if aware(a['attempted_at']) < cutoff and aware(a['verified_at']) < cutoff]
    usable.sort(key=lambda a: (aware(a['attempted_at']), a['attempt_id']))
    groups, latest = defaultdict(list), {}
    for a in usable:
        latest[a['question_id']] = a
        groups[knowledge(records[a['question_id']])].append(a)
    abilities = {}
    for kid, attempts in groups.items():
        dims = {k: None for k in lr.DIMENSIONS}
        successes = set()
        for a in attempts:
            for k, v in a['dimensions'].items():
                if v is not None:
                    dims[k] = v
            if (a['is_unseen'] and a['highest_hint_level_used'] == 'L0'
                    and a['first_score_pct'] >= threshold
                    and a['attempt_kind'] == 'near_variant'
                    and a['usage_role'] in {'TRAIN', 'AUX_OFFPOLICY'}):
                successes.add(a['question_id'])
        last = attempts[-1]
        q = records[last['question_id']]
        recent_fail = last['first_score_pct'] < threshold or any(v in {'fail', 'partial'} for v in dims.values())
        abilities[kid] = {
            'knowledge_id': kid, 'name': (q.get('l2') or {}).get('main_knowledge', {}).get('name', scope(q)),
            'exam_track': last['exam_track'], 'scope': scope(q),
            'stage': '工作掌握' if len(successes) >= 2 and not kid.startswith('scope:') else '已接触',
            'independent_certification': 'unverified',
            'weak': recent_fail, 'dimensions': dims, 'attempt_count': len(attempts),
            'last_score_pct': last['first_score_pct'], 'last_attempted_at': last['attempted_at'],
            'next_review_at': last['next_review_at'],
            'due': aware(last['next_review_at']) < end_of_day(as_of + timedelta(days=1))
        }
    return {'version': VERSION, 'as_of': str(as_of), 'attempt_count': len(usable),
            'unobserved_ability_status': None, 'abilities': abilities,
            'latest_questions': latest,
            'whole_exam_summaries': [s for s in summaries if aware(s['verified_at']) < cutoff],
            'E_metrics': None,
            'notes': ['整科总分不推导单项掌握；训练反馈不自动激活独立认证；未观察五维保持null。']}, usable


def validate_teacher_plan(plan, records):
    if not isinstance(plan, dict) or set(plan) - {'version', 'effective_week_start', 'weekly_allocation', 'subjects'}:
        raise ValueError('Teacher计划只接受版本、预算周、周分配及subjects')
    if plan.get('version') != 'daily-teacher-plan-v1':
        raise ValueError('Teacher计划version应为daily-teacher-plan-v1')
    if set(plan.get('subjects', {})) - set(TRACKS):
        raise ValueError('未知学科')
    known = {knowledge(q): q['l0']['exam_track'] for q in records.values()}
    scopes = {scope(q): q['l0']['exam_track'] for q in records.values()}
    fields = {'priority_knowledge_ids', 'required_knowledge_ids', 'working_knowledge_ids',
              'frontier_scopes', 'exclude_question_ids', 'practice_minutes'}
    for track, subject in plan.get('subjects', {}).items():
        if not isinstance(subject, dict) or set(subject) - fields:
            raise ValueError('未知Teacher学科计划字段')
        for key, values in subject.items():
            if key == 'practice_minutes':
                if not lr.finite(values, 1):
                    raise ValueError('practice_minutes必须为正数')
                continue
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                raise ValueError(key + '必须为字符串数组')
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


def prepare_candidates(project, records, state, attempts, navigation, track, teacher):
    subject = teacher.get('subjects', {}).get(track, {})
    excluded, blocked_papers = role_exclusions(project, attempts)
    excluded.update(subject.get('exclude_question_ids', []))
    abilities, latest = state['abilities'], state['latest_questions']
    seen = set(latest)
    seen_hashes = {records[q]['l0']['question_hash_sha256'] for q in seen}
    due = {q for q, a in latest.items() if a['exam_track'] == track and q not in excluded
           and records[q]['l0']['paper_id'] not in blocked_papers
           and aware(a['next_review_at']) < end_of_day(date.fromisoformat(state['as_of']) + timedelta(days=1))}
    weak = {k for k, a in abilities.items() if a['exam_track'] == track and a['weak']}
    weak_scopes = {a['scope'] for a in abilities.values() if a['exam_track'] == track and a['weak']}
    working = {k for k, a in abilities.items() if a['stage'] == '工作掌握' and not a['weak']} | set(subject.get('working_knowledge_ids', []))
    priority = set(subject.get('priority_knowledge_ids', []))
    required = set(subject.get('required_knowledge_ids', []))
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
        kid, sc = knowledge(q), scope(q)
        if l0['exam_track'] != track or qid in excluded or l0['paper_id'] in blocked_papers:
            continue
        if l0['question_type'] not in TYPE_NAMES or (track == 'CS408' and l0['question_type'] == 'fill'):
            continue
        if (qid in seen or l0['question_hash_sha256'] in seen_hashes) and qid not in due:
            continue
        if qid not in due and kid not in required | priority | weak and sc not in covered | frontier:
            continue
        prereqs = l2.get('prerequisites') or {}
        missing = [p for p in prereqs.get('hard_prerequisite', []) if p['id'] not in working]
        # Missing observations are not failed prerequisites. At the initial
        # frontier, unknown prerequisites become explicit preparation tasks;
        # observed insufficient prerequisites do block new downstream work.
        blocked = [p for p in missing if p['id'] in abilities]
        if blocked and qid not in due:
            continue
        dependency = l3.get('inter_question_dependency') or {}
        if dependency.get('unresolved_legacy_note'):
            continue
        if any(r['from_question_id'].split('#')[0] != qid or r['to_question_id'].split('#')[0] != qid
               for r in dependency.get('relations', [])):
            continue  # keep internally dependent subparts intact; no orphan cross-question context
        if qid in due:
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
        # Current repaired mathematical sources are preferred within an equal
        # learning need. Source preference never overrides due/Teacher priorities.
        candidates.append({'question_id': qid, 'q': q, 'knowledge_id': kid, 'reason': reason,
                           'preparation': missing,
                           'rank': (rank, order.get(sc, 999), difficulty,
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


def select_paper(project, candidates, due, order, track, budget, speed, policy):
    blueprint = policy['blueprints'][track]
    unavailable = {}
    bodies = {}
    limit = math.floor(sum(blueprint['counts'].values()) * policy['maximum_paper_scale'])
    best = None
    for total in range(limit, policy['minimum_questions'][track] - 1, -1):
        counts = proportional_counts(total, blueprint['counts'])
        if not all(counts.values()):
            continue
        estimate = sum(counts[k] * speed[k]['minutes'] for k in counts)
        if estimate > budget['practice_minutes']:
            continue
        selected, hashes, clusters, remaining = [], set(), set(), dict(counts)
        for c in candidates:
            qid, q = c['question_id'], c['q']
            kind = q['l0']['question_type']
            fingerprint = q['l0']['question_hash_sha256']
            relation = (q.get('l3') or {}).get('isomorphic_relation') or {}
            cluster = relation.get('cluster_id') if relation.get('status') == 'verified' else None
            if not remaining.get(kind) or fingerprint in hashes or (cluster and cluster in clusters and c['reason'] != '到期复习'):
                continue
            if qid in unavailable:
                continue
            try:
                if qid not in bodies:
                    body, source = question_body(project, q)
                    bodies[qid] = render_markdown(body, source, project)
            except ValueError as error:
                unavailable[qid] = str(error)
                continue
            selected.append(c)
            hashes.add(fingerprint)
            if cluster:
                clusters.add(cluster)
            remaining[kind] -= 1
        if any(remaining.values()):
            continue
        best = (selected, counts, estimate)
        break
    if best is None:
        return {'exam_track': track, 'status': 'insufficient_eligible_questions_or_time', 'questions': [],
                'counts': {k: 0 for k in blueprint['counts']}, 'budget': budget, 'speed': speed,
                'warnings': ['当前学习前沿/完整题干/时间不足以组成含全部题型的小卷；保留教学与复习任务，补充Teacher学习前沿后再生成。'],
                'unplaced_due_question_ids': sorted(due), 'unavailable_questions': unavailable}
    selected, counts, estimate = best
    selected.sort(key=lambda c: (list(blueprint['counts']).index(c['q']['l0']['question_type']), c['rank']))
    questions, slots = [], Counter()
    for number, c in enumerate(selected, 1):
        q, qid = c['q'], c['question_id']
        l0, kind = q['l0'], q['l0']['question_type']
        points = l0['original_points']
        training = blueprint['points'][kind]
        if points is None:
            points = training[slots[kind] % len(training)] if isinstance(training, list) else training
        slots[kind] += 1
        questions.append({'number': number, 'question_id': qid, 'paper_id': l0['paper_id'],
                          'question_type': kind, 'points': points,
                          'point_basis': 'original' if l0['original_points'] is not None else 'training_assignment',
                          'estimated_minutes': speed[kind]['minutes'],
                          'source_file': l0['source_file'], 'source_locator': l0['source_locator'],
                          'source_sha256': lr.sha(lr.inside(project, l0['source_file'])),
                          'scope': scope(q), 'knowledge_id': c['knowledge_id'],
                          'target_ability_id': c['knowledge_id'], 'reason': c['reason'],
                          'preparation': c.get('preparation', []),
                          'was_attempted': qid in due,
                          'usage_role': 'TRAIN' if l0['source_file'].startswith('核心真题/') else 'AUX_OFFPOLICY',
                          'body_html': bodies[qid]})
    outstanding = sorted(due - {q['question_id'] for q in questions})
    warnings = ['整数题量按真题数量比例取整，分值保留原题；旧年份及不同大题分值会使分值占比略有偏差。']
    if outstanding:
        warnings.append(f'{len(outstanding)}道到期题未装入比例小卷，已列入单独强制复习清单；优先占用预留时间，不因卷面比例删除复习债务。')
    return {'exam_track': track, 'status': 'ready', 'counts': counts, 'reference_counts': blueprint['counts'],
            'estimated_minutes': round(estimate, 2), 'budget': budget, 'speed': speed,
            'maximum_points': sum(q['points'] for q in questions), 'questions': questions,
            'focus_scopes': list(dict.fromkeys(q['scope'] for q in questions)),
            'warnings': warnings, 'unplaced_due_question_ids': outstanding, 'unavailable_questions': unavailable}


def build_day(project, as_of, teacher=None, new_rows=None):
    records, rows, summaries, navigation, selector = load_inputs(project)
    teacher = teacher or {'version': 'daily-teacher-plan-v1', 'subjects': {}}
    validate_teacher_plan(teacher, records)
    if new_rows:
        rows = rows + new_rows
        validate_attempts(project, rows, records)
        if any(aware(a['verified_at']) >= end_of_day(as_of) for a in new_rows):
            raise ValueError('新增反馈的自核日期不能晚于本次日结')
    policy = lr.read(project / CONFIG)
    target = as_of + timedelta(days=1)
    state, usable = derive_state(records, rows, summaries, as_of, policy['score_threshold_pct'])
    budgets = time_budgets(lr.read(project / '系统文件/系统配置/execution_contract_v1.json'), policy, teacher, target)
    papers = {}
    for track in TRACKS:
        speed = estimate_speed(records, usable, track, policy)
        candidates, due, order = prepare_candidates(project, records, state, usable, navigation, track, teacher)
        papers[track] = select_paper(project, candidates, due, order, track, budgets[track], speed, policy)
    result = {'version': VERSION, 'as_of': str(as_of), 'target_date': str(target),
              'learner_feedback_count': state['attempt_count'], 'state': state, 'papers': papers,
              'teacher_plan': teacher, 'policy': policy,
              'catalog_snapshot': selector['runtime_snapshot'],
              'input_digest': digest({'attempts': rows, 'summaries': summaries, 'teacher': teacher, 'policy': policy})}
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
        content.append(f'<article id="q{q["number"]}"><div class="qheading"><b>第{q["number"]}题 · {q["points"]}分</b><small>{basis} · 预计{q["estimated_minutes"]}分钟</small></div>'
                       + '<div class="stem">' + q['body_html'] + '</div><button class="question-start">开始本题</button><label class="response">答题区<textarea placeholder="在这里记录作答，或在纸上完成"></textarea></label>'
                       + f'<details class="feedback"><summary>完成第一遍并用外部答案自核后，填写反馈</summary><div class="fields">'
                       + '<label>本题作答开始时间<input class="attempted" type="datetime-local" step="1"></label>'
                       + '<label>第一遍得分率 %<input class="score" type="number" min="0" max="100"></label>'
                       + '<label>用时（分钟）<input class="duration" type="number" min="0.02" step="0.1"></label>'
                       + '<label>最高提示等级<select class="hint"><option>L0</option><option>L1</option><option>L2</option><option>L3</option><option>L4</option></select></label>'
                       + '<label><input class="unseen" type="checkbox">题目陌生</label><label><input class="timed" type="checkbox">限时完成</label>'
                       + '<label>距离上次学习（小时，可空）<input class="interval" type="number" min="0"></label>'
                       + '<label>复习间隔（天）<input class="review" type="number" min="1" value="2"></label>'
                       + '<label>主要错误（可空）<input class="error" type="text"></label>'
                       + ''.join(f'<label>{label}<select class="dim" data-dim="{dim}"><option value="">未观察</option><option value="pass">通过</option><option value="partial">部分通过</option><option value="fail">失败</option></select></label>' for dim, label in zip(lr.DIMENSIONS, ['独立辨型', '步骤执行', '综合迁移', '限时流畅', '延迟保持']))
                       + '</div><label><input class="confirmed" type="checkbox">已完成第一遍作答，并用外部权威答案自行核对分数</label></details></article>')
    meta = {'track': track, 'date': day['target_date'], 'questions': [dict({k: q[k] for k in ('number', 'question_id', 'paper_id', 'target_ability_id', 'usage_role', 'was_attempted')}, requires_preparation=bool(q['preparation'])) for q in paper['questions']]}
    payload = json.dumps(meta, ensure_ascii=False).replace('<', '\\u003c')
    scopes = '；'.join(paper.get('focus_scopes', [])) or '暂无足够可用题目'
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
cards.forEach(c=>{c.querySelector('.question-start').onclick=()=>{const now=new Date();const local=new Date(now.getTime()-now.getTimezoneOffset()*60000).toISOString().slice(0,19);c.querySelector('.attempted').value=local;save();};});
let started=null;document.querySelector('#start').onclick=()=>{if(started)return;started=Date.now();document.querySelector('#start').textContent='计时中';setInterval(()=>{const s=Math.floor((Date.now()-started)/1000);document.querySelector('#timer').textContent=String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');},1000);};
document.querySelector('#export').onclick=()=>{
 try{
 const now=new Date(), batch='practice-'+META.date+'-'+META.track;
 const mixed=META.questions.length>=2&&new Set(META.questions.map(q=>q.target_ability_id)).size>=2;
 const rows=META.questions.flatMap((q,i)=>{
  const c=cards[i], field=s=>c.querySelector(s), score=field('.score').value, duration=field('.duration').value;
  if(score===''&&duration==='')return [];
  if(score===''||duration===''||!field('.confirmed').checked)throw Error('第'+q.number+'题请补齐分数、用时和自核确认');
  const attempted=new Date(field('.attempted').value);if(!field('.attempted').value||isNaN(attempted.getTime())||attempted>now)throw Error('第'+q.number+'题请填写实际作答开始时间，或使用开始本题按钮');
  if(!Number.isFinite(Number(score))||Number(score)<0||Number(score)>100||!Number.isFinite(Number(duration))||Number(duration)<=0)throw Error('第'+q.number+'题分数或用时无效');
  const timed=field('.timed').checked, unseen=field('.unseen').checked;
  if(q.was_attempted&&unseen)throw Error('第'+q.number+'题有既往作答，不能再标陌生');
  const interval=field('.interval').value===''?null:Number(field('.interval').value);
  const dimensions=Object.fromEntries([...c.querySelectorAll('.dim')].map(e=>[e.dataset.dim,e.value||null]));
  if(!timed&&dimensions.timed_fluency!==null)throw Error('第'+q.number+'题未限时，请保留限时流畅为未观察');
  if(dimensions.delayed_retention!==null&&interval===null)throw Error('第'+q.number+'题延迟保持需填写间隔');
  const review=Number(field('.review').value);if(!Number.isFinite(review)||review<1)throw Error('复习间隔至少1天');
  const verified=new Date(verificationTimes[q.question_id]||now.toISOString());if(attempted>verified)throw Error('第'+q.number+'题开始时间晚于此前自核时间，请核对实际时间');
  verificationTimes[q.question_id]=verified.toISOString();const next=new Date(verified.getTime()+review*86400000);
  return [{schema_version:'attempt-record-v1.0.0',attempt_id:'practice-'+META.date+'-'+META.track+'-'+q.question_id,
   attempted_at:attempted.toISOString(),verified_at:verified.toISOString(),question_id:q.question_id,paper_id:q.paper_id,exam_track:META.track,
   usage_role:q.usage_role,attempt_kind:q.was_attempted?'review_probe':q.requires_preparation?'initial':'near_variant',target_ability_id:q.target_ability_id,
   batch_id:mixed?batch:null,first_score_pct:Number(score),duration_seconds:Math.max(1,Math.round(Number(duration)*60)),
   highest_hint_level_used:field('.hint').value,is_unseen:unseen,is_timed:timed,is_mixed:false,
   interval_hours:interval,primary_error_code:field('.error').value||null,dimensions,next_review_at:next.toISOString(),
   student_verification:{mode:'external_authoritative_self_check',score_confirmed_by_student:true,answer_checked_after_first_pass:true,teacher_answer_access:false},notes:''}];
 });
 if(!rows.length)throw Error('请先填写至少一题自核反馈');
 if(document.querySelector('#mixed').checked){if(rows.length<2||new Set(rows.map(r=>r.target_ability_id)).size<2)throw Error('混合反馈必须包含至少两题、两个能力');rows.forEach(r=>{r.is_mixed=true;});}
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
    (destination / 'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>明日练习</title><style>' + CSS + '</style><body><header><h1>' + day['target_date'] + ' 明日练习</h1><ul>' + links + '</ul><p>完成后用外部答案自核，导出反馈进行日结。</p></header></body></html>', encoding='utf-8')
    report = [f'# {day["target_date"]} 明日学习建议', '', f'截至{day["as_of"]}收到{day["learner_feedback_count"]}条真实反馈。', '']
    if not day['learner_feedback_count']:
        report += ['没有真实逐题反馈，个人掌握度保持未知；本卷按教材顺序及核心覆盖生成。', '']
    for track in TRACKS:
        p = day['papers'][track]
        report += [f'## {NAMES[track]}', '', f'净时间{p["budget"]["net_minutes"]}分钟，作答预算{p["budget"]["practice_minutes"]}分钟，教学/自核/复盘预留{p["budget"]["reserved_minutes"]}分钟。',
                   '题型：' + '、'.join(f'{TYPE_NAMES[k]}{v}题' for k, v in p['counts'].items()), '', '[打开试卷](' + NAMES[track] + '.html)', '']
        for q in p['questions']:
            report.append(f'- {q["question_id"]}：{q["reason"]}；{q["scope"]}')
        preparation = {item['id']: item['name'] for q in p['questions'] for item in q['preparation']}
        if preparation:
            report += ['', '作答前先在预留时间内核对/学习这些尚无可靠观察的前置；这类题用于教学后训练，不能当作前置已掌握或冷测认证：', '', *['- ' + name for name in preparation.values()]]
        if p['unplaced_due_question_ids']:
            report += ['', '必须补做的到期复习（先占用预留时间，超时则保留债务并反馈）：', ''] + ['- ' + q for q in p['unplaced_due_question_ids']]
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
    args = parser.parse_args()
    try:
        project = args.project.resolve()
        if args.command == 'check':
            result = {'status': 'PASS', 'manifest': verify_frozen(args.output.resolve())}
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
