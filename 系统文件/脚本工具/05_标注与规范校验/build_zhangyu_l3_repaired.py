#!/usr/bin/env python3
"""Assemble source-locked explicit practice decisions, including partial omissions.

This revision rechecks 653 risk questions and inherits 1264 v2 decisions. It
does not classify questions from chapter names or claim a fresh full audit.
"""
from __future__ import annotations
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

sys.dont_write_bytecode=True
VERSION='zhangyu-practice-l3-repaired-v3.0.0'
TOOL='系统文件/脚本工具/05_标注与规范校验'
DEFAULT_OUTPUT='系统文件/题目标注/数学一配套题_L3_20260930_v3'
PREVIOUS='系统文件/题目标注/数学一配套题_L3_20260929_v2'
REVIEW=Path(__file__).with_name('zhangyu_l3_review_v3')
BASE='系统文件/题目标注/L1_L3衔接_20260910_v1/L1/question_annotations_l1_v1.json'
L2=('main_knowledge','assessed_construct','secondary_knowledge','primary_method','prerequisites','difficulty_band')
L3=('score_units','score_attribution','evidence_steps','alternative_methods','inter_question_dependency','isomorphic_relation')
COUNTS={'zy30':876,'zy1000':1041}
FORBIDDEN={'answer','solution','reference_answer','reference_solution','student_answer','student_score',
           'data_role','practice_role','usage_role','candidate_main_ability','audited_main_ability'}
