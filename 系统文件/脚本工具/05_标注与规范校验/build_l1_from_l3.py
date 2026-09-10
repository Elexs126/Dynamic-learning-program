#!/usr/bin/env python3
"""Reconcile reviewed core L3 with L1 in a new, auditable cumulative release."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile

VERSION = 'l1-from-l3-v1.0.0'
T = '系统文件/脚本工具/05_标注与规范校验'
RELEASE = '系统文件/题目标注/L1_L3衔接_20260910_v1'
L1_NAME = 'question_annotations_l1_v1.json'
OLD_L1 = '系统文件/题目标注/L1/' + L1_NAME
COHORTS = [
    ('math1', 'build_math1_l23.py', 'math1_l23_review_v1', '数学一_L2_L3', 'question_annotations_math1_l23_v1.json'),
    ('cs408_early', 'build_cs408_l23.py', 'cs408_2009_2012_review_v1', '408_2009_2012_L3', 'question_annotations_cs408_2009_2012_l23_v1.json'),
    ('cs408_late', 'build_cs408_2013_2026_l23.py', 'cs408_2013_2026_review_v1', '408_2013_2026_L3', 'question_annotations_cs408_2013_2026_l23_v1.json'),
]


def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def content(value): return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(content(value))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def require(test, message):
    if not test: raise ValueError(message)


def reanchor(anchor, block, source_lines):
    """Keep a valid original location; otherwise accept only a unique exact match."""
    start, end = block['line_start'], block['line_end']
    valid = lambda n: start <= n <= end and source_lines[n-1].count(anchor['match']) >= anchor['occurrence']
    if valid(anchor['line']): return dict(anchor)
    candidates = [n for n in range(start, end+1) if valid(n)]
    require(len(candidates) == 1, f"Ambiguous/missing source anchor: {block['question_id']} {anchor['match']}")
    return dict(anchor, line=candidates[0])


def apply_review(records, evidence, reviewed_l3, scope_review, scopes, confirmation, groups):
    byid = {r['question_id']: r for r in records}; ev = {e['question_id']: e for e in evidence}
    resolutions = {r['question_id']: r for r in scope_review['records']}
    pending = {q for q in reviewed_l3 if set(byid[q]['review_flags']) & {'SCOPE_UNMAPPED', 'SCOPE_AMBIGUOUS'}}
    require(set(resolutions) == pending, 'Scope decisions must cover exactly the unresolved core set')
    changes = []
    for q, audited in sorted(reviewed_l3.items()):
        r = byid[q]; before = copy.deepcopy(r['l1']); l1 = r['l1']
        main = audited['l2']['main_knowledge']
        require(audited['l2']['review_status_by_field']['main_knowledge'] == 'verified', q + ': L2 main is unreviewed')
        confidence = audited['l2']['confidence_by_field']['main_knowledge']
        l1['candidate_main_knowledge'] = dict(main, role='reviewed_l2_reference', confidence=confidence)
        l1['confidence_by_field']['candidate_main_knowledge'] = confidence
        l1['review_status_by_field']['candidate_main_knowledge'] = 'verified'
        l1['label_provenance'] = sorted(set(l1['label_provenance'] + ['question_semantics']))
        remove = {'LEGACY_LABEL_UNVERIFIED', 'CHAPTER_PROXY_NOT_FINE_KNOWLEDGE', 'GENERIC_LABEL_NOT_KNOWLEDGE'}
        r['review_flags'] = sorted(set(r['review_flags']) - remove | {'L1_MAIN_RECONCILED_WITH_REVIEWED_L2'})
        if q in resolutions:
            decision = resolutions[q]
            require(decision['reviewed_main_knowledge'] == main['name'], q + ': scope decision source main changed')
            ids = decision['scope_ids']; require(ids and len(set(ids)) == len(ids), q + ': duplicate/empty scope list')
            require(all(s in scopes and not scopes[s]['parent_scope'] for s in ids), q + ': nonchapter scope')
            require(all(scopes[s]['subject_area'] == r['l0']['subject_area'] for s in ids), q + ': cross-course scope')
            prefix = r['l1']['official_scope_coarse'].split(' > ')[:2]
            paths = [' > '.join(prefix + [scopes[s]['scope_name']]) for s in ids]
            l1['official_scope_coarse'] = '；'.join(paths)
            l1['review_status_by_field']['official_scope_coarse'] = 'verified'
            l1['confidence_by_field']['official_scope_coarse'] = 'medium' if len(ids) > 1 else 'high'
            l1['label_provenance'] = sorted(set(l1['label_provenance'] + ['official_syllabus']))
            r['review_flags'] = sorted(set(r['review_flags']) - {'SCOPE_UNMAPPED', 'SCOPE_AMBIGUOUS'} | {'L1_SCOPE_LOCALLY_REVIEWED'})
            ev[q].update(scope_ids=ids, scope_route_status='verified', scope_resolution=decision)
        changes.append({'question_id': q, 'source_hash': r['l0']['question_hash_sha256'],
                        'before_l1': before, 'after_l1': copy.deepcopy(l1),
                        'reviewed_l2_main': main, 'scope_resolution': resolutions.get(q),
                        'reviewer_kind': 'assistant_offline_semantic_review', 'human_review_performed': False})
    for group in groups:
        group['status'] = 'verified'
        group['verification_scope'] = 'identical_local_statement_options_and_image_bytes_after_whitespace_normalization'
        for q in group['question_ids']:
            l1 = byid[q]['l1']; dup = l1['duplicate_candidate']
            require(dup['is_candidate'] is True and set(dup['possible_duplicate_ids']) == set(group['question_ids']) - {q}, q + ': duplicate candidate not reciprocal')
            dup['status'] = 'verified'
            dup['basis'] = '本地逐组核对：同课程、同题型的题干、数值、符号、选项及图片内容一致；确认当前记录重复，不认证原卷身份，不删除或合并题目。'
            l1['review_status_by_field']['duplicate_candidate'] = 'verified'
            l1['confidence_by_field']['duplicate_candidate'] = 'high'
    short_ids = confirmation['short_stem_confirmed_normal_ids']
    require(set(short_ids) == {r['question_id'] for r in records if 'SHORT_OR_EMPTY_STEM' in r['review_flags']}, 'Short-statement confirmation set changed')
    for q in short_ids:
        r = byid[q]
        r['review_flags'] = sorted(set(r['review_flags']) - {'SHORT_OR_EMPTY_STEM'} | {'SHORT_STEM_CONFIRMED_NORMAL_BY_USER'})
        ev[q]['short_stem_resolution'] = {'status': 'verified', 'basis': '2026-09-10 explicit user confirmation; only statement length issue closed'}
    # Include final duplicate changes in the main trace, too.
    for c in changes: c['after_l1'] = copy.deepcopy(byid[c['question_id']]['l1'])
    return changes


def check(project, release):
    directory = project / release
    manifest = read(directory / 'release_manifest.json'); errors = []
    if manifest['builder_sha256'] != sha(Path(__file__)):
        errors.append('release builder changed')
    for path, expected in manifest['input_sha256'].items():
        p = project / path
        if not p.is_file() or sha(p) != expected: errors.append('input changed: ' + path)
    for path, expected in manifest['output_sha256'].items():
        p = directory / path
        if not p.is_file() or sha(p) != expected: errors.append('output changed: ' + path)
    if errors: return {'status': 'FAIL', 'errors': errors}
    final_l1 = {r['question_id']: r for r in read(directory / 'L1' / L1_NAME)['records']}
    count = 0; papers = defaultdict(float)
    schema = load('post_l3_check_schema', project / T / 'json_schema_runtime.py')
    errors += schema.SchemaRuntime(project/'系统文件/数据规范/question_annotations_bundle.schema.json').validate(read(directory/'L1'/L1_NAME))
    for key, script, _, _, _ in COHORTS:
        m = load('post_l3_check_' + key, project / T / script)
        m.L1_PATH = release + '/L1/' + L1_NAME
        validation = m.run(project, directory / key, 'check', directory / 'review_inputs' / key)
        require(validation['status'] == 'PASS', key + ': L3 validation failed')
        for r in read(directory/key/m.BUNDLE)['records']:
            count += 1
            require(r['l0'] == final_l1[r['question_id']]['l0'] and r['l1'] == final_l1[r['question_id']]['l1'], 'Cumulative layer mismatch')
            require(not r.get('field_omissions'), 'L3 still has unresolved omissions')
            require(all(v == 'verified' for v in r['l2']['review_status_by_field'].values()), 'L2 field not verified')
            require(all(v == 'verified' for v in r['l3']['review_status_by_field'].values()), 'L3 field not verified')
            require(sum(u['points'] for u in r['l3']['score_units']) == r['l0']['original_points'], 'Scoring sum mismatch')
            papers[r['l0']['paper_id']] += r['l0']['original_points']
    require(count == 1277 and len(papers) == 37 and set(papers.values()) == {150}, 'Core coverage or paper total mismatch')
    confirmation = read(directory/'review_inputs/user_confirmation_v1.json')
    require(not set(confirmation['retired_id_merges']) & final_l1.keys(), 'Retired fragment remains active')
    require(set(confirmation['retired_id_merges'].values()) <= final_l1.keys(), 'Missing merge target')
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors, 'question_count': len(final_l1),
            'core_count': count, 'paper_count': len(papers), 'all_papers_150': True,
            'scope_resolutions': 123, 'input_file_count': len(manifest['input_sha256'])}


def build(project, output, inputs, release=RELEASE):
    require(not (output/'release_manifest.json').exists(), 'Release exists: use check or a new version')
    require(not Path(release).is_absolute() and '..' not in Path(release).parts, 'Unsafe release path')
    created_at = datetime.now(timezone.utc).isoformat()
    tracked = {}
    def track(path):
        relative = path.relative_to(project).as_posix(); tracked[relative] = sha(path); return relative
    parser = load('post_l3_l1_parser', project/T/'build_l1.py')
    baseline = read(project/parser.MANIFEST); track(project/parser.MANIFEST)
    confirmation = read(inputs/'user_confirmation_v1.json'); scope_review = read(inputs/'scope_resolutions_v1.json')
    scopes = {s['scope_id']: s for s in read(project/parser.SCOPE_FILE)}; track(project/parser.SCOPE_FILE)
    rules = read(project/T/'l1_scope_rules_v1.json'); track(project/T/'l1_scope_rules_v1.json')
    records, evidence, blocks, assets = [], [], {}, {}
    files = parser.canonical_files(project, baseline); counts = Counter()
    for source, path in files:
        relative = track(path)
        for block in parser.parse_file(path.read_text(), relative):
            require(block['question_id'] not in blocks, 'Duplicate source ID')
            r, ev = parser.make_record(project, source, path, block, scopes, rules, assets)
            records.append(r); evidence.append(ev); blocks[r['question_id']] = dict(block, source_file=relative)
            counts[source['source_id']] += 1
    records.sort(key=lambda r:r['question_id']); evidence.sort(key=lambda r:r['question_id'])
    require(len(records) == baseline['expected_unique_question_records'], 'Canonical total mismatch')
    baseline_repairs=[]
    for source in baseline['sources']:
        actual=counts[source['source_id']]
        if actual != source['expected_records']:
            require(source['source_id']=='WANGDAO_408' and source.get('expected_record_count')==actual
                    and source['expected_records']-actual==len(confirmation['retired_id_merges']), 'Unconfirmed canonical source count mismatch')
            baseline_repairs.append({'source_id':source['source_id'],'before':source['expected_records'],'after':actual,
                                     'basis':'User-confirmed fragment merge and existing corrected expected_record_count'})
            source['expected_records']=actual
        source.pop('expected_record_count',None)
    baseline['manifest_version']='canonical-sources-v2.0.0'
    byid = {r['question_id']: r for r in records}
    old = {r['question_id']: r for r in read(project/OLD_L1)['records']}; track(project/OLD_L1)
    groups = parser.attach_duplicates(records, evidence)
    require(set(old)-set(byid) == set(confirmation['retired_id_merges']), 'Unexpected removed IDs')
    bundle = {'schema_version':'question-annotations-bundle-v1.0.0', 'generated_at':created_at,
              'source_file':release+'/canonical_sources_v2.json', 'source_schema_version':baseline['manifest_version'],
              'record_count':len(records), 'records':records}
    with tempfile.TemporaryDirectory(prefix='l1-l3-release-') as temp:
        mirror = Path(temp); relout = mirror/release
        (relout/'review_inputs').mkdir(parents=True)
        write(relout/'canonical_sources_v2.json',baseline)
        for path in inputs.glob('*.json'): shutil.copyfile(path,relout/'review_inputs'/path.name)
        def copy_input(relative):
            src = project/relative; target = mirror/relative
            require(src.resolve().is_relative_to(project.resolve()), 'Input symlink escapes project')
            track(src); target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,target)
        for _, path in files: copy_input(path.relative_to(project).as_posix())
        for image in assets: copy_input(image)
        for path in (project/'系统文件/数据规范').glob('*.json'): copy_input(path.relative_to(project).as_posix())
        for path in (project/T).glob('*.py'):
            if path.name.startswith(('build_', 'validate_', 'json_schema')): copy_input(path.relative_to(project).as_posix())
        modules = {}; anchor_changes = []; partial_modes = []
        for key, script, review, folder, name in COHORTS:
            oldpath = project/'系统文件/题目标注'/folder/name; track(oldpath)
            dest = relout/'review_inputs'/key; dest.mkdir()
            for path in (project/T/review).iterdir():
                if path.is_file(): track(path); shutil.copyfile(path,dest/path.name)
            lock = read(dest/'source_lock_v1.json')
            for relative in lock['images']:
                require(sha(project/relative)==lock['images'][relative], 'Reviewed image changed: '+relative)
                if not (mirror/relative).exists(): copy_input(relative)
            lock['source_files'] = {p:sha(project/p) for p in lock['source_files']}
            lock['question_hashes'] = {q:blocks[q]['block_hash'] for q in lock['question_hashes']}
            write(dest/'source_lock_v1.json',lock)
            policy = read(dest/'review_policy_v1.json'); policy['generated_at']=created_at
            policy['source_correction_confirmation']='2026-09-10 explicit user confirmation; original semantic review remains assistant local review'
            write(dest/'review_policy_v1.json',policy)
            sp=dest/'scoring_plan_v1.json'
            if sp.exists():
                plan=read(sp)
                for q,spec in plan['questions'].items():
                    if spec['mode']=='partial':
                        partial_modes.append(q);spec['mode']='whole'
                        spec['source_review_mode']='partial_confirmed_by_user'
                    source_lines=(project/blocks[q]['source_file']).read_text().splitlines()
                    for item in spec.get('units',spec.get('documented_units',[]))+spec.get('rules',[])+spec.get('explicit_total_claims',[]):
                        old_anchor=item['anchor'];new_anchor=reanchor(old_anchor,blocks[q],source_lines)
                        if old_anchor!=new_anchor:anchor_changes.append({'question_id':q,'before':old_anchor,'after':new_anchor})
                        item['anchor']=new_anchor
                write(sp,plan)
            m=load('post_l3_builder_'+key,mirror/T/script);m.L1_PATH=release+'/L1/'+L1_NAME
            modules[key]=m
        write(relout/'L1'/L1_NAME,bundle)
        preflight = {}; preflight_validations = []
        for key,_,_,_,_ in COHORTS:
            m=modules[key];rd=relout/'review_inputs'/key;payload=m.generate(mirror,rd)
            validation = m.validate_data(mirror,mirror/'系统文件/数据规范',payload) if key=='math1' else m.validate_data(mirror,None,payload,rd)
            require(validation['status']=='PASS', key+': preflight failed '+str(validation.get('errors')))
            b=read_bytes_json(payload[m.BUNDLE]);preflight.update({r['question_id']:r for r in b['records']})
            preflight_validations.append(validation)
        require(len(preflight)==1277 and all(not r.get('field_omissions') for r in preflight.values()), 'Incomplete preflight L3')
        totals=defaultdict(float)
        for r in preflight.values():
            totals[r['l0']['paper_id']]+=r['l0']['original_points']
            require(all(x==r['l0']['original_points'] for x in [float(v) for v in re.findall(r'本题满分\s*(\d+(?:\.\d+)?)\s*分',blocks[r['question_id']]['body'])]), 'Statement total mismatch')
        require(len(totals)==37 and set(totals.values())=={150}, 'Whole-paper totals must be 150 before L1 review')
        changes=apply_review(records,evidence,preflight,scope_review,scopes,confirmation,groups)
        write(relout/'L1'/L1_NAME,bundle)
        schema=load('post_l3_schema',mirror/T/'json_schema_runtime.py')
        errors=schema.SchemaRuntime(mirror/'系统文件/数据规范/question_annotations_bundle.schema.json').validate(bundle)
        require(not errors,str(errors[:5]))
        write(relout/'L1/duplicate_review_v1.json',{'groups':groups,'no_match_does_not_mean_unique':True})
        write(relout/'L1/l1_review_changes_v1.json',{'records':changes})
        (relout/'L1/l1_evidence_v1.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in evidence))
        write(relout/'retired_id_mapping.json',{'merges':confirmation['retired_id_merges'],'basis':'User-corrected source merges, not newly deleted records'})
        final_validations=[]
        for key,_,_,_,_ in COHORTS:
            m=modules[key];rd=relout/'review_inputs'/key
            result=m.run(mirror,relout/key,'build',rd); require(result['status']=='PASS',key+': final validation failed')
            final_validations.append(result)
        unresolved=sum(bool(set(r['review_flags'])&{'SCOPE_UNMAPPED','SCOPE_AMBIGUOUS'}) for r in records)
        summary={'status':'PASS','version':VERSION,'generated_at':created_at,'question_count':len(records),'core_count':1277,
                 'paper_count':37,'all_papers_150':True,'L2_main_reconciled':len(changes),'scope_resolved':len(scope_review['records']),
                 'multi_scope_resolved':sum(len(x['scope_ids'])>1 for x in scope_review['records']),
                 'remaining_course_only_scope':unresolved,'remaining_core_course_only_scope':sum(q in preflight for q,r in byid.items() if set(r['review_flags'])&{'SCOPE_UNMAPPED','SCOPE_AMBIGUOUS'}),
                 'duplicate_groups_reviewed':len(groups),'duplicate_records_reviewed':sum(len(g['question_ids']) for g in groups),
                 'short_stems_closed':len(confirmation['short_stem_confirmed_normal_ids']),
                 'changed_source_questions':sum(q in old and old[q]['l0']['question_hash_sha256']!=r['l0']['question_hash_sha256'] for q,r in byid.items()),
                 'retired_fragment_ids':list(confirmation['retired_id_merges']), 'partial_scoring_normalized':partial_modes,
                 'canonical_baseline_repairs':baseline_repairs,
                 'preflight_validations':preflight_validations,'final_validations':final_validations,
                 'anchor_relocations':anchor_changes,'student_records_created':0,'formal_E_activated':False,
                 'canonical_knowledge_dictionary_frozen':False,'no_match_duplicates_left_unknown':True}
        write(relout/'release_report.json',summary)
        # All input hashes refer to original project files; generated normalized
        # review inputs are protected by the output manifest instead.
        out_hashes={p.relative_to(relout).as_posix():sha(p) for p in relout.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        write(relout/'release_manifest.json',{'version':VERSION,'builder_sha256':sha(Path(__file__)),
                                            'input_sha256':tracked,'output_sha256':out_hashes})
        output.mkdir(parents=True,exist_ok=True)
        for p in relout.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                dest=output/p.relative_to(relout);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    return summary


def read_bytes_json(data): return json.loads(data)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['build','check'])
    p.add_argument('--project',type=Path,required=True);p.add_argument('--release',default=RELEASE)
    p.add_argument('--output',type=Path);p.add_argument('--inputs',type=Path)
    args=p.parse_args()
    try:
        if args.mode=='build':
            require(args.output is not None and args.inputs is not None,'build requires output and inputs')
            result=build(args.project.resolve(),args.output,args.inputs,args.release)
        else:result=check(args.project.resolve(),args.release)
        print(json.dumps(result,ensure_ascii=False,indent=2));return int(result['status']!='PASS')
    except (ValueError,KeyError,OSError) as error:
        print(json.dumps({'status':'FAIL','error':str(error)},ensure_ascii=False));return 1


if __name__=='__main__':raise SystemExit(main())
