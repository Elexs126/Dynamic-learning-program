#!/usr/bin/env python3
"""Local, read-only learning navigation and conservative runtime preflight.

Only offline-append mutates a learner log, and only with supplied real feedback.
Build writes derived artifacts to an explicitly selected output directory.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
from zoneinfo import ZoneInfo

VERSION = 'learning-runtime-v1.1.0'
SYS = '系统文件/'
POLICY = SYS + '系统配置/runtime_policy_v1.json'
OFFLINE_SCHEMA = SYS + '数据规范/offline_assessment_summary.schema.json'
OFFLINE_LOG = SYS + '做题记录/offline_assessment_summaries_v1.jsonl'
ATTEMPTS = SYS + '做题记录/attempts_v1.jsonl'
ANNOTATIONS = [
    SYS + '题目标注/L1/question_annotations_l1_v1.json',
    SYS + '题目标注/数学一_L2_L3/question_annotations_math1_l23_v1.json',
    SYS + '题目标注/408_2009_2012_L3/question_annotations_cs408_2009_2012_l23_v1.json',
    SYS + '题目标注/408_2013_2026_L3/question_annotations_cs408_2013_2026_l23_v1.json',
]
COURSES = [
    ('m1_calculus', '高等数学', 'calculus', 'MATH1'),
    ('m1_linear_algebra', '线性代数', 'linear_algebra', 'MATH1'),
    ('m1_prob', '概率论与数理统计', 'probability', 'MATH1'),
    ('408_ds', '数据结构', 'data_structure', 'CS408'),
    ('408_co', '计算机组成原理', 'computer_organization', 'CS408'),
    ('408_os', '操作系统', 'operating_system', 'CS408'),
    ('408_cn', '计算机网络', 'computer_network', 'CS408'),
]
DIMENSIONS = ('independent_recognition', 'procedural_execution', 'transfer',
              'timed_fluency', 'delayed_retention')
E_CHECKS = ('complete_paper_verified', 'teacher_visibility_and_role_verified',
            'primary_stat_labels_verified', 'points_verified',
            'atomic_units_verified', 'target_comparability_verified')


def fail_constant(value):
    raise ValueError('Non-finite JSON number: ' + value)


def loads(text):
    return json.loads(text, parse_constant=fail_constant)


def read(path):
    return loads(Path(path).read_text(encoding='utf-8'))


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside(project, relative):
    result = (project / relative).resolve()
    if not result.is_relative_to(project.resolve()):
        raise ValueError('Path escapes project: ' + relative)
    return result


def unique(records, key):
    result = {}
    for record in records:
        value = record[key]
        if value in result:
            raise ValueError('Duplicate ' + key + ': ' + value)
        result[value] = record
    return result


def jsonl(text):
    rows = []
    for line, raw in enumerate(text.splitlines(), 1):
        if raw.strip():
            value = loads(raw)
            if not isinstance(value, dict):
                raise ValueError(f'JSONL line {line} is not an object')
            rows.append(value)
    return rows


def merge_annotations(bundles):
    latest, paths = {}, {}
    for i, (path, bundle) in enumerate(bundles):
        records = unique(bundle['records'], 'question_id')
        if bundle['record_count'] != len(records):
            raise ValueError('Incorrect record_count: ' + path)
        for qid, record in records.items():
            if i:
                if qid not in latest or paths[qid] != bundles[0][0]:
                    raise ValueError('Missing L1 or conflicting L3 snapshot: ' + qid)
                if record['l0'] != latest[qid]['l0'] or record['l1'] != latest[qid]['l1']:
                    raise ValueError('L0/L1 changed in overlay: ' + qid)
            latest[qid], paths[qid] = record, path
    return latest, paths


def qualify_paper(decisions=None):
    """A targeted prerequisite check, never an all-L3-complete gate.

    The caller must provide independently grounded decisions. This module does
    not manufacture them from tag confidence or infer a formal E sample.
    """
    decisions = decisions or {}
    missing = [key for key in E_CHECKS if decisions.get(key) is not True]
    return {'eligible': not missing, 'unresolved_checks': missing}


def finite(value, minimum=0):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value) and value >= minimum
    except OverflowError:
        return False


def budget_preflight(request, today=None):
    """Read-only admission check; not a billing meter or concurrent reservation."""
    today = today or datetime.now(ZoneInfo('Asia/Shanghai')).date()
    why = []
    required = {'unit', 'unit_name', 'week_start', 'limit', 'used', 'reserved',
                'estimate', 'retry_reserve', 'max_input_tokens_per_call',
                'max_output_tokens_per_call'}
    if not isinstance(request, dict) or set(request) != required:
        return {'allowed': False, 'reasons': ['budget_fields_missing_or_unknown'],
                'remaining_before_batch': None, 'remaining_after_batch': None}
    if request['unit'] not in ('tokens', 'currency', 'calls'):
        why.append('unsupported_unit')
    if not isinstance(request['unit_name'], str) or not request['unit_name'].strip():
        why.append('explicit_unit_name_required')
    for key in ('limit', 'used', 'reserved', 'estimate', 'retry_reserve'):
        if not finite(request[key]):
            why.append(key + '_unknown_or_invalid')
        elif request['unit'] in ('tokens', 'calls') and type(request[key]) is not int:
            why.append(key + '_must_be_integer')
    try:
        start = date.fromisoformat(request['week_start'])
        if start.weekday() != 0 or not start <= today < start + timedelta(days=7):
            why.append('budget_week_not_current')
    except (ValueError, TypeError):
        why.append('budget_week_invalid')
    for key in ('max_input_tokens_per_call', 'max_output_tokens_per_call'):
        value = request[key]
        if request['unit'] == 'calls' and (type(value) is not int or value < 1):
            why.append(key + '_required_for_call_budget')
        elif value is not None and (type(value) is not int or value < 1):
            why.append(key + '_invalid')
    if why:
        return {'allowed': False, 'reasons': why,
                'remaining_before_batch': None, 'remaining_after_batch': None}
    remaining = request['limit'] - request['used'] - request['reserved']
    after = remaining - request['estimate'] - request['retry_reserve']
    if remaining <= 0:
        why.append('cap_reached')
    if after < 0:
        why.append('batch_and_retry_exceed_remaining')
    return {'allowed': not why, 'reasons': why,
            'remaining_before_batch': remaining, 'remaining_after_batch': after,
            'reservation_created': False, 'external_call_performed': False}


def schema_runtime(project):
    path = project / SYS / '脚本工具/05_标注与规范校验/json_schema_runtime.py'
    spec = importlib.util.spec_from_file_location('local_schema_runtime', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SchemaRuntime(project / OFFLINE_SCHEMA)


def aware_time(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Explicit timezone required')
    return result


def validate_summary(record, runtime):
    errors = runtime.validate(record)
    if errors:
        return errors
    for key in ('earned_points', 'maximum_points'):
        if not finite(record[key]):
            errors.append(key + ': finite number required')
    if errors:
        return errors
    if record['earned_points'] > record['maximum_points']:
        errors.append('earned_points exceeds maximum_points')
    try:
        if aware_time(record['verified_at']) < aware_time(record['completed_at']):
            errors.append('verified_at precedes completed_at')
    except (ValueError, TypeError):
        errors.append('timestamps require valid explicit timezone')
    # Whole-exam totals carry no per-ability observations. v1 deliberately leaves
    # all five dimensions null; a future compatible evidence interface may add them.
    return errors


def validate_summaries(rows, runtime):
    errors, seen = [], set()
    for index, row in enumerate(rows, 1):
        errors.extend(f'line {index}: {e}' for e in validate_summary(row, runtime))
        key = row.get('summary_id')
        if isinstance(key, str):
            if key in seen:
                errors.append(f'line {index}: duplicate summary_id')
            seen.add(key)
    return errors


def append_summary(path, record, runtime):
    """Under exclusive lock: validate all history, reject duplicates, append once."""
    errors = validate_summary(record, runtime)
    if errors:
        raise ValueError('; '.join(errors))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # a+ does not truncate. A missing final newline is repaired only on success.
    with path.open('a+', encoding='utf-8') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        original = handle.read()
        rows = jsonl(original)
        errors = validate_summaries(rows + [record], runtime)
        if errors:
            raise ValueError('; '.join(errors))
        separator = '\n' if original and not original.endswith('\n') else ''
        handle.write(separator + json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
        handle.flush()
        os.fsync(handle.fileno())
    return {'status': 'APPENDED', 'summary_id': record['summary_id'],
            'record_count': len(rows) + 1, 'independent_measurement_activated': False}


def build(project, policy):
    inputs = {}

    def tracked(relative, kind='json'):
        path = inside(project, relative)
        raw = path.read_bytes()
        inputs[relative] = hashlib.sha256(raw).hexdigest()
        return loads(raw) if kind == 'json' else raw.decode('utf-8')

    selector_path = SYS + '系统配置/annotation_sources_current_v1.json'
    if (project / selector_path).exists():
        selector = tracked(selector_path)
        annotation_paths = selector['annotation_files']
        if len(annotation_paths) != 4 or len(set(annotation_paths)) != 4:
            raise ValueError('Current annotation selector requires four distinct snapshots')
        release_manifest = tracked(selector['release_manifest'])
        release_root = Path(selector['release_manifest']).parent
        for prefix, hashes in ((Path('.'), release_manifest['input_sha256']),
                               (release_root, release_manifest['output_sha256'])):
            for relative, expected in hashes.items():
                source_path = (prefix / relative).as_posix()
                current = sha(inside(project, source_path))
                if current != expected:
                    raise ValueError('Current release source/output changed: ' + source_path)
                inputs[source_path] = current
        builder_path = selector['release_builder']
        inputs[builder_path] = sha(inside(project, builder_path))
        if inputs[builder_path] != release_manifest['builder_sha256']:
            raise ValueError('Current release builder changed')
        baseline = tracked(selector['canonical_sources'])
    else:
        annotation_paths = ANNOTATIONS
        baseline = tracked(SYS + '系统配置/canonical_sources_v1.json')
    contract = tracked(SYS + '系统配置/execution_contract_v1.json')
    if inputs[SYS + '系统配置/execution_contract_v1.json'] != policy['base_contract_sha256']:
        raise ValueError('Frozen base contract changed; policy needs a new version')
    if contract['time_budget'] != policy['time_budget']:
        raise ValueError('Policy must preserve the agreed time budget')
    for implementation in ('07_学习运行/learning_runtime.py',
                           '05_标注与规范校验/json_schema_runtime.py'):
        path = SYS + '脚本工具/' + implementation
        inputs[path] = sha(inside(project, path))
    bundles = [(p, tracked(p)) for p in annotation_paths]
    latest, paths = merge_annotations(bundles)
    if len(latest) != baseline['expected_unique_question_records']:
        raise ValueError('Canonical baseline count mismatch')
    source_counts = Counter()
    source_by_qid = {}
    for qid, r in latest.items():
        matches = [s for s in baseline['sources'] if
                   Path(r['l0']['source_file']).is_relative_to(s['canonical_path'])]
        if len(matches) != 1:
            raise ValueError('Ambiguous/noncanonical source: ' + qid)
        source_by_qid[qid] = matches[0]
        source_counts[matches[0]['source_id']] += 1
        relative = r['l0']['source_file']
        if relative not in inputs:
            # Mechanical provenance hashing, no textbook or question reannotation.
            inputs[relative] = sha(inside(project, relative))
    for s in baseline['sources']:
        if source_counts[s['source_id']] != s['expected_records']:
            raise ValueError('Canonical source count mismatch: ' + s['source_id'])

    evidence = {}
    for path in annotation_paths[1:]:
        ep = str(Path(path).parent / 'field_evidence_v1.jsonl')
        records = unique(jsonl(tracked(ep, 'text')), 'question_id')
        expected = {q for q, p in paths.items() if p == path}
        if set(records) != expected or set(evidence) & set(records):
            raise ValueError('Review evidence coverage mismatch: ' + ep)
        for q, r in records.items():
            evidence[q] = {'evidence_file': ep, 'reviewer_kind': r['reviewer_kind'],
                           'human_review_performed': r['human_review_performed']}

    questions, core, pending = [], defaultdict(list), []
    exposure = []
    for qid, r in sorted(latest.items()):
        l0 = r['l0']
        row = {key: l0[key] for key in ('exam_track', 'subject_area', 'paper_id',
               'year', 'question_number', 'original_points', 'source_file',
               'source_locator', 'question_hash_sha256')}
        row.update(question_id=qid, annotation_file=paths[qid],
                   annotation_depth=r['annotation_depth'],
                   source_id=source_by_qid[qid]['source_id'],
                   official_scope_coarse=r['l1']['official_scope_coarse'],
                   main_knowledge=(r['l2'] or {}).get('main_knowledge'),
                   field_omissions=r.get('field_omissions', []))
        questions.append(row)
        if source_by_qid[qid]['eligible_for_target_prior']:
            core[l0['paper_id']].append(r)
        if any(x['reason_type'] == 'human_review_needed' for x in row['field_omissions']):
            pending.append(row)
        ev = evidence.get(qid)
        if ev and ev['reviewer_kind'] == 'assistant_offline_semantic_review':
            exposure.append({'question_id': qid, **ev,
                             'student_seen_status': 'unknown_current',
                             'hidden_measurement_eligible': False})
    papers = []
    for paper, records in sorted(core.items()):
        meta = records[0]['l0']
        papers.append({'paper_id': paper, 'exam_track': meta['exam_track'],
                       'year': meta['year'], 'question_count': len(records),
                       'local_main_label_verified_count': sum(
                           (r['l2'] or {}).get('review_status_by_field', {}).get('main_knowledge') == 'verified'
                           for r in records),
                       'atomization_unreviewed_count': sum(
                           'ATOMIZATION_NOT_REVIEWED' in r['review_flags'] for r in records),
                       'human_issue_question_count': sum(bool(r.get('field_omissions')) for r in records),
                       'formal_sample_status': 'not_established',
                       **qualify_paper()})
    if sum(p['question_count'] for p in papers) != baseline['target_prior_eligible_records']:
        raise ValueError('Core candidate count mismatch')

    base = SYS + '考纲与教材映射/'
    scope_path = base + '大纲范围/json/syllabus_scope_v0.json'
    scopes = tracked(scope_path)
    scope_ids = unique(scopes, 'scope_id')
    for r in scopes:
        if r['parent_scope'] is not None and r['parent_scope'] not in scope_ids:
            raise ValueError('Dangling parent scope: ' + r['scope_id'])
    courses, all_sections, all_batches = [], set(), set()
    for key, name, area, track in COURSES:
        mp = base + f'教材章节映射/json/textbook_scope_mapping_{key}_v0.json'
        bp = base + f'正文抽取批次/json/extraction_batches_{key}_v0.json'
        sections, batches = tracked(mp), tracked(bp)
        sm = unique(sections, 'textbook_section_id')
        bm = unique(batches, 'batch_id')
        if all_sections & sm.keys() or all_batches & bm.keys():
            raise ValueError('Cross-course section/batch ID collision')
        all_sections.update(sm); all_batches.update(bm)
        sb = defaultdict(list)
        for batch in batches:
            if set(batch['included_sections']) - sm.keys():
                raise ValueError('Dangling batch section: ' + batch['batch_id'])
            if set(batch['relevant_scope_ids']) - scope_ids.keys():
                raise ValueError('Dangling batch scope: ' + batch['batch_id'])
            for section in batch['included_sections']:
                sb[section].append(batch['batch_id'])
        for section in sections:
            if set(section['mapped_scope_ids']) - scope_ids.keys():
                raise ValueError('Dangling mapped scope: ' + section['textbook_section_id'])
        lecture_dir = '讲义/' + name
        if not inside(project, lecture_dir).is_dir():
            raise ValueError('Missing primary lecture directory: ' + lecture_dir)
        courses.append({'course_key': key, 'course_name': name, 'exam_track': track,
                        'subject_area': area, 'lecture_directory': lecture_dir,
                        'scope_source': scope_path, 'mapping_source': mp, 'batch_source': bp,
                        'scopes': [r for r in scopes if r['subject_area'] == area],
                        'sections': [{**r, 'batch_ids': sb[r['textbook_section_id']]} for r in sections],
                        'batches': batches,
                        'unbatched_sections': [r['textbook_section_id'] for r in sections if not sb[r['textbook_section_id']]]})

    attempt_text = tracked(ATTEMPTS, 'text')
    attempts = jsonl(attempt_text)
    # Structural and semantic validation remains the existing attempt validator's job.
    # This read-only build never claims that counting records certifies a learner.
    summary_log = inside(project, OFFLINE_LOG)
    summaries = jsonl(tracked(OFFLINE_LOG, 'text')) if summary_log.exists() else []
    if summary_log.exists():
        errors = validate_summaries(summaries, schema_runtime(project))
        if errors:
            raise ValueError('; '.join(errors))
        inputs[OFFLINE_SCHEMA] = sha(project / OFFLINE_SCHEMA)
    status = {
        'version': VERSION,
        'question_count': len(questions), 'core_question_count': sum(len(rs) for rs in core.values()),
        'core_paper_count': len(papers), 'source_counts': dict(source_counts),
        'human_issue_question_count': len(pending),
        'human_issue_questions_by_track': dict(Counter(r['exam_track'] for r in pending)),
        'teacher_semantically_exposed_question_count': len(exposure),
        'human_signoff_inferred': False, 'student_seen_status': 'unknown_current',
        'scope_count': len(scopes), 'section_count': len(all_sections), 'batch_count': len(all_batches),
        'unbatched_section_count': sum(len(c['unbatched_sections']) for c in courses),
        'attempt_record_count': len(attempts), 'offline_summary_count': len(summaries),
        'learner_state': None, 'current_frontier': None, 'review_queue': None,
        'learner_status': 'awaiting_feedback' if not attempts and not summaries else 'feedback_requires_audited_derivation',
        'formal_E': {'status': 'not_established', 'qualified_years': None,
                     'F': None, 'C': None, 'V': None,
                     'fallback': 'course_coverage_and_primary_textbook_order',
                     'requires_all_L3_verified': False},
        'extra_background_API': 'paused_numeric_budget_unknown',
        'independent_measurement': 'not_activated',
        'batch_execution_count_this_build': 0,
    }
    return {
        'question_catalog.json': {'version': VERSION, 'records': questions},
        'course_navigation.json': {'version': VERSION, 'ordering': 'existing_metadata_order_not_hard_prerequisite_or_frontier', 'courses': courses},
        'paper_readiness.json': {'version': VERSION, 'papers': papers},
        'teacher_exposure.json': {'version': VERSION, 'basis': 'existing_local_field_evidence_only', 'records': exposure},
        'pending_human_issues.json': {'version': VERSION, 'records': pending},
        'readiness.json': status,
        'source_manifest.json': {'version': VERSION, 'sha256': inputs},
    }


def navigation_markdown(data):
    lines = ['# 七门课按需导航', '',
             '按现有教材映射顺序列出；不是个人学习前沿，也不代表硬前置关系。范围外候选保留说明，未自动加入抽取批次。', '']
    for c in data['courses']:
        lines += [f"## {c['course_name']}", '',
                  f"主教材：`{c['lecture_directory']}`；{len(c['scopes'])} 个 Scope，{len(c['sections'])} 个章节条目，{len(c['batches'])} 个按需批次。", '',
                  '| 章节 | 范围状态 | Scope | 批次 |', '|---|---|---|---|']
        for s in c['sections']:
            values = [s['textbook_section_path'], s['scope_status'],
                      ', '.join(s['mapped_scope_ids']) or '未映射', ', '.join(s['batch_ids']) or '无既有批次']
            lines.append('| ' + ' | '.join(v.replace('|', '\\|').replace('\n', ' ') for v in values) + ' |')
        lines.append('')
    return '\n'.join(lines) + '\n'


def write_build(project, output, policy):
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be empty; use a new snapshot directory')
    artifacts = build(project, policy)
    output.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        (output / name).write_text(dump(content), encoding='utf-8')
    (output / '七门课按需导航.md').write_text(navigation_markdown(artifacts['course_navigation.json']), encoding='utf-8')
    manifest = {'version': VERSION, 'policy_sha256': hashlib.sha256(dump(policy).encode()).hexdigest(),
                'output_sha256': {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output / 'output_manifest.json').write_text(dump(manifest), encoding='utf-8')
    return artifacts['readiness.json']


def check_build(project, output, policy):
    manifest = read(output / 'output_manifest.json')
    errors = []
    if manifest['policy_sha256'] != hashlib.sha256(dump(policy).encode()).hexdigest():
        errors.append('policy_changed')
    for name, expected in manifest['output_sha256'].items():
        p = inside(output, name)
        if not p.is_file() or sha(p) != expected:
            errors.append('output_changed: ' + name)
    sources = read(output / 'source_manifest.json')['sha256']
    for path, expected in sources.items():
        p = inside(project, path)
        if not p.is_file() or sha(p) != expected:
            errors.append('source_changed: ' + path)
    return {'status': 'FAIL' if errors else 'PASS', 'source_file_count': len(sources),
            'output_file_count': len(manifest['output_sha256']), 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('build', 'check'):
        sp = sub.add_parser(command); sp.add_argument('--output', type=Path, required=True)
    nav = sub.add_parser('navigate')
    nav.add_argument('--snapshot', type=Path, required=True)
    nav.add_argument('--course', choices=[c[0] for c in COURSES], required=True)
    nav.add_argument('--scope'); nav.add_argument('--batch')
    budget = sub.add_parser('budget-check'); budget.add_argument('--input', type=Path)
    offline = sub.add_parser('offline-check'); offline.add_argument('--input', type=Path, required=True)
    append = sub.add_parser('offline-append'); append.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    try:
        policy = read(project / POLICY)
        if args.command == 'build':
            result = write_build(project, args.output, policy)
        elif args.command == 'check':
            result = check_build(project, args.output, policy)
        elif args.command == 'navigate':
            result = check_build(project, args.snapshot, policy)
            if result['status'] != 'PASS':
                raise ValueError('Snapshot stale or damaged; rebuild before navigation')
            data = read(args.snapshot / 'course_navigation.json')
            course = next(c for c in data['courses'] if c['course_key'] == args.course)
            if args.scope and args.scope not in {s['scope_id'] for s in course['scopes']}:
                raise ValueError('Unknown scope for selected course')
            if args.batch and args.batch not in {b['batch_id'] for b in course['batches']}:
                raise ValueError('Unknown batch for selected course')
            result = dict(course)
            result['sections'] = [s for s in course['sections'] if
                (not args.scope or args.scope in s['mapped_scope_ids']) and
                (not args.batch or args.batch in s['batch_ids'])]
            section_ids = {s['textbook_section_id'] for s in result['sections']}
            result['batches'] = [b for b in course['batches'] if
                (not args.batch or b['batch_id'] == args.batch) and
                (not args.scope or args.scope in b['relevant_scope_ids'] or section_ids.intersection(b['included_sections']))]
        elif args.command == 'budget-check':
            request = read(args.input) if args.input else policy['api_budget_default']
            result = budget_preflight(request)
        elif args.command == 'offline-check':
            errors = validate_summary(read(args.input), schema_runtime(project))
            result = {'status': 'FAIL' if errors else 'PASS', 'errors': errors,
                      'independent_measurement_activated': False}
        else:
            result = append_summary(project / OFFLINE_LOG, read(args.input), schema_runtime(project))
        print(dump(result), end='')
        return int(result.get('status') == 'FAIL' or result.get('allowed') is False)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(dump({'status': 'FAIL', 'error': str(error)}), end='')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
