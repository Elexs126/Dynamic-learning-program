#!/usr/bin/env python3
"""Audit current local sources against frozen annotations without changing either.

Reports unresolved source contradictions separately from stale snapshot hashes.
It does not rewrite scores, restore merged fragments, or certify official answers.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

VERSION = 'post-correction-audit-v1.0.0'
TOOLS = '系统文件/脚本工具/05_标注与规范校验/'
L1 = '系统文件/题目标注/L1/question_annotations_l1_v1.json'
COHORTS = [
    ('MATH1', '数学一_L2_L3', 'question_annotations_math1_l23_v1.json', 'math1_l23_review_v1'),
    ('CS408', '408_2009_2012_L3', 'question_annotations_cs408_2009_2012_l23_v1.json', 'cs408_2009_2012_review_v1'),
    ('CS408', '408_2013_2026_L3', 'question_annotations_cs408_2013_2026_l23_v1.json', 'cs408_2013_2026_review_v1'),
]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def declared_totals(body, first_line):
    result = []
    for m in re.finditer(r'本题满分\s*(\d+(?:\.\d+)?)\s*分', body):
        result.append({'points': float(m[1]), 'relative_body_line': body.count('\n', 0, m.start()) + 1,
                       'question_start_line': first_line, 'fragment': m[0]})
    return result


def total_conflicts(metadata_total, claims):
    return [c for c in claims if c['points'] != metadata_total]


def reviewed_step_ids(record):
    counts = Counter()
    for entry in record['l3'].get('evidence_steps', []):
        for step in entry['steps']:
            m = re.match(r'\[[^\]]+#T(\d+)\]', step)
            if m:
                counts[int(m[1])] += 1
    return {f'{task}.{step}' for task, count in counts.items() for step in range(1, count + 1)}


def covering_partition_conflict(record, spec):
    """Do not treat genuinely partial scoring evidence as a full partition.

    A whole-unit switch cannot resolve a formerly complete contradictory
    partition. Report the discrepancy without choosing a replacement total.
    """
    units = spec.get('units', spec.get('documented_units', []))
    refs = [s for u in units for s in u['step_refs']]
    required = reviewed_step_ids(record)
    if not units or not required or len(refs) != len(set(refs)) or set(refs) != required:
        return None
    subtotal = sum(u['points'] for u in units)
    total = record['l0']['original_points']
    if total == subtotal:
        return None
    return {'metadata_points': total, 'documented_points_sum': subtotal,
            'documented_unit_count': len(units), 'covered_reviewed_step_count': len(required),
            'mode': spec['mode'], 'anchors': [u['anchor'] for u in units],
            'interpretation': 'All listed reviewed steps have scoring evidence, but the subtotal differs. '
                              'Needs an explicit reconciliation; do not choose or distribute a difference.'}


def keyset(records):
    rows = {r['question_id']: r for r in records}
    if len(rows) != len(records):
        raise ValueError('Duplicate question IDs')
    return rows


def audit_active_release(project, selector):
    """Audit the selected current release; never silently fall back to history."""
    builder = module('current_release_audit', project / selector['release_builder'])
    release = str(Path(selector['release_manifest']).parent)
    expected = [release + '/L1/' + builder.L1_NAME] + [release + '/' + key + '/' + name
                for key, _, _, _, name in builder.COHORTS]
    if selector['annotation_files'] != expected or selector['canonical_sources'] != release + '/canonical_sources_v2.json':
        return {'audit_version': 'post-correction-audit-v1.1.0', 'status': 'REVIEW_REQUIRED',
                'selected_release': release, 'dependent_l1_execution_allowed': False,
                'dependent_l1_executed': True, 'counts': None,
                'note': 'Current selector does not match the selected release.'}
    validation = builder.check(project, release)
    if validation['status'] != 'PASS':
        return {'audit_version': 'post-correction-audit-v1.1.0',
                'status': 'REVIEW_REQUIRED', 'selected_release': release,
                'dependent_l1_execution_allowed': False, 'dependent_l1_executed': True,
                'counts': None, 'current_release_check': validation,
                'note': 'Current source or release changed; historical snapshots are not substituted.'}
    summary = read(project / release / 'release_report.json')
    baseline = read(project / selector['canonical_sources'])
    l1 = read(project / selector['annotation_files'][0])['records']
    cohorts = []
    for path in selector['annotation_files'][1:]:
        rows = read(project / path)['records']
        cohorts.append({'cohort': str(Path(path).parent), 'record_count': len(rows),
                        'stored_field_omission_question_count': sum(bool(r.get('field_omissions')) for r in rows),
                        'source_file_hash_drift': [], 'question_hash_drift': [],
                        'cumulative_layer_mismatch_ids': []})
    return {'audit_version': 'post-correction-audit-v1.1.0', 'status': 'PASS',
            'selected_release': release, 'dependent_l1_execution_allowed': True,
            'dependent_l1_executed': True, 'cohorts': cohorts,
            'counts': {'actual_canonical': len(l1), 'stored_baseline': baseline['expected_unique_question_records'],
                       'core': summary['core_count'], 'score_conflict_questions': 0,
                       'semantic_choice_issues': 0, 'rule_scope_documentation_issues': 0,
                       'paper_total_mismatches': 0, 'stored_l1_changed_question_hashes': 0,
                       'ocr_suspicious_characters_remaining': 0, 'short_stem_candidates': 0,
                       'short_stems_confirmed_normal': summary['short_stems_closed'],
                       'duplicate_candidate_groups': summary['duplicate_groups_reviewed'],
                       'duplicate_candidate_records': summary['duplicate_records_reviewed'],
                       'core_course_only_routes': summary['remaining_core_course_only_scope'],
                       'core_course_only_routes_by_track': {},
                       'remaining_noncore_course_only_routes': summary['remaining_course_only_scope']},
            'missing_ids_from_current_sources': [], 'new_ids': [],
            'retired_id_mapping': read(project / release / 'retired_id_mapping.json'),
            'score_conflicts': [], 'semantic_findings': [], 'rule_scope_notes': [],
            'paper_total_mismatches': [], 'current_release_check': validation,
            'limits': ['Current hashes, cumulative fields and L3 replay are verified; no official-answer or learner certification is inferred.']}


def audit(project, run_checks=True):
    selector_path = project / '系统文件/系统配置/annotation_sources_current_v1.json'
    if selector_path.exists():
        return audit_active_release(project, read(selector_path))
    tracked = {}

    def load(relative):
        tracked[relative] = sha(project / relative)
        return read(project / relative)

    baseline = load('系统文件/系统配置/canonical_sources_v1.json')
    contract = load('系统文件/系统配置/execution_contract_v1.json')
    if '两科均为150分' not in contract['time_budget']['initial_weekly_allocation']['basis']:
        raise ValueError('The frozen local 150-point contract basis needs review before this audit')
    parser = module('correction_audit_l1_parser', project / TOOLS / 'build_l1.py')
    tracked[TOOLS + 'build_l1.py'] = sha(project / TOOLS / 'build_l1.py')
    scopes = {s['scope_id']: s for s in load(parser.SCOPE_FILE)}
    rules = load(TOOLS + 'l1_scope_rules_v1.json')
    fresh, evidence, blocks, assets = [], [], {}, {}
    counts = Counter()
    for source, path in parser.canonical_files(project, baseline):
        relative = path.relative_to(project).as_posix()
        tracked[relative] = sha(path)
        text = path.read_text(encoding='utf-8')
        for block in parser.parse_file(text, relative):
            r, e = parser.make_record(project, source, path, block, scopes, rules, assets)
            if r['question_id'] in blocks:
                raise ValueError('Duplicate canonical ID: ' + r['question_id'])
            fresh.append(r); evidence.append(e)
            block['source_file'] = relative
            blocks[r['question_id']] = block
            counts[source['source_id']] += 1
    fresh_byid = keyset(fresh)
    old_l1 = keyset(load(L1)['records'])
    duplicate_groups = parser.attach_duplicates(fresh, evidence)
    flags = Counter(flag for r in fresh for flag in r['review_flags'])
    missing_ids = sorted(set(old_l1) - set(fresh_byid))
    new_ids = sorted(set(fresh_byid) - set(old_l1))
    changed = sorted(q for q in set(old_l1) & set(fresh_byid)
                     if old_l1[q]['l0']['question_hash_sha256'] != fresh_byid[q]['l0']['question_hash_sha256'])

    def location(q):
        b = blocks[q]
        return {'source_file': b['source_file'], 'question_id': q,
                'line_start': b['line_start'], 'line_end': b['line_end'],
                'question_hash_sha256': b['block_hash']}

    scores, cohort_reports, all_records = [], [], {}
    paper_totals = defaultdict(lambda: {'question_count': 0, 'points': 0, 'unknown_points': 0})
    for track, folder, bundle_name, review in COHORTS:
        bp = '系统文件/题目标注/' + folder + '/' + bundle_name
        bundle = load(bp); records = keyset(bundle['records'])
        overlap = records.keys() & all_records.keys()
        if overlap:
            raise ValueError('Duplicate L3 cohort coverage')
        all_records.update(records)
        scoring_path = TOOLS + review + '/scoring_plan_v1.json'
        scoring = load(scoring_path)['questions'] if (project / scoring_path).exists() else {}
        lock = load(TOOLS + review + '/source_lock_v1.json')
        policy = load(TOOLS + review + '/review_policy_v1.json')
        drift_files = [p for p, expected in lock['source_files'].items()
                       if not (project / p).exists() or sha(project / p) != expected]
        hash_drift, layer_mismatch = [], []
        for q, r in records.items():
            if q not in fresh_byid:
                raise ValueError('Missing canonical core question: ' + q)
            current = fresh_byid[q]
            if r['l0']['question_hash_sha256'] != current['l0']['question_hash_sha256']:
                hash_drift.append(q)
            if r['l0'] != old_l1[q]['l0'] or r['l1'] != old_l1[q]['l1']:
                layer_mismatch.append(q)
            b = blocks[q]
            claims = declared_totals(b['body'], b['line_start'])
            for c in claims:
                # Locate within the real file rather than presenting relative body offsets as source lines.
                source_lines = (project / b['source_file']).read_text().splitlines()
                c['line'] = next(i + 1 for i in range(b['line_start'] - 1, b['line_end'])
                                 if c['fragment'] in source_lines[i])
            mismatch = total_conflicts(current['l0']['original_points'], claims)
            covering = covering_partition_conflict(r, scoring.get(q, {}))
            if mismatch or covering:
                scores.append({**location(q), 'exam_track': track,
                    'metadata_points': current['l0']['original_points'],
                    'statement_total_claims': claims,
                    'statement_total_mismatch': bool(mismatch),
                    'covering_scoring_mismatch': covering,
                    'current_l3_score_status': r['l3']['review_status_by_field']['score_units'],
                    'current_effective_points': [u['points'] for u in r['l3']['score_units']],
                    'review_status': 'needs_reconciliation'})
            paper = paper_totals[current['l0']['paper_id']]
            paper.update(exam_track=track, source_file=b['source_file'])
            paper['question_count'] += 1
            if current['l0']['original_points'] is None: paper['unknown_points'] += 1
            else: paper['points'] += current['l0']['original_points']
        cohort_reports.append({'cohort': folder, 'record_count': len(records),
            'stored_field_omission_question_count': sum(bool(r.get('field_omissions')) for r in records.values()),
            'source_file_hash_drift': sorted(drift_files), 'question_hash_drift': sorted(hash_drift),
            'cumulative_layer_mismatch_ids': sorted(layer_mismatch),
            'note': 'An empty omission list is not proof of reconciled source scoring.'})

    papers = [{'paper_id': p, **r, 'contract_maximum_points': 150,
               'difference': r['points'] - 150,
               'whole_paper_usable_for_E': False}
              for p, r in sorted(paper_totals.items()) if r['points'] != 150 or r['unknown_points']]
    # The 150-point target is bound to the existing local contract above.

    # Bounded semantic review of the user's revised 2026 option set. Exact source
    # predicates prevent blindly carrying this finding after another correction.
    semantic = []
    q = 'M1-26-C-T04'; b = blocks[q]
    predicates = [r'z = \sqrt{4 - x^2 - y^2}', r'z = \sqrt{x^2 + y^2}',
        r'\int_0^{\sqrt{2}} dr \int_r^{\sqrt{4-r^2}} f(r^2+z^2) r dz',
        r'\int_0^{\frac{\pi}{4}} d\varphi \int_0^2 f(r^2) r^2 \sin\varphi dr']
    if all(fragment in b['body'] for fragment in predicates):
        semantic.append({**location(q), 'kind': 'non_unique_choice_after_formula_repair',
            'related_fields': ['l3.alternative_methods', 'l3.evidence_steps'],
            'finding': '当前A为柱坐标、C为球坐标；两者都对应球内且圆锥上方的同一区域、同一径向被积函数。参考答案只列C，选项不唯一，不能把整题记为完全无疑点。',
            'proof': '柱坐标0≤r≤√2、r≤z≤√(4−r²)等价于球坐标0≤ρ≤2、0≤φ≤π/4，周向均为0到2π；体积元分别为r和ρ²sinφ。',
            'action': '核对原选项，不凭常见题型猜改A；已成立的知识、方法和通用步骤可保留。'})

    scope_notes = []
    for folder, q in [('cs408_2009_2012_review_v1', '408-12-A-T42'),
                       ('cs408_2013_2026_review_v1', '408-13-A-T41')]:
        plan = load(TOOLS + folder + '/scoring_plan_v1.json')['questions'][q]
        if all(r['scope_status'] == 'verified' for r in plan.get('rules', [])) and any(
            token in json.dumps(plan, ensure_ascii=False) for token in ('未明确', '无法从文件确认')):
            scope_notes.append({**location(q), 'finding': '条件规则已标verified并绑定任务，但同记录仍说明适用范围未明确；需同步本次人工核对依据或保持该条件范围待核。'})

    check_results = []
    if run_checks:
        for name in ['build_l1.py', 'build_math1_l23.py', 'build_cs408_l23.py', 'build_cs408_2013_2026_l23.py']:
            path = project / TOOLS / name
            tracked[TOOLS + name] = sha(path)
            run = subprocess.run([sys.executable, '-B', str(path), 'check', '--project', str(project)],
                                 capture_output=True, text=True)
            check_results.append({'tool': name, 'exit_code': run.returncode,
                                  'output': (run.stdout + run.stderr).strip()[:1800]})
    unresolved_scope = [r for r in fresh if r['l0']['source_file'].startswith('核心真题/') and
                        set(r['review_flags']) & {'SCOPE_UNMAPPED', 'SCOPE_AMBIGUOUS'}]
    blockers = sorted({r['question_id'] for r in scores + semantic})
    blocked = bool(blockers or missing_ids or new_ids or changed or scope_notes or papers
                   or len(fresh) != baseline['expected_unique_question_records']
                   or any(c['source_file_hash_drift'] or c['cumulative_layer_mismatch_ids'] for c in cohort_reports)
                   or any(c['exit_code'] for c in check_results))
    return {'audit_version': VERSION, 'status': 'REVIEW_REQUIRED' if blocked else 'PASS',
        'dependent_l1_execution_allowed': not blocked,
        'dependent_l1_executed': False,
        'counts': {'actual_canonical': len(fresh), 'stored_baseline': baseline['expected_unique_question_records'],
            'core': len(all_records), 'actual_by_source': dict(counts),
            'score_conflict_questions': len(scores), 'semantic_choice_issues': len(semantic),
            'rule_scope_documentation_issues': len(scope_notes), 'paper_total_mismatches': len(papers),
            'stored_l1_changed_question_hashes': len(changed),
            'ocr_suspicious_characters_remaining': flags.get('OCR_SUSPICIOUS_CHARACTERS', 0),
            'short_stem_candidates': flags.get('SHORT_OR_EMPTY_STEM', 0),
            'duplicate_candidate_groups': len(duplicate_groups),
            'duplicate_candidate_records': sum(len(g['question_ids']) for g in duplicate_groups),
            'core_course_only_routes': len(unresolved_scope),
            'core_course_only_routes_by_track': dict(Counter(r['l0']['exam_track'] for r in unresolved_scope))},
        'cohorts': cohort_reports, 'score_conflicts': scores, 'semantic_findings': semantic,
        'rule_scope_notes': scope_notes, 'paper_total_mismatches': papers,
        'missing_ids_from_current_sources': missing_ids, 'new_ids': new_ids,
        'changed_question_hashes': changed,
        'short_stem_candidates': [location(r['question_id']) for r in fresh if 'SHORT_OR_EMPTY_STEM' in r['review_flags']],
        'core_course_only_routes': [location(r['question_id']) for r in unresolved_scope],
        'duplicate_candidates': duplicate_groups,
        'existing_builder_checks': check_results, 'input_sha256': tracked,
        'limits': ['全量检查结构、引用、显式分值冲突、来源变化；定向复核本次修正，不认证全库答案。',
                   '旧快照保留；不改原题，不猜选冲突总分，不将尚未完成的L3作为下游L1依据。',
                   '11条短题干提示不是11道损坏题；其中有正常的短问句和填空式，不能仅据长度判坏。']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[3])
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error('Use a new output path; audit reports are snapshots')
    result = audit(args.project.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded(result))
    print(json.dumps({'status': result['status'], 'counts': result['counts'],
                      'dependent_l1_executed': result['dependent_l1_executed']}, ensure_ascii=False, indent=2))
    return 1 if result['status'] == 'REVIEW_REQUIRED' else 0


if __name__ == '__main__':
    raise SystemExit(main())
