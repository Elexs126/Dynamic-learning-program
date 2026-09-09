#!/usr/bin/env python3
"""Reproducible offline CS408 2009–2012 L2/L3 snapshot from reviewed local evidence.

The PSV files are the per-question semantic review, not an automatic inference
algorithm. This builder verifies their source lock and assembles cumulative
records. It never calls a model, network service, or modifies canonical sources.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

VERSION = 'cs408-2009-2012-l23-builder-v1.0.0'
REVIEW_DIR = Path(__file__).with_name('cs408_2009_2012_review_v1')
L1_PATH = '系统文件/题目标注/L1/question_annotations_l1_v1.json'
TOOL_DIR = '系统文件/脚本工具/05_标注与规范校验'
SCHEMA_DIR = '系统文件/数据规范'
OUTPUT_DIR = '系统文件/题目标注/408_2009_2012_L3'
BUNDLE = 'question_annotations_cs408_2009_2012_l23_v1.json'
L2_FIELDS = ('main_knowledge', 'assessed_construct', 'secondary_knowledge', 'primary_method', 'prerequisites', 'difficulty_band')
L3_FIELDS = ('score_units', 'score_attribution', 'evidence_steps', 'alternative_methods', 'inter_question_dependency', 'isomorphic_relation')
DIFFICULTIES = ('basic', 'intermediate', 'advanced', 'very_advanced')
DIFFICULTY_BASIS = {
    'basic': '单一标准任务，直接调用，操作链短。',
    'intermediate': '标准前置下的连续多步推理或计算。',
    'advanced': '存在条件辨识、边界退化、迁移、证明或多个关键目标。',
    'very_advanced': '多知识深度综合且证明或建模负荷很高。',
}
DATA_FILES = (BUNDLE, 'field_evidence_v1.jsonl', 'task_index_v1.json', 'label_registry_v1.json', 'isomorphic_clusters_v1.json', 'coverage_report.json', '执行与覆盖报告.md')
FORBIDDEN_KEYS = {'answer', 'solution', 'reference_answer', 'reference_solution', 'data_role', 'usage_role', 'practice_role', 'student_answer', 'student_score', 'audited_main_ability', 'candidate_main_ability'}


def require(value, message):
    if not value: raise ValueError(message)


def in_scope(record):
    fact=record['l0']
    return (fact['exam_track']=='CS408' and fact['source_file'].startswith('核心真题/408/')
            and fact['year'] in (2009,2010,2011,2012))


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def safe_path(root, relative):
    p = Path(relative)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in relative, 'Invalid relative path')
    full = (root/p).resolve()
    require(full.is_relative_to(root.resolve()), 'Path escapes project')
    return full


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec and spec.loader, 'Missing local dependency')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_reviews(folder):
    rows = {}
    require({p.stem for p in folder.glob('*.psv')}=={'2009','2010','2011','2012'}, 'Review years must be 2009–2012')
    for path in sorted(folder.glob('*.psv')):
        year_count = 0
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.startswith('#'): continue
            cells = [v.strip() for v in line.split('|')]
            require(len(cells) == 12, f'{path.name}:{lineno}: expected 12 columns')
            match = re.fullmatch(r'(\d{2})([CA])(\d{2})', cells[0])
            require(match is not None, f'Invalid reviewed id: {cells[0]}')
            yy, typ, number = match.groups()
            qid = f'408-{yy}-{typ}-T{number}'
            require(qid not in rows, f'Duplicate review: {qid}')
            require(int(path.stem) == 2000+int(yy), f'Year mismatch: {qid}')
            require(cells[3] in ('1','2','3','4'), f'Invalid difficulty: {qid}')
            rows[qid] = dict(zip(('short_id','main','method','difficulty','hard','secondary','tasks','signature','variant','alternatives','dependencies','issue'),cells))
            rows[qid].update(review_file=path.name, review_line=lineno)
            year_count += 1
        require(year_count == 47, f'Incomplete review year: {path.name}')
    require(len(rows) == 188, f'Expected 188 reviewed questions, found {len(rows)}')
    return rows


def split_items(text):
    return [s.strip() for s in text.split(';') if s.strip() and s.strip() != '-']


def field_path(name):
    if name.startswith(('l2.','l3.')): return name
    first, _, suffix = name.partition('.')
    require(first in L2_FIELDS + L3_FIELDS, f'Unknown omission field: {name}')
    return ('l2.' if first in L2_FIELDS else 'l3.') + first + ('.'+suffix if suffix else '')


def omissions_for(qid, row, policy):
    omissions = copy.deepcopy(policy.get('field_omissions',{}).get(qid,[]))
    issue = row['issue']
    if issue.startswith('BLOCK:'):
        fields, reason = issue[6:].split('@', 1)
        omissions += [dict(field_path=field_path(f), reason_type='human_review_needed', reason=reason) for f in fields.split(',')]
    for path in policy.get('extra_omissions',{}).get(qid,[]):
        omissions.append(dict(field_path=path,reason_type='human_review_needed',reason=issue))
    require(len({v['field_path'] for v in omissions}) == len(omissions), f'Duplicate omission: {qid}')
    return omissions


def source_inventory(project, review_dir):
    lock = read_json(review_dir/'source_lock_v1.json')
    l1 = read_json(project/L1_PATH)
    base = {r['question_id']:r for r in l1['records'] if in_scope(r)}
    parser = load_module('cs408_local_l1_parser',project/TOOL_DIR/'build_l1.py')
    blocks = {}
    inventory = collections.Counter()
    for rel, expected in lock['source_files'].items():
        source = safe_path(project,rel)
        require(sha_file(source) == expected, f'Source changed since review: {rel}')
        text = source.read_text(encoding='utf-8')
        lines = text.splitlines()
        for block in parser.parse_file(text,rel):
            qid = block['question_id']
            require(qid not in blocks, f'Duplicate source id: {qid}')
            require(block['block_hash'] == lock['question_hashes'][qid], f'Review source mismatch: {qid}')
            require(block['block_hash'] == base[qid]['l0']['question_hash_sha256'], f'L1 source mismatch: {qid}')
            start,end = block['line_start'],block['line_end']
            local_text = '\n'.join(lines[start-1:end])
            explanation = re.search(r'\*\*【解析】\*\*|【解析】',local_text)
            require(explanation, f'No local explanation: {qid}')
            evidence = {'source_file':rel,'source_locator':qid,'question_hash_sha256':block['block_hash'],
                        'line_start':start,'line_end':end,
                        'explanation_line': start+local_text.count('\n',0,explanation.start()),
                        'statement_sha256':sha_bytes(block['body'].encode())}
            block.update(evidence=evidence, local_text=local_text)
            blocks[qid]=block
            inventory['question_count'] += 1
            inventory['with_local_explanation'] += 1
            inventory['with_explicit_total_points'] += base[qid]['l0']['original_points'] is not None
            # Subpoint matches are evidence cues, not inferred allocations.
            rubric = re.search(r'评分说明|评分标准|评分细则|得分点|[（(]\d+\s*分[）)]',local_text)
            inventory['with_subpoint_or_rubric_cue'] += bool(rubric)
    require(set(blocks) == set(base) == set(lock['question_hashes']), 'Source/L1/review scope differs')
    live_files = {p.relative_to(project).as_posix() for p in (project/'核心真题/408').glob('*.md') if re.match(r'(2009|2010|2011|2012)年',p.name)}
    require(live_files == set(lock['source_files']), 'CS408 2009–2012 source files were added or removed')
    for rel, expected in lock['images'].items():
        require(sha_file(safe_path(project,rel)) == expected, f'Source image changed: {rel}')
    return base,blocks,dict(inventory),lock


def scoring_for(qid, record, block, local_tasks, main, secondary, ref, control):
    """Resolve additive units separately from partial and conditional evidence."""
    spec=control['questions'].get(qid,{'mode':'whole'})
    mode=spec['mode']; total=record['l0']['original_points']
    require(mode in ('whole','partition','conflicting_total'),'Unknown scoring mode')
    all_steps={f'{i}.{j}':f'[{tid}] {step}' for i,(tid,steps) in enumerate(local_tasks,1)
               for j,step in enumerate(steps,1)}

    def source_anchor(value):
        number=value['line'];start=block['evidence']['line_start']
        lines=block['local_text'].splitlines()
        require(start<=number<start+len(lines),f'{qid}: grading anchor outside question')
        text=lines[number-start];fragment=value['match']; occurrence=value['occurrence']
        require(occurrence>=1 and text.count(fragment)>=occurrence,f'{qid}: grading anchor changed at {number}')
        return {'source_file':block['evidence']['source_file'],'question_id':qid,
                'line':number,'fragment':fragment,'occurrence':occurrence,
                'line_sha256':sha_bytes(text.encode()),'question_hash_sha256':block['block_hash']}

    documented=[]
    for i,item in enumerate(spec.get('units',spec.get('documented_units',[])),1):
        require(item['step_refs'] and len(set(item['step_refs']))==len(item['step_refs']),f'{qid}: empty/duplicate scoring steps')
        require(set(item['step_refs'])<=set(all_steps),f'{qid}: unknown scoring task step')
        target=main if item['target']=='main' else ref(item['target'])
        require(target['id'] in [v['id'] for v in [main]+secondary],f'{qid}: unreviewed scoring target')
        documented.append({'evidence_id':f'{qid}:D{i:02d}','points':item['points'],
            'description':item['description'],'step_refs':item['step_refs'],
            'steps':[all_steps[s] for s in item['step_refs']],
            'attribution':{'category':item['category'],'target_knowledge_ids':[target['id']]},
            'source_anchor':source_anchor(item['anchor']),
            'promoted_unit_id':f'{qid}:S{i}' if mode=='partition' else None,
            'count_separately':False})
    if mode=='partition':
        require(len(documented)>1 and sum(x['points'] for x in documented)==total,f'{qid}: grading partition does not match source total')
        assigned=[s for x in documented for s in x['step_refs']]
        require(len(set(assigned))==len(assigned) and set(assigned)==set(all_steps),f'{qid}: grading partition must cover reviewed task steps exactly')
        units=[{'unit_id':x['promoted_unit_id'],'points':x['points'],'point_status':'explicit',
            'description':x['description'],
            'source_evidence':f"{x['source_anchor']['source_file']}:{x['source_anchor']['line']}；{x['evidence_id']}，见scoring_evidence_v1.json。",
            'confidence':'high'} for x in documented]
        attribution=[{'unit_id':x['promoted_unit_id'],**x['attribution'],'status':'verified'} for x in documented]
        evidence=[{'unit_id':x['promoted_unit_id'],'steps':x['steps'],
            'basis':f"本地解析明确标分位置{x['source_anchor']['line']}；仅提取作答行为，非解答。条件分另见scoring_evidence_v1.json。"} for x in documented]
    else:
        conflict=mode=='conflicting_total'
        if conflict:
            require(documented and sum(x['points'] for x in documented)!=total,f'{qid}: conflicting-total mode requires actual conflict')
        unit_id=qid+':S0'
        units=[{'unit_id':unit_id,'points':None if conflict else total,
            'point_status':'unresolved' if conflict else 'explicit_total_single_unit',
            'description':'整题单元；原总分与分项合计冲突，评分总分留空。' if conflict else '整题评分单元；原文未提供可完整采用的独立分值拆分。',
            'source_evidence':f"{block['evidence']['source_file']}#{qid}：分值元数据与局部细则见scoring_evidence_v1.json。",
            'confidence':'unknown' if conflict else 'high'}]
        integrated=record['l0']['question_type']=='analytical' and (secondary or len(local_tasks)>1)
        attribution=[{'unit_id':unit_id,'category':'integrated_target' if integrated else 'main_knowledge',
            'target_knowledge_ids':[v['id'] for v in [main]+(secondary if integrated else [])],'status':'verified'}]
        evidence=[{'unit_id':unit_id,'steps':list(all_steps.values()),
            'basis':f"{block['evidence']['source_file']}#{qid}；依据题干任务与本地解析提取可观察行为；未据此推算小问分值。"}]
    rules=[]
    for i,item in enumerate(spec.get('rules',[]),1):
        require(item['additive'] is False and item['application'] in ('once','per_task'),f'{qid}: conditional rule cannot be additive')
        require(item['kind'] in ('conditional_credit','conditional_cap','conditional_zero','clarification','discretionary'),f'{qid}: unknown scoring rule kind')
        require(item['points'] is None or 0<=item['points']<=total,f'{qid}: rule points exceed raw total')
        require(item['scope_status'] in ('verified','needs_review'),f'{qid}: unknown rule scope status')
        require(all(1<=j<=len(local_tasks) for j in item['tasks']),f'{qid}: rule refers to unknown task')
        rules.append({'rule_id':f'{qid}:R{i:02d}',**{k:item[k] for k in ('kind','points','condition','application','scope_status','additive')},
            'target_task_ids':[local_tasks[j-1][0] for j in item['tasks']] if item['scope_status']=='verified' else [],
            'source_anchor':source_anchor(item['anchor'])})
    return units,attribution,evidence,{'question_id':qid,'mode':mode,'raw_total_points':total,
        'effective_unit_ids':[u['unit_id'] for u in units],
        'effective_total_points':None if mode=='conflicting_total' else total,
        'documented_subpoints':documented,'conditional_rules':rules,'notes':spec.get('notes',[]),
        'counting_policy':'只累加核心记录的已确定score_units；本文件的分项证据和条件规则不另行加算。'}


def generate(project,review_dir=REVIEW_DIR):
    rows = read_reviews(review_dir)
    policy = read_json(review_dir/'review_policy_v1.json')
    scoring_control=read_json(review_dir/'scoring_plan_v1.json')
    base,blocks,inventory,lock = source_inventory(project,review_dir)
    require(set(rows)==set(base), 'Reviewed ids do not exactly cover canonical CS408 2009–2012')
    cue_ids={q for q,b in blocks.items() if re.search(r'评分说明|评分标准|评分细则|得分点|[（(]\d+\s*分[）)]',b['local_text'])}
    require(cue_ids==set(scoring_control['questions']),'Local rubric cues must all be reviewed; do not apply a global skip')
    registry = {'knowledge':{},'methods':{}}

    def ref(name,kind='knowledge'):
        require(name and name!='-', 'Empty semantic label')
        identifier = ('CS408_K_' if kind=='knowledge' else 'CS408_METHOD_')+sha_bytes(name.encode())[:16]
        previous=registry[kind].get(identifier)
        require(previous is None or previous['name']==name, 'Label identifier collision')
        registry[kind][identifier]={'id':identifier,'name':name}
        return {'id':identifier,'name':name}

    clusters={}
    for c in policy['clusters']:
        require(len(c['question_ids'])>=2,'Singleton declared isomorphism')
        for qid in c['question_ids']:
            require(qid in rows and qid not in clusters,'Invalid or multiply clustered question')
            clusters[qid]=c
    require(set(scoring_control['questions'])<=set(rows),'Grading control outside review scope')
    require(scoring_control['default_mode']=='whole','Unknown default scoring policy')
    records=[]; evidence=[]; tasks=[];scoring=[]
    for qid in sorted(rows):
        row=rows[qid];block=blocks[qid];r=copy.deepcopy(base[qid])
        r.update(schema_version='question-annotation-v1.1.0',annotation_depth='L3',record_status='needs_review')
        r['field_omissions']=omissions_for(qid,row,policy)
        omitted={x['field_path'] for x in r['field_omissions']}
        main=ref(policy.get('main_overrides',{}).get(qid,row['main']))
        secondary=[ref(s) for s in split_items(row['secondary'])] if 'l2.secondary_knowledge' not in omitted else []
        local_tasks=[]
        for i,section in enumerate(row['tasks'].split('/'),1):
            steps=split_items(section)
            require(steps,f'Missing observable task: {qid}')
            tid=f'{qid}#T{i:02d}'
            task={'task_id':tid,'question_id':qid,'task_index':i,'description':'；'.join(steps),
                  'kind':'statement_or_reasoning_task_not_score_atom','source_locator':qid}
            tasks.append(task);local_tasks.append((tid,steps))
        construct='能'+ '；并能'.join('、'.join(steps) for _,steps in local_tasks)+'。'
        l2={'main_knowledge':main,'assessed_construct':construct,'secondary_knowledge':secondary,
            'prerequisites':{'hard_prerequisite':[ref(s) for s in split_items(row['hard'])],'soft_prerequisite':[]},
            'difficulty_band':DIFFICULTIES[int(row['difficulty'])-1]}
        if row['method']!='-': l2['primary_method']=ref(row['method'],'methods')
        units,attribution,observable,grading=scoring_for(qid,r,block,local_tasks,main,secondary,ref,scoring_control)
        scoring.append(grading)
        l3={'score_units':units,'score_attribution':attribution,
            'evidence_steps':observable,
            'alternative_methods':[dict(ref(s,'methods'),conditions='仅按本题现存题干及本地解析所述适用条件；不据此补全缺失原稿。') for s in split_items(row['alternatives'])],
            'inter_question_dependency':{'relations':[],'unresolved_legacy_note':None},
            'isomorphic_relation':None}
        for edge in split_items(row['dependencies']):
            a,b=map(int,edge.split('>'))
            require(1<=a<b<=len(local_tasks),f'Invalid task dependency: {qid}:{edge}')
            l3['inter_question_dependency']['relations'].append({
                'from_question_id':local_tasks[a-1][0],'to_question_id':local_tasks[b-1][0],
                'description':f'本地解法中任务{b}调用任务{a}得到的对象或结果。仅描述该解法的直接使用，不声称所有备选方法都必须依赖。任务引用不是独立评分原子。',
                'status':'verified'})
        if qid in clusters:
            c=clusters[qid]
            l3['isomorphic_relation']={k:copy.deepcopy(c[k]) for k in ('cluster_id','structural_invariant','transfer_axis','status')}
            l3['isomorphic_relation']['related_question_ids']=[v for v in c['question_ids'] if v!=qid]
        for layer,fields in [('l2',L2_FIELDS),('l3',L3_FIELDS)]:
            values=l2 if layer=='l2' else l3
            status={f:'verified' for f in fields}; confidence={f:'high' for f in fields}
            for f in fields:
                path=f'{layer}.{f}'
                if path in omitted:
                    values.pop(f,None); status[f]='needs_review';confidence[f]='unknown'
                elif any(v.startswith(path+'.') for v in omitted):
                    status[f]='needs_review';confidence[f]='medium'
                elif f in ('prerequisites','difficulty_band','score_attribution','isomorphic_relation'):
                    confidence[f]='medium'
                elif row['issue']!='-' and f in ('main_knowledge','primary_method','evidence_steps','secondary_knowledge'):
                    confidence[f]='medium'
            values['review_status_by_field']=status;values['confidence_by_field']=confidence
        r['l2']=l2;r['l3']=l3
        r['review_flags']=sorted(set(r['review_flags']+['LOCAL_L2_L3_SEMANTIC_REVIEW','LOCAL_RUBRIC_NOT_INDEPENDENTLY_AUTHENTICATED']
            +(['EXPLICIT_SUBPOINT_PARTITION'] if grading['mode']=='partition' else ['NO_COMPLETE_SUBPOINT_PARTITION'])
            +(['SOURCE_SCORE_CONFLICT'] if grading['mode']=='conflicting_total' else [])
            +(['LOCAL_SOURCE_ISSUE'] if row['issue']!='-' else [])+(['PARTIAL_FIELDS_REQUIRE_ORIGINAL_CHECK'] if omitted else [])))
        field_evidence={}
        for layer,fields in [('l2',L2_FIELDS),('l3',L3_FIELDS)]:
            for f in fields:
                path=f'{layer}.{f}'; status=r[layer]['review_status_by_field'][f]
                field_evidence[path]={'status':status,'confidence':r[layer]['confidence_by_field'][f],
                    'basis':'题干任务和本地解析的逐题语义核对；见同记录source与review_source定位。'}
        field_evidence['l2.difficulty_band']['basis']=DIFFICULTY_BASIS[DIFFICULTIES[int(row['difficulty'])-1]]+' 为静态教学判断，不是学生实测难度。'
        if 'l2.difficulty_band' in omitted:
            field_evidence['l2.difficulty_band']['basis']='源条件冲突，不能可靠判断静态难度；未采用草案难度。'
        field_evidence['l3.score_units']['basis']=policy['score_policy']
        field_evidence['l3.score_attribution']['basis']='根据所采用评分单元填写结构性目标归属；分项只在本地评分证据完整一致时采用，不表示已独立认证的官方知识点评分比例。'
        field_evidence['l3.isomorphic_relation']['basis']='；'.join([policy['empty_policy'],clusters[qid]['scope'] if qid in clusters else '未在本次408的2009—2012年范围确认可填写的匹配关系。'])
        field_evidence['l3.alternative_methods']['basis']='只登记本地解析实际给出且具有不同机制的可行方法；孤立特例或同一推导改写不作独立备选。'
        if r['l3'].get('isomorphic_relation') is None and 'l3.isomorphic_relation' in omitted:
            field_evidence['l3.isomorphic_relation']['basis']='源条件存在冲突，不能确认结构匹配；待核对原稿，不能当作没有同构题。'
        evidence.append({'question_id':qid,'source':block['evidence'],
                         'review_source':{'file':f'{TOOL_DIR}/cs408_2009_2012_review_v1/{row["review_file"]}','line':row['review_line']},
                         'reviewer_kind':'assistant_offline_semantic_review','human_review_performed':False,
                         'source_issue':None if row['issue']=='-' else row['issue'].split('@',1)[-1],
                         'field_evidence':field_evidence,'field_omissions':r['field_omissions']})
        records.append(r)
    bundle={'schema_version':'question-annotations-bundle-v1.1.0','generated_at':policy['generated_at'],
            'source_file':L1_PATH,'source_schema_version':'question-annotations-bundle-v1.0.0','record_count':len(records),'records':records}
    task_bundle={'schema_version':'cs408-task-reference-index-v1.0.0','description':policy['score_policy'],'tasks':tasks}
    reg={'schema_version':'cs408-label-registry-v1.0.0','scope':'本次408的2009—2012年标注中出现的可引用词条；未冻结全库知识图或能力认证。',
         'knowledge':sorted(registry['knowledge'].values(),key=lambda x:x['id']), 'methods':sorted(registry['methods'].values(),key=lambda x:x['id'])}
    coverage={}
    for layer,fields in [('l2',L2_FIELDS),('l3',L3_FIELDS)]:
        for f in fields:
            coverage[f'{layer}.{f}']={'filled':sum(f in r[layer] for r in records),
                'verified':sum(r[layer]['review_status_by_field'][f]=='verified' for r in records),
                'needs_review':sum(r[layer]['review_status_by_field'][f]=='needs_review' for r in records)}
    human=collections.defaultdict(list)
    for r in records:
        for v in r['field_omissions']:
            human['.'.join(v['field_path'].split('.')[:2])].append(r['question_id'])
    report={'schema_version':'cs408-2009-2012-l23-coverage-v1.0.0','builder_version':VERSION,'record_count':188,'inventory':inventory,
            'year_counts':dict(sorted(collections.Counter(str(r['l0']['year']) for r in records).items())),
            'field_coverage':coverage,'global_skips':policy['global_skips'],'source_scope':policy['source_scope'],
            'human_required_label_types':{f:sorted(set(ids)) for f,ids in sorted(human.items())},
            'human_required_question_count':sum(bool(r['field_omissions']) for r in records),
            'source_issue_count':sum(e['source_issue'] is not None for e in evidence),
            'source_issues':[{k:e[k] for k in ('question_id','source_issue','field_omissions')} for e in evidence if e['source_issue']],
            'score_unit_count':sum(len(r['l3']['score_units']) for r in records),'task_reference_count':len(tasks),
            'explicit_partition_question_count':sum(s['mode']=='partition' for s in scoring),
            'explicit_partition_unit_count':sum(len(s['documented_subpoints']) for s in scoring if s['mode']=='partition'),
            'documented_subpoint_count':sum(len(s['documented_subpoints']) for s in scoring),
            'conditional_rule_count':sum(len(s['conditional_rules']) for s in scoring),
            'unresolved_total_question_ids':[s['question_id'] for s in scoring if s['mode']=='conflicting_total'],
            'unresolved_rule_scope_question_ids':[s['question_id'] for s in scoring if any(x['scope_status']=='needs_review' for x in s['conditional_rules'])],
            'incomplete_documented_partition_question_ids':[s['question_id'] for s in scoring if s['mode']=='whole' and s['documented_subpoints']],
            'analytical_without_numeric_subpoint_partition':[r['question_id'] for r,s in zip(records,scoring) if r['l0']['question_type']=='analytical' and s['mode']!='partition'],
            'official_rubric_authenticated':False,
            'alternative_method_question_count':sum(bool(r['l3'].get('alternative_methods')) for r in records),
            'alternative_method_count':sum(len(r['l3'].get('alternative_methods',[])) for r in records),
            'dependency_count':sum(len(r['l3'].get('inter_question_dependency',{}).get('relations',[])) for r in records),
            'isomorphic_cluster_count':len(policy['clusters']),'isomorphic_question_count':len(clusters),
            'source_image_count':len(lock['images']),'external_api_calls':0,'network_requests':0,
            'record_status_note':'整条记录保留needs_review，因为累积L0/L1仍有来源质量/候选状态；L2/L3以字段状态判断。',
            'additional_human_required_label_types':policy['additional_human_required_label_types'],
            'additional_human_required_reasons':policy['additional_human_required_reasons'],
            'limitations':[policy['review_policy'],policy['score_policy'],policy['empty_policy'],policy['out_of_scope_missing_source_note'],
                           '未修改原题、原答案、L1快照、使用角色、作答或正式考频。']}
    lines=['# 408的2009—2012年 L2—L3 执行与覆盖报告','',f"完成本地188题可判断标签；{report['human_required_question_count']}题存在受源文冲突影响而留空的字段。",'',
           '逐题读取题干和本地解析；仅记录任务与解法骨架，不输出原题答案。未联网或调用外部API。','',
           '## 字段覆盖','', '| 字段 | 已填 | 已核对 | 待核对 |','|---|---:|---:|---:|']
    for f,n in coverage.items():lines.append(f"| {f} | {n['filled']} | {n['verified']} | {n['needs_review']} |")
    lines += ['', '## 因整库未提供信息而整体跳过','']
    lines += [f"- {v['label_type']}：{v['reason']}" for v in policy['global_skips']]
    if not policy['global_skips']:lines.append('本批L2/L3没有因整类资料缺失而整体跳过的字段类型。部分题目缺少小问分值，仍保留整题单元；有明确细则的题全部记录。')
    lines += ['', '## 需人工或原稿确认而未完成的标签类型','']
    for f,ids in report['human_required_label_types'].items():lines.append(f"- `{f}`：{len(ids)}题；"+'、'.join(ids)+'。')
    lines += ['', '具体冲突和受影响字段见 `coverage_report.json` 的 `source_issues`；普通质量注记不代表整题标签都被跳过。', '',
              '## 评分与关系','',f"共{report['score_unit_count']}个评分单元；{report['explicit_partition_question_count']}题使用{report['explicit_partition_unit_count']}个明确且合计一致的分项，其余保留整题口径；{len(report['unresolved_total_question_ids'])}题因总分冲突留空有效总分。{len(tasks)}个任务引用只用于定位，不是额外评分原子。",
              f"另记录{report['documented_subpoint_count']}项原文分值证据与{report['conditional_rule_count']}条条件评分规则。这些证据不能与评分单元再次相加。2012第44题只提供前三问分值，不推算末问。",
              f"登记{report['alternative_method_count']}个备选方法、{report['dependency_count']}条本地解法依赖、{len(policy['clusters'])}个同构簇（{len(clusters)}题）。",'',
              *report['limitations'],'','核验结果另见 `validation_report.json` 和执行清单 `run_manifest.json`。']
    output={BUNDLE:json_bytes(bundle),'task_index_v1.json':json_bytes(task_bundle),'label_registry_v1.json':json_bytes(reg),
            'scoring_evidence_v1.json':json_bytes({'schema_version':'cs408-scoring-evidence-v1.0.0','policy':scoring_control['policy'],'records':scoring}),
            'isomorphic_clusters_v1.json':json_bytes({'schema_version':'cs408-isomorphic-clusters-v1','clusters':policy['clusters']}),
            'coverage_report.json':json_bytes(report),'执行与覆盖报告.md':('\n'.join(lines)+'\n').encode(),
            'field_evidence_v1.jsonl':''.join(json.dumps(e,ensure_ascii=False,sort_keys=True)+'\n' for e in evidence).encode()}
    return output


def walk_forbidden(value,trail='$'):
    errors=[]
    if isinstance(value,dict):
        for k,v in value.items():
            if k in FORBIDDEN_KEYS:errors.append(f'{trail}.{k}: forbidden payload')
            errors += walk_forbidden(v,trail+'.'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):errors += walk_forbidden(v,f'{trail}[{i}]')
    return errors


def validate_data(project,schema_dir,output,review_dir=REVIEW_DIR):
    project=Path(project);schema_dir=Path(schema_dir or project/SCHEMA_DIR)
    bundle=json.loads(output[BUNDLE]);tasks=json.loads(output['task_index_v1.json'])['tasks']
    registry=json.loads(output['label_registry_v1.json'])
    runtime=load_module('cs408_schema_runtime',project/TOOL_DIR/'json_schema_runtime.py')
    errors=runtime.SchemaRuntime(schema_dir/'question_annotations_bundle_v1.1.schema.json').validate(bundle)
    errors += walk_forbidden(bundle)
    for name,data in output.items():
        if name.endswith('.json') and name!=BUNDLE:errors += walk_forbidden(json.loads(data),name)
        elif name.endswith('.jsonl'):
            for line in data.decode().splitlines():errors += walk_forbidden(json.loads(line),name)
    if errors:
        return {'status':'FAIL','record_count':len(bundle.get('records',[])), 'error_count':len(errors),'errors':errors,'checks':['schema and forbidden payload']}
    records=bundle['records'];byid={r['question_id']:r for r in records};task_byid={t['task_id']:t for t in tasks}
    base={r['question_id']:r for r in read_json(project/L1_PATH)['records'] if in_scope(r)}
    knowledge={r['id']:r['name'] for r in registry['knowledge']};methods={r['id']:r['name'] for r in registry['methods']}
    evidence=[json.loads(line) for line in output['field_evidence_v1.jsonl'].decode().splitlines()]
    reviewed=read_reviews(review_dir);policy=read_json(review_dir/'review_policy_v1.json')
    scoring_control=read_json(review_dir/'scoring_plan_v1.json')
    _,blocks,_,_=source_inventory(project,review_dir)
    score_records=json.loads(output['scoring_evidence_v1.json'])['records']
    score_byid={r['question_id']:r for r in score_records}
    if len(score_byid)!=188 or len(score_records)!=188 or set(score_byid)!=set(base):errors.append('Scoring evidence coverage differs')
    if len(byid)!=188 or len(records)!=188 or bundle['record_count']!=188: errors.append('CS408 2009–2012 record coverage must be exactly 188 unique ids')
    if set(byid)!=set(base): errors.append('Canonical CS408 2009–2012 scope differs')
    if len(evidence)!=188 or {e['question_id'] for e in evidence}!=set(byid):errors.append('Evidence coverage differs')
    if len(task_byid)!=len(tasks):errors.append('Duplicate task reference')
    if len(knowledge)!=len(registry['knowledge']) or len(methods)!=len(registry['methods']):errors.append('Duplicate registry identifier')
    expected_tasks=[]
    for q,row in sorted(reviewed.items()):
        for i,section in enumerate(row['tasks'].split('/'),1):
            expected_tasks.append({'task_id':f'{q}#T{i:02d}','question_id':q,'task_index':i,
                'description':'；'.join(split_items(section)),
                'kind':'statement_or_reasoning_task_not_score_atom','source_locator':q})
    if tasks!=expected_tasks:errors.append('Task index differs from reviewed observable tasks')
    expected_clusters=json.loads(output['isomorphic_clusters_v1.json'])['clusters']
    if expected_clusters!=policy['clusters']:errors.append('Isomorphic clusters differ from reviewed structural evidence')
    cluster_by_q={q:c for c in policy['clusters'] for q in c['question_ids']}
    for r in records:
        q=r['question_id'];l2=r['l2'];l3=r['l3'];om={v['field_path'] for v in r['field_omissions']}
        for path in om:
            parts=path.split('.')
            valid=parts[0] in ('l2','l3') and len(parts)>=2 and parts[1] in (L2_FIELDS if parts[0]=='l2' else L3_FIELDS)
            valid=valid and (len(parts)==2
                or (len(parts)==3 and parts[:2]==['l3','evidence_steps'] and re.fullmatch(r'U\d{2}',parts[2]))
                or (len(parts)==4 and parts[:2]==['l3','score_units'] and re.fullmatch(r'S\d+',parts[2]) and parts[3] in ('points','subdivision')))
            if not valid:errors.append(q+': unknown omission path '+path)
        if q not in base:errors.append(q+': not canonical');continue
        if r['field_omissions']!=omissions_for(q,reviewed[q],policy):errors.append(q+': omission differs from reviewed reason')
        if r['l0']!=base[q]['l0'] or r['l1']!=base[q]['l1']:errors.append(q+': cumulative L0/L1 changed')
        for layer,fields in [('l2',L2_FIELDS),('l3',L3_FIELDS)]:
            for f in fields:
                p=f'{layer}.{f}'
                if f not in r[layer] and p not in om:errors.append(q+': undeclared omission '+p)
                if f in r[layer] and p in om:errors.append(q+': omitted field was filled '+p)
                affected=any(v==p or v.startswith(p+'.') for v in om)
                if affected != (r[layer]['review_status_by_field'][f]=='needs_review'):errors.append(q+': omission status mismatch '+p)
        if 'main_knowledge' in l2:
            reviewed_tasks=[(f'{q}#T{i:02d}',split_items(s)) for i,s in enumerate(reviewed[q]['tasks'].split('/'),1)]
            kref=lambda name:{'id':'CS408_K_'+sha_bytes(name.encode())[:16],'name':name}
            try:
                expected_scores=scoring_for(q,base[q],blocks[q],reviewed_tasks,l2['main_knowledge'],l2.get('secondary_knowledge',[]),kref,scoring_control)
                for field,expected in zip(('score_units','score_attribution','evidence_steps'),expected_scores[:3]):
                    if l3.get(field)!=expected:errors.append(q+': scoring field differs from reviewed evidence '+field)
                if score_byid.get(q)!=expected_scores[3]:errors.append(q+': conditional/partial scoring evidence changed or double counted')
            except ValueError as exc:
                errors.append(str(exc))
        units={u['unit_id'] for u in l3.get('score_units',[])}
        if len(units)!=len(l3.get('score_units',[])):errors.append(q+': duplicate scoring unit')
        for item in l3.get('evidence_steps',[])+l3.get('score_attribution',[]):
            if item['unit_id'] not in units:errors.append(q+': dangling score unit')
        if 'main_knowledge' not in l2:errors.append(q+': this release requires one main knowledge target')
        local_refs=([l2['main_knowledge']] if 'main_knowledge' in l2 else [])+l2.get('secondary_knowledge',[])
        if len(l2.get('secondary_knowledge',[]))>(2 if r['l0']['question_type']=='analytical' else 1):errors.append(q+': too many secondary knowledge labels')
        if len({v['id'] for v in local_refs})!=len(local_refs):errors.append(q+': duplicate main/secondary label')
        prereq=l2.get('prerequisites',{})
        local_refs += prereq.get('hard_prerequisite',[])+prereq.get('soft_prerequisite',[])
        for ref in local_refs:
            if knowledge.get(ref['id'])!=ref['name']:errors.append(q+': unknown knowledge reference')
        for ref in ([l2['primary_method']] if 'primary_method' in l2 else [])+l3.get('alternative_methods',[]):
            if methods.get(ref['id'])!=ref['name']:errors.append(q+': unknown method reference')
        for attr in l3.get('score_attribution',[]):
            if not set(attr['target_knowledge_ids'])<=set(knowledge):errors.append(q+': unknown attribution reference')
        for dep in l3.get('inter_question_dependency',{}).get('relations',[]):
            a,b=dep['from_question_id'],dep['to_question_id']
            if a not in task_byid or b not in task_byid:errors.append(q+': dangling dependency');continue
            if task_byid[a]['question_id']!=q or task_byid[b]['question_id']!=q or task_byid[a]['task_index']>=task_byid[b]['task_index']:errors.append(q+': invalid/cyclic task dependency')
        iso=l3.get('isomorphic_relation')
        expected_iso=None
        if q in cluster_by_q:
            cluster=cluster_by_q[q]
            expected_iso={k:cluster[k] for k in ('cluster_id','structural_invariant','transfer_axis','status')}
            expected_iso['related_question_ids']=[v for v in cluster['question_ids'] if v!=q]
        if iso!=expected_iso:errors.append(q+': isomorphism differs from reviewed local comparison')
        if iso:
            for target in iso['related_question_ids']:
                other=byid.get(target,{}).get('l3',{}).get('isomorphic_relation')
                if target==q or not other or other['cluster_id']!=iso['cluster_id'] or q not in other['related_question_ids']:errors.append(q+': asymmetric/dangling isomorphism')
                if target in r['l1']['duplicate_candidate']['possible_duplicate_ids']:errors.append(q+': duplicate reused as isomorphism')
    return {'status':'PASS' if not errors else 'FAIL','record_count':len(records),'error_count':len(errors),'errors':errors,
            'checks':['v1.1 JSON schema','188 unique canonical ids in 2009–2012','original L0/L1 exact preservation','reviewed source hashes and local images',
                      'explicit partitions equal raw totals and cover observable steps','partial and conditional scores cannot be added twice','source total conflict remains unresolved',
                      'all omitted fields declared with reviewed reasons','task dependency references and acyclicity',
                      'reciprocal isomorphic references distinct from duplicates','knowledge and method registry','no answer/student/role payload'],
            'semantic_limit':'PASS证明结构、引用、来源绑定及一致性；语义标签已逐题核对，但不是原稿答案认证或人工签核。'}


def inputs(project,review_dir,schema_dir):
    result={'project:'+L1_PATH:sha_file(project/L1_PATH),'code:build_cs408_l23.py':sha_file(Path(__file__))}
    for rel in ('build_l1.py','json_schema_runtime.py'):result['project:'+TOOL_DIR+'/'+rel]=sha_file(project/TOOL_DIR/rel)
    for p in sorted(review_dir.iterdir()):
        if p.is_file():result['review:'+p.name]=sha_file(p)
    for name in ('question_annotation_v1.1.schema.json','question_annotations_bundle_v1.1.schema.json'):
        result['schema:'+name]=sha_file(schema_dir/name)
    lock=read_json(review_dir/'source_lock_v1.json')
    for rel in list(lock['source_files'])+list(lock['images']):result['project:'+rel]=sha_file(safe_path(project,rel))
    return dict(sorted(result.items()))


def run(project,output,mode='build',review_dir=REVIEW_DIR,schema_dir=None):
    project=Path(project).resolve();output=Path(output).resolve();review_dir=Path(review_dir).resolve()
    schema_dir=Path(schema_dir or project/SCHEMA_DIR).resolve()
    require(not output.is_relative_to(project/'核心真题'), 'Cannot write an annotation snapshot inside raw sources')
    before=inputs(project,review_dir,schema_dir)
    payload=generate(project,review_dir)
    validation=validate_data(project,schema_dir,payload,review_dir)
    require(validation['status']=='PASS',json.dumps(validation,ensure_ascii=False))
    payload['validation_report.json']=json_bytes(validation)
    require(inputs(project,review_dir,schema_dir)==before,'Inputs changed during build')
    if output.exists():
        require((output/'run_manifest.json').is_file(),'Existing output is not a managed snapshot')
        manifest=read_json(output/'run_manifest.json')
        require({p.name for p in output.iterdir()} == set(payload)|{'run_manifest.json'},'Unexpected files in immutable snapshot')
        require(manifest['input_hashes']==before,'Snapshot inputs changed; use a new versioned output directory')
        require(set(manifest['output_hashes'])==set(payload),'Snapshot file inventory differs')
        for name,data in payload.items():
            require(sha_file(output/name)==manifest['output_hashes'][name]==sha_bytes(data),'Snapshot content changed: '+name)
        validation['mode']='checked' if mode=='check' else 'reused'
        return validation
    require(mode=='build','Snapshot does not exist')
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix='.cs408-2009-2012-l23-',dir=output.parent))
    try:
        for name,data in payload.items():(temp/name).write_bytes(data)
        manifest={'builder_version':VERSION,'input_hashes':before,'output_hashes':{name:sha_bytes(data) for name,data in payload.items()},
                  'network_requests':0,'external_api_calls':0,'source_mutations':0}
        (temp/'run_manifest.json').write_bytes(json_bytes(manifest))
        temp.rename(output)
    finally:
        if temp.exists():shutil.rmtree(temp)
    validation['mode']='built'
    return validation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['build','check'])
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[3])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--review-dir',type=Path,default=REVIEW_DIR)
    parser.add_argument('--schema-dir',type=Path)
    args=parser.parse_args()
    try:
        result=run(args.project,args.output or args.project/OUTPUT_DIR,args.mode,args.review_dir,args.schema_dir)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError) as exc:
        print(f'FAIL: {exc}',file=sys.stderr);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