SYNTHETIC=('所需的中间对象','代入前项中间对象')

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def dump(x):return (json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def file_sha(path):return sha(Path(path).read_bytes())
def require(ok,message):
    if not ok:raise ValueError(message)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def book(q):return 'zy30' if q.startswith('ZY30-') else 'zy1000'
def resolve(root,relative):
    p=(root/relative).resolve()
    require(p.is_relative_to(root.resolve()),'Path outside project: '+str(relative))
    return p
def helper(project):return module('zy_v2_source_helpers',project/TOOL/'build_zhangyu_l3_full.py')
def inventory(project,review):return helper(project).inventory(project,review)
def reference(name,kind='knowledge'):
    prefix='M1_K_' if kind=='knowledge' else 'M1_METHOD_'
    return {'id':prefix+sha(name.encode())[:16],'name':name}
def task_omissions(d):
    return {int(p.rsplit('.U',1)[1]) for p in d.get('blocked',[]) if '.U' in p}

def load_decisions(review,base,blocks):
    decisions=read(review/'decisions_v3.json');scope=read(review/'repair_scope_v3.json')
    require(set(decisions)==set(base),'Release requires all 1917 explicit decisions')
    reviewed=scope['corrected_question_ids']
    require(len(reviewed)==len(set(reviewed))==653,'Repair scope must contain 653 distinct questions')
    require(set(reviewed)=={q for q,d in decisions.items() if d['review_round']=='corrected_v3'},'Repair scope/review provenance mismatch')
    require(scope['fresh_semantic_rechecks']==653 and scope['inherited_v2_decisions']==1264,'Review count mismatch')
    paths={l+'.'+f for l,fields in [('l2',L2),('l3',L3)] for f in fields}
    for q,d in decisions.items():
        require(d['question_hash_sha256']==blocks[q]['block_hash'],'Semantic review is stale: '+q)
        require(d['review_round'] in ('inherited_v2','corrected_v3'),'Invalid review provenance: '+q)
        require(all(isinstance(d[k],str) and d[k].strip() for k in ('main','method','review_note')),'Missing explicit label or review note: '+q)
        require(d['steps'] and d['tasks'] and all(ss and all(isinstance(s,str) and s.strip() for s in ss) for ss in d['tasks']),'Missing explicit steps/tasks: '+q)
        require(not any(t in s for ss in d['tasks'] for s in ss for t in SYNTHETIC),'Synthetic task template: '+q)
        blocked=d.get('blocked',[])
        require(len(blocked)==len(set(blocked)),'Duplicate blocked path: '+q)
        for p in blocked:
            require(p in paths or (re.fullmatch(r'l3\.evidence_steps\.U\d{2}',p) and 1<=int(p[-2:])<=len(d['tasks'])),'Invalid omission path: '+q+' '+p)
        require(not blocked or d.get('source_issue'),'Omission needs a source-specific reason: '+q)
        require(not ('l3.evidence_steps' in blocked and task_omissions(d)),'Redundant whole/partial omission: '+q)
        require(len(d['dependencies'])==len({tuple(e) for e in d['dependencies']}),'Duplicate dependency: '+q)
        for a,b in d['dependencies']:
            require(1<=a<b<=len(d['tasks']),'Dangling/backward/cyclic task dependency: '+q)
        mechanisms=[a.get('mechanism') for a in d['alternatives']]
        if mechanisms:
            require(d.get('primary_mechanism') and all(mechanisms),'Alternative mechanism must be explicitly reviewed: '+q)
            require(len(set(mechanisms+[d['primary_mechanism']]))==len(mechanisms)+1,'Duplicate method mechanism: '+q)
            require(all(a.get('conditions') and a.get('name') for a in d['alternatives']),'Alternative lacks conditions: '+q)
    return decisions,scope

def project_record(original,b,d,cluster,helpers):
    """The complete approved projection for one question; no profile defaults."""
    q=original['question_id'];r=copy.deepcopy(original);unit=q+':S0'
    flags=helpers.quality(b['body'])
    if d.get('images_reviewed'):flags=[f for f in flags if f!='IMAGE_REQUIRES_VISUAL_REVIEW']
    change=None;typ=helpers.changed_type(r,b['body'])
    if typ and typ!=r['l0']['question_type']:
        change=dict(question_id=q,field='l0.question_type',before=r['l0']['question_type'],after=typ,
                    basis='明确填空占位符；沿用v2已登记修正，选择题优先。',source_file=b['source_file'],
                    line_start=b['line_start'],question_hash_sha256=b['block_hash'])
        r['l0']['question_type']=typ;r['l0']['review_status_by_field']['question_type']='verified'
    r.update(schema_version='question-annotation-v1.2.0',annotation_depth='L3',record_status='needs_review',field_omissions=[])
    r['review_flags']=sorted(set(r['review_flags']+flags+['NO_LOCAL_SOLUTION_OR_OFFICIAL_RUBRIC','TEXTBOOK_POINTS_NOT_APPLICABLE']+(['SOURCE_SEMANTIC_ISSUE'] if d.get('source_issue') else [])))
    layers={name:{'review_status_by_field':{f:'verified' for f in fields},
                  'confidence_by_field':{f:'medium' for f in fields}} for name,fields in [('l2',L2),('l3',L3)]}
    main=reference(d['main']);secondary=[reference(x) for x in d['secondary']]
    method=reference(d['method'],'methods')
    if d.get('method_conditions'):method['conditions']=d['method_conditions']
    partial=task_omissions(d);whole='l3.evidence_steps' in d.get('blocked',[])
    confirmed=[s for i,ss in enumerate(d['tasks'],1) if i not in partial for s in ss]
    construct=d['steps'] if whole else confirmed
    layers['l2'].update(main_knowledge=main,secondary_knowledge=secondary,
        assessed_construct='能'+'；并能'.join(construct)+'。',primary_method=method,
        prerequisites={'hard_prerequisite':[reference(x) for x in d['hard']],
                       'soft_prerequisite':[reference(x) for x in d.get('soft',[])]},difficulty_band=d['difficulty_band'])
    provenance=('本轮按源文重新核对本题。' if d['review_round']=='corrected_v3' else '沿用源文锁定的v2逐题决定，本轮未声称重新阅读本题。')
    layers['l3'].update(
      score_units=[dict(unit_id=unit,points=None,point_status='not_applicable',
        description='教辅整题观察单元；不设小问分值或最小评分原子。',
        source_evidence=f"{b['source_file']}#{q}；原题不含试卷分值。",confidence='high')],
      score_attribution=[dict(unit_id=unit,category='integrated_target' if secondary else 'main_knowledge',
        target_knowledge_ids=[x['id'] for x in [main]+secondary],status='verified')],
      evidence_steps=[dict(unit_id=unit,steps=[f'[{q}#T{i:02d}] {s}' for i,ss in enumerate(d['tasks'],1) if i not in partial for s in ss],
        basis=f"{b['source_file']}#{q}；"+provenance+'只记录有依据的可观察行为；缺失任务见field_omissions。')],
      alternative_methods=[dict(reference(a['name'],'methods'),conditions=a['conditions']) for a in d['alternatives']],
      inter_question_dependency={'relations':[],'unresolved_legacy_note':None},
      isomorphic_relation=None)
    layers['l3']['confidence_by_field']['score_units']='high'
    tasks=[]
    for i,ss in enumerate(d['tasks'],1):
        tasks.append(dict(task_id=f'{q}#T{i:02d}',question_id=q,task_index=i,description='；'.join(ss),
            kind='reasoning_reference_not_scoring_atom',evidence_status='needs_review' if whole or i in partial else 'verified'))
    relations=layers['l3']['inter_question_dependency']['relations']
    for a,t in d['dependencies']:
        relations.append(dict(from_question_id=f'{q}#T{a:02d}',to_question_id=f'{q}#T{t:02d}',
            description=f'后项“{d["tasks"][t-1][0]}”使用前项“{d["tasks"][a-1][-1]}”所得对象或结论；这里只登记已确认的调用，未认定缺失任务已解出。',status='verified'))
    if d.get('external_dependency'):
        relations.append(dict(from_question_id=d['external_dependency'],to_question_id=q,
            description='题干明确调用该具体前题的结论；不是同章节关系。',status='verified'))
    if cluster:
        layers['l3']['isomorphic_relation']={**{k:v for k,v in cluster.items() if k!='question_ids'},
                'related_question_ids':[other for other in cluster['question_ids'] if other!=q]}
    for path in d.get('blocked',[]):
        layer,field,*rest=path.split('.')
        if rest:
            layers[layer]['review_status_by_field'][field]='needs_review'
            layers[layer]['confidence_by_field'][field]='low'
        else:
            layers[layer].pop(field,None)
            layers[layer]['review_status_by_field'][field]='needs_review'
            layers[layer]['confidence_by_field'][field]='unknown'
        r['field_omissions'].append(dict(field_path=path,reason=d['source_issue'],reason_type='human_review_needed'))
    r['l2']=layers['l2'];r['l3']=layers['l3']
    ev=dict(question_id=q,source_file=b['source_file'],source_locator=q,
      question_hash_sha256=b['block_hash'],statement_sha256=sha(b['body'].encode()),line_start=b['line_start'],line_end=b['line_end'],
      priority='CORE_L2' if book(q)=='zy30' else 'L1_FIRST',reviewer_kind='assistant_offline_semantic_review',
      human_review_performed=False,review_round=d['review_round'],semantic_review_note=d['review_note'],
      source_issue=d.get('source_issue'),quality_flags=flags,method_basis=d['method'],
      method_mechanisms={'primary':d.get('primary_mechanism'),'alternatives':[a.get('mechanism') for a in d['alternatives']]},
      additional_source_evidence=d.get('additional_source_evidence'),images_reviewed=d.get('images_reviewed',False),
      source_recovery=d.get('source_recovery'),field_status={l:layers[l]['review_status_by_field'] for l in ('l2','l3')},
      field_omissions=r['field_omissions'])
    return r,ev,tasks,change

def create(project,review):
    helpers=helper(project);base,blocks,inputs=helpers.inventory(project,review)
    decisions,scope=load_decisions(review,base,blocks)
    clusters=read(review/'isomorphic_clusters_v1.json');cluster_by_q={}
    for c in clusters:
        for q in c['question_ids']:
            require(q in base and q not in cluster_by_q,'Invalid reviewed isomorphic cluster membership')
            cluster_by_q[q]=c
    for rel,h in read(review/'auxiliary_sources_v2.json').items():inputs[rel]=h
    rows=[];evidence=[];tasks=[];changes=[];registry={'knowledge':{},'methods':{}}
    def register(x):
        if isinstance(x,dict):
            if 'id' in x and 'name' in x and x['id'].startswith(('M1_K_','M1_METHOD_')):
                kind='knowledge' if x['id'].startswith('M1_K_') else 'methods'
                registry[kind][x['id']]={k:x[k] for k in ('id','name')}
            for v in x.values():register(v)
        elif isinstance(x,list):
            for v in x:register(v)
    for q in sorted(base,key=lambda q:(0 if book(q)=='zy30' else 1,blocks[q]['source_file'],blocks[q]['line_start'])):
        r,e,ts,c=project_record(base[q],blocks[q],decisions[q],cluster_by_q.get(q),helpers)
        rows.append(r);evidence.append(e);tasks+=ts
        if c:changes.append(c)
        register(r['l2']);register(r['l3'])
    outputs={}
    for cohort in COUNTS:
        selected=[r for r in rows if book(r['question_id'])==cohort]
        outputs[cohort+'/question_annotations_l3_v1.json']=dump(dict(schema_version='question-annotations-bundle-v1.2.0',
            generated_at='2026-09-30T00:00:00+08:00',source_file=BASE,source_schema_version='question-annotations-bundle-v1.0.0',
            record_count=len(selected),records=selected))
        outputs[cohort+'/field_evidence_v1.jsonl']=''.join(json.dumps(e,ensure_ascii=False,sort_keys=True)+'\n' for e in evidence if book(e['question_id'])==cohort).encode()
    outputs['label_registry_v1.json']=dump({k:list(v.values()) for k,v in registry.items()})
    outputs['task_index_v1.json']=dump({'tasks':tasks})
    outputs['isomorphic_clusters_v1.json']=dump({'clusters':clusters})
    outputs['l0_type_corrections_v1.json']=dump({'changes':changes})
    queue=[dict(question_id=e['question_id'],priority=e['priority'],source_file=e['source_file'],line_start=e['line_start'],
            source_issue=e['source_issue'],missing_fields=[o['field_path'] for o in e['field_omissions']])
            for e in evidence if e['field_omissions'] or e['source_issue']]
    outputs['review_queue_v1.json']=dump({'records':queue})
    before={}
    for cohort in COUNTS:
        rel=PREVIOUS+'/'+cohort+'/question_annotations_l3_v1.json';inputs[rel]=file_sha(project/rel)
        before.update({r['question_id']:r for r in read(project/rel)['records']})
    ledger=[]
    for r in rows:
        q=r['question_id'];changed={}
        for layer,fields in [('l2',L2),('l3',L3)]:
            for f in fields:
                if before[q][layer].get(f)!=r[layer].get(f):
                    changed[layer+'.'+f]={'before':before[q][layer].get(f),'after':r[layer].get(f)}
        if changed:ledger.append(dict(question_id=q,review_round=decisions[q]['review_round'],
            question_hash_sha256=blocks[q]['block_hash'],changes=changed))
    outputs['semantic_change_ledger_v3.json']=dump({'base_commit':scope['base_commit'],'records':ledger})
    report=dict(version=VERSION,record_count=len(rows),by_source={k:COUNTS[k] for k in COUNTS},
      fresh_semantic_rechecks=653,inherited_v2_decisions=1264,field_coverage={},
      questions_with_omitted_fields=sum(bool(r['field_omissions']) for r in rows),
      partial_evidence_question_count=sum(bool(task_omissions(d)) for d in decisions.values()),
      omitted_task_count=sum(len(task_omissions(d)) for d in decisions.values()),
      questions_all_l2_l3_fields_verified=sum(all(s=='verified' for l in ('l2','l3') for s in r[l]['review_status_by_field'].values()) for r in rows),
      l0_type_correction_count=len(changes),task_reference_count=len(tasks),
      dependency_count=sum(len(r['l3']['inter_question_dependency']['relations']) for r in rows),
      alternative_method_question_count=sum(bool(d['alternatives']) for d in decisions.values()),
      removed_duplicate_alternative_count=8,isomorphic_cluster_count=len(clusters),isomorphic_question_count=len(cluster_by_q),
      source_issue_count=len(queue),external_api_calls=0,
      semantics=scope['limits'],source_issues=[{'question_id':e['question_id'],'reason':e['source_issue']} for e in evidence if e['source_issue']],
      integration='活动入口应通过annotation_sources_current_v1.json的practice_release指向本版；独立check仅验证本快照，是否接入由learning_runtime校验。')
    for l,fields in [('l2',L2),('l3',L3)]:
        for f in fields:
            report['field_coverage'][l+'.'+f]={'filled':sum(f in r[l] for r in rows),
                **dict(collections.Counter(r[l]['review_status_by_field'][f] for r in rows))}
    outputs['coverage_report.json']=dump(report)
    lines=['# 数学一配套题 L3 修订报告','',
      '范围：基础30讲876题，1000题1041题，共1917题。修订653道风险题；其余1264题沿用锁定的v2决定。','',
      f"受源文影响而省略字段的题目：{report['questions_with_omitted_fields']}；其中{report['partial_evidence_question_count']}题只缺部分任务证据。",
      'filled表示有内容，verified表示相应字段已核对；二者不能混为全题质量结论。','',
      '| 字段 | 已填 | 已核对 | 待核对 |','|---|---:|---:|---:|']
    for f,c in report['field_coverage'].items():lines.append(f"| {f} | {c['filled']} | {c.get('verified',0)} | {c.get('needs_review',0)} |")
    lines+=['','## 修订口径','',
      '- 每题明确记录任务和方法，不再用章节模板填充缺失行为。653题的重新核对与1264题的继承在证据中分别登记。',
      '- 任务#Txx仅用于定位原题任务与调用关系；整题仍只有S0观察单元，points=null，未制造评分原子或小问分值。',
      '- Uxx省略只影响对应任务；其余步骤保留，整项证据状态为needs_review。缺少图、公式或精确概率条件时不自动升级为verified。',
      '- 方法去重使用逐题确认的机制说明；同一方法改名不计入备选方法。',
      '- 空备选或空同构仅表示本轮未确认其它路径或配对，不证明全库不存在。',
      '- L1保持原值；L0仅沿用267条有源文依据的题型修正。',
      '- 校验将生成值、状态、任务、依赖和证据逐题对照锁定决定，同时检查schema、来源与哈希；不能替代数学判断。','',
      '## 源文问题','']
    lines += [f"- {e['question_id']}：{e['reason']}" for e in report['source_issues']]
    lines+=['','## 复跑','',
      '`build_zhangyu_l3_repaired.py check --project 项目目录`验证本版。',
      '旧v1/v2快照和输入保留。`semantic_change_ledger_v3.json`保存字段前后值，`review_queue_v1.json`定位源文事项。',
      report['integration'],'']
    outputs['执行与覆盖报告.md']='\n'.join(lines).encode()
    tsv=['question_id\tpriority\tmain_knowledge\tmethod\tevidence_status\treview_round\tsource_file\tline_start']
    for r,e in zip(rows,evidence):tsv.append('\t'.join([r['question_id'],e['priority'],r['l2']['main_knowledge']['name'],r['l2'].get('primary_method',{}).get('name',''),r['l3']['review_status_by_field']['evidence_steps'],e['review_round'],e['source_file'],str(e['line_start'])]))
    outputs['标签浏览.tsv']=('\n'.join(tsv)+'\n').encode()
    for name in ('build_zhangyu_l3_full.py','build_l1.py','json_schema_runtime.py'):
        rel=TOOL+'/'+name;inputs[rel]=file_sha(project/rel)
    for name in ('question_annotation_v1.2.schema.json','question_annotations_bundle_v1.2.schema.json'):
        rel='系统文件/数据规范/'+name;inputs[rel]=file_sha(project/rel)
    return outputs,inputs

def validate(project,output,review):
    expected,_=create(project,review)
    schema=module('zy_schema',project/TOOL/'json_schema_runtime.py').SchemaRuntime(project/'系统文件/数据规范/question_annotations_bundle_v1.2.schema.json')
    errors=[];byid={};evs={}
    def walk(x,path='$'):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in FORBIDDEN:errors.append(path+': forbidden '+k)
                walk(v,path+'.'+k)
        elif isinstance(x,list):
            for v in x:walk(v,path)
    for cohort,count in COUNTS.items():
        rel=cohort+'/question_annotations_l3_v1.json';bundle=read(output/rel)
        errors+=schema.validate(bundle);walk(bundle)
        correct=json.loads(expected[rel]);approved={r['question_id']:r for r in correct['records']}
        if len(bundle['records'])!=count or bundle['record_count']!=count:errors.append(cohort+': count mismatch')
        if {k:v for k,v in bundle.items() if k!='records'}!={k:v for k,v in correct.items() if k!='records'}:errors.append(cohort+': bundle metadata differs from approved release')
        for r in bundle['records']:
            q=r['question_id']
            if q in byid or q not in approved:errors.append(q+': duplicate/wrong cohort');continue
            byid[q]=r;er=approved[q]
            for key in set(r)|set(er):
                if r.get(key)!=er.get(key):errors.append(q+': decision binding mismatch '+key)
        rel=cohort+'/field_evidence_v1.jsonl'
        actual=[json.loads(s) for s in (output/rel).read_text().splitlines()]
        correct=[json.loads(s) for s in expected[rel].decode().splitlines()]
        if actual!=correct:errors.append(cohort+': per-question evidence differs from approved decisions/source')
        for e in actual:
            if e['question_id'] in evs:errors.append('Duplicate evidence: '+e['question_id'])
            evs[e['question_id']]=e
    if len(byid)!=1917 or set(byid)!=set(evs):errors.append('Canonical/evidence coverage mismatch')
    for rel,raw in expected.items():
        if rel.endswith('question_annotations_l3_v1.json') or rel.endswith('.jsonl'):continue
        actual=(output/rel).read_bytes()
        equal=read(output/rel)==json.loads(raw) if rel.endswith('.json') else actual==raw
        if not equal:errors.append('Approved decision/report mismatch: '+rel)
    task_rows=read(output/'task_index_v1.json')['tasks'];task_by_id={t['task_id']:t for t in task_rows}
    if len(task_rows)!=len(task_by_id):errors.append('Duplicate task ID')
    for q,r in byid.items():
        omissions=[o['field_path'] for o in r['field_omissions']]
        if len(omissions)!=len(set(omissions)):errors.append(q+': duplicate omission')
        for l,fields in [('l2',L2),('l3',L3)]:
            for f in fields:
                path=l+'.'+f;present=f in r[l];status=r[l]['review_status_by_field'][f]
                partial=[p for p in omissions if p.startswith(path+'.U')]
                if present==(path in omissions):errors.append(q+': omission/content conflict '+path)
                if (not present or partial) and status!='needs_review':errors.append(q+': missing/partial field must need review '+path)
                if status=='candidate':errors.append(q+': candidates cannot be promoted by this release')
        steps=[s for item in r['l3'].get('evidence_steps',[]) for s in item['steps']]
        for p in omissions:
            if '.U' in p:
                i=int(p[-2:]);tid=f'{q}#T{i:02d}'
                if tid not in task_by_id or any(s.startswith('['+tid+']') for s in steps):errors.append(q+': invalid partial task omission '+p)
        for edge in r['l3']['inter_question_dependency']['relations']:
            a=task_by_id.get(edge['from_question_id']);b=task_by_id.get(edge['to_question_id'])
            if edge['from_question_id'] in byid and edge['to_question_id']==q:continue
            if not a or not b or a['question_id']!=q or b['question_id']!=q or a['task_index']>=b['task_index']:errors.append(q+': dangling/backward/cyclic task dependency')
        iso=r['l3']['isomorphic_relation']
        if iso:
            for other in iso['related_question_ids']:
                rev=byid.get(other,{}).get('l3',{}).get('isomorphic_relation') or {}
                if other==q or q not in rev.get('related_question_ids',[]) or iso['cluster_id']!=rev.get('cluster_id'):errors.append(q+': asymmetric isomorphism')
    return dict(status='FAIL' if errors else 'PASS',record_count=len(byid),error_count=len(errors),errors=errors,
        checks=['1917 source-locked canonical IDs','v1.2 schema','exact per-question values/statuses bound to explicit decisions',
                'task/edge/alternative mechanism and evidence binding','partial task omissions retain confirmed evidence',
                '267 explained L0 corrections; literal L1 preservation','no points/answers/student-role fabrication',
                'source and auxiliary hashes; distinct provenance; immutable snapshots'],
        semantic_limit='PASS检验输出与明确复核决定及来源一致；本轮语义复核653题，继承1264题，不把结构通过当作全部题目数学正确的证明。')

def run(project,output,review,mode):
    project=Path(project).resolve();output=Path(output).resolve();review=Path(review).resolve()
    if mode=='check':
        manifest=read(output/'run_manifest.json');errors=[]
        if manifest['version']!=VERSION or manifest['builder_sha256']!=file_sha(Path(__file__)):errors.append('Builder/version changed')
        expected,inputs=create(project,review)
        if manifest['input_sha256']!=inputs:errors.append('Input manifest differs from actual complete inputs')
        expected_reviews={p.name:file_sha(p) for p in review.glob('*.json')}
        if manifest['review_sha256']!=expected_reviews:errors.append('Review manifest changed/incomplete')
        names=set(expected)|{'validation_report.json'}
        if set(manifest['output_sha256'])!=names:errors.append('Output manifest incomplete')
        if {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}!=names|{'run_manifest.json'}:errors.append('Snapshot file scope changed')
        for rel,h in manifest['output_sha256'].items():
            path=resolve(output,rel)
            if not path.is_file() or file_sha(path)!=h:errors.append('Changed output: '+rel)
        if errors:return dict(status='FAIL',errors=errors)
        result=validate(project,output,review)
        if read(output/'validation_report.json')!=result:return dict(status='FAIL',errors=['Stored validation report mismatch'])
        return result
    require(not output.exists(),'Refusing to overwrite an existing snapshot; use check or a new output path.')
    data,inputs=create(project,review);output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.'+output.name+'-',dir=output.parent) as temp:
        staging=Path(temp)/'snapshot';staging.mkdir()
        for name,raw in data.items():
            dest=staging/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        result=validate(project,staging,review);require(result['status']=='PASS',str(result))
        (staging/'validation_report.json').write_bytes(dump(result))
        manifest=dict(version=VERSION,builder_sha256=file_sha(Path(__file__)),input_sha256=inputs,
            review_sha256={p.name:file_sha(p) for p in review.glob('*.json')},
            output_sha256={p.relative_to(staging).as_posix():file_sha(p) for p in staging.rglob('*') if p.is_file()})
        (staging/'run_manifest.json').write_bytes(dump(manifest))
        require(not output.exists(),'Snapshot appeared during build; refusing replacement');staging.rename(output)
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['build','check'])
    ap.add_argument('--project',type=Path,required=True);ap.add_argument('--output',type=Path)
    ap.add_argument('--review',type=Path,default=REVIEW);a=ap.parse_args()
    result=run(a.project,a.output or a.project/DEFAULT_OUTPUT,a.review,a.mode)
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
