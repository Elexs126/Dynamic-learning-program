#!/usr/bin/env python3
"""Source-locked, local practice-question L3 annotations.

Individually reviewed decisions and rule-generated candidates are deliberately
separate. No rule or chapter route can produce a verified semantic field.
"""
from __future__ import annotations
import argparse
import collections
import copy
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
VERSION = 'zhangyu-practice-l3-v1.0.0'
TOOL = '系统文件/脚本工具/05_标注与规范校验'
DEFAULT_OUTPUT = '系统文件/题目标注/数学一配套题_L3_20260929_v1'
REVIEW = Path(__file__).with_name('zhangyu_l3_review_v1')
BASE = '系统文件/题目标注/L1_L3衔接_20260910_v1/L1/question_annotations_l1_v1.json'
L2 = ('main_knowledge','assessed_construct','secondary_knowledge','primary_method','prerequisites','difficulty_band')
L3 = ('score_units','score_attribution','evidence_steps','alternative_methods','inter_question_dependency','isomorphic_relation')
COUNTS = {'zy30':876,'zy1000':1041}
FORBIDDEN = {'answer','solution','reference_answer','reference_solution','student_answer','student_score',
             'data_role','practice_role','usage_role','candidate_main_ability','audited_main_ability'}

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def dump(x): return (json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
def sha(x): return hashlib.sha256(x).hexdigest()
def file_sha(p): return sha(Path(p).read_bytes())
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def require(ok,message):
    if not ok: raise ValueError(message)
def book(q): return 'zy30' if q.startswith('ZY30-') else 'zy1000'
def resolve(root,relative):
    result=(root/relative).resolve()
    require(result.is_relative_to(root.resolve()),'Path outside project: '+str(relative))
    return result

def inventory(project, review):
    parser=module('zy_local_parser',project/TOOL/'build_l1.py')
    base={r['question_id']:r for r in read(project/BASE)['records']
          if r['l0']['source_file'].startswith(('配套习题/张宇基础30讲/','配套习题/张宇1000题/'))}
    require(collections.Counter(book(q) for q in base)==COUNTS,'Practice source count mismatch')
    blocks={}; inputs={BASE:file_sha(project/BASE)}
    for rel in sorted({r['l0']['source_file'] for r in base.values()}):
        path=resolve(project,rel);text=path.read_text(encoding='utf-8');inputs[rel]=file_sha(path)
        for b in parser.parse_file(text,rel):
            q=b['question_id'];require(q not in blocks,'Duplicate source id: '+q)
            require(q in base and base[q]['l0']['question_hash_sha256']==b['block_hash'],'L1 source drift: '+q)
            b['source_file']=rel; blocks[q]=b
            for image in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',b['body']):
                image=image.split(' "')[0].strip('<>')
                p=(path.parent/image).resolve()
                require(p.is_relative_to(project.resolve()),'External image path')
                if p.is_file():inputs[p.relative_to(project).as_posix()]=file_sha(p)
    require(set(blocks)==set(base),'Canonical ID coverage mismatch')
    lock=read(review/'source_lock_v1.json')
    require(lock['source_files']=={k:v for k,v in inputs.items() if k!=BASE},'Locked source or image changed')
    require(lock['l1_sha256']==inputs[BASE],'Base L1 snapshot changed')
    require(lock['question_hashes']=={q:b['block_hash'] for q,b in blocks.items()},'Question lock changed')
    return base,blocks,inputs

def statement(body):
    # Options are alternatives, never affirmative semantic evidence.
    return re.split(r'(?m)^\s*-?\s*\*\*A[.．、]|^\s*[（(]A[）)]|(?<![A-Za-z])A[.．、]\s',body,maxsplit=1)[0]

def chapter(q):
    m=re.search(r'-(GS|XD|GL)-?(\d{2})-',q)
    return (m.group(1),int(m.group(2))) if m else ('',-1)

def select_profile(q, body, area, profiles):
    """Return a grounded *candidate*. No chapter-only fallback is emitted."""
    s=statement(body); compact=re.sub(r'\s+','',s)
    course,ch=chapter(q)
    # Ordered task rules. Each stores its literal matched evidence separately.
    rules=[]
    def rule(p,regex): rules.append((p,regex))
    if area=='calculus':
        for p,pat in [('ode_model' if ch==15 else 'rate','变化率|变化速度'),('centroid','形心|质心|重心'),
                      ('div_curl',r'rot|div'),('arc_length','弧的长度')]:rule(p,pat)
        for p,pat in [
            ('path_independent','路径无关'),('div_curl','散度|旋度'),('fourier','傅里叶|Fourier'),
            ('power_radius','收敛域|收敛半径|收敛区间'),('series_sum','和函数|级数的和'),
            ('series_expand','展开为.*级数|展开成.*级数'),('direction','方向导数|梯度'),
            ('ode_exact','全微分方程'),('ode_euler','欧拉方程'),
            ('inverse','反函数'),('discontinuity','间断点'),('asymptote','渐近线'),
            ('arc_length','弧长'),('integral_volume','旋转体|体积'),
            ('work_integral','做功|功为|压力|引力|做.*功'),('convex','拐点|凹凸'),
            ('higher_deriv','高阶导数|[nN0-9}]+\\$?阶导数'),
            ('limit_local','同阶|高阶无穷小|等价无穷小|泰勒'),
            ('limit_side','左极限|右极限'),('limit_sign','保号'),
            ('floor','取整|最大整数'),('period','周期'),('parity','奇函数|偶函数|奇偶'),
        ]:rule(p,pat)
        if course=='GS' and ch==15:
            for p,pat in [('ode_model','曲线|温度|速度|变化率|轨迹|斜率'),
                          ('integral_equation',r'\\int|\\iint'),
                          ('ode_nonhom','非齐次'),('ode_hom','齐次线性'),
                          ('ode_first','一阶线性'),('ode_separable','分离变量')]:rule(p,pat)
            rule('ode_general',r'微分方程|通解|特解')
        if course=='GS' and ch==16:
            rule('series_converge',r'级数|收敛|发散|敛散|\\sum')
        if course=='GS' and ch==13:
            rule('lagrange','条件极值|约束|条件下')
            rule('multivar_ext','极值|最大值|最小值')
            rule('multivar_cont',r'可微|连续性|极限|\\lim')
            rule('partial',r'偏导|全微分|可导|\\partial|∂|f\s*[_′\']')
        if course=='GS' and ch in (17,):
            rule('space_line','平面|直线')
            rule('space_surface','曲面|投影')
        for p,pat in [
            ('surface_integral',r'曲面积分|\\iint_\{?\\(?:Sigma|varSigma|Omega|Pi|partial)'),
            ('line_integral',r'曲线积分|\\oint|\\int_\{?L'),
            ('triple_integral',r'三重积分|\\iiint'),('double_integral',r'二重积分|\\iint'),
            ('lagrange','条件极值'),('partial','偏导|全微分'),
            ('integral_improper','反常积分|广义积分'),('integral_area','面积'),
            ('integral_variable','变限积分|变上限'),('integral_primitive','不定积分|原函数'),
            ('integral_definite','定积分'),('max_one','最大值|最小值|最值|极值|极大值|极小值'),
            ('tangent','切线|法线'),('bound','有界'),
            ('monotone','单调'),('function_expr','表达式|解析式'),
        ]:rule(p,pat)
        if ch==2:rule('sequence',r'数列|x_n|a_n|n\s*\\to|n\s*\\rightarrow|n\s*→|lim')
        if ch in (3,4):
            rule('deriv_def','可导|导数定义')
            rule('deriv_calc',r'导数|微分|f\^?\{?\(?[′\']|y\s*\x27|dy|dx')
        if ch in (6,11):
            rule('integral_inequality' if ch==11 else 'mean_value','证明|证:|证：|中值定理')
        if ch in (8,9):rule('integral_primitive' if re.search(r'\\int\s*(?!_)',s) else 'integral_definite',r'积分|\\int')
        rule('limit_general',r'极限|\\lim|\blim')
        rule('continuity','连续性|处连续|连续的|连续，则|连续,则')
        if ch==14 and len(re.findall(r'\\int',s))>=2:rule('double_integral',r'\\int')
    elif area=='linear_algebra':
        for p,pat in [
            ('positive','正定|负定'),('quadratic','二次型|合同'),('adjugate','伴随'),
            ('det_cofactor','余子式'),('orthogonal','正交'),('similar','相似|对角化'),
            ('eigen','特征值|特征向量'),('basis','极大无关组|一组基|一组标准正交基'),
            ('vector_rep','线性表示|线性表出'),('vector_equiv','向量组.*等价|初等列变换'),('linear_dependence','线性相关|线性无关'),
            ('hom_system','齐次线性方程组'),('linear_system','线性方程组|基础解系|通解'),
            ('inverse_matrix','逆矩阵|可逆'),('matrix_rank','矩阵的秩|秩为|的秩|r\\('),
            ('det_polynomial','多项式|二重根'),('det_compute',r'行列式|\\begin\{vmatrix\}'),
            ('matrix_ops',r'矩阵|\\begin\{[bp]matrix\}')]:rule(p,pat)
    else:
        for p,pat in [
            ('mle','最大似然'),('moment_est','矩估计'),('confidence','置信'),
            ('unbiased','无偏|有效性|均方误差'),('hypothesis','假设|拒绝域'),
            ('clt','中心极限|近似'),('lln','大数|依概率'),('correlation','相关系数'),
            ('conditional_dist','条件分布|条件密度'),('joint_dist','联合|边缘'),
        ]:rule(p,pat)
        if ch==1:
            for p,pat in [('independence','两两独立|相互独立'),('bernoulli','独立重复|射击'),
                          ('conditional',r'条件概率|\\mid'),('bayes','贝叶斯'),
                          ('geometric','随机地取|均匀落|投掷一点'),('classical','任取|袋|球|骰子|信封'),
                          ('total_prob','两箱|两批'),('prob_axioms',r'P\('),('event_algebra','事件')]:rule(p,pat)
        else:
            for p,pat in [('sample_dist','统计量|自由度'),('variance',r'方差|协方差|D\('),
                          ('expectation',r'期望|E\('),('transform_dist','函数的分布|求.*的分布'),
                          ('density','密度'),('distribution','分布函数|分布律'),
                          ('rv_independent','独立'),('sample_dist','样本'),
                          ('common_dist',r'泊松|指数分布|正态分布|二项分布|\\sim\s*[NBEPG]\(')]:rule(p,pat)
    for key,pattern in rules:
        m=re.search(pattern,s,re.S)
        if m:
            return key, {'pattern':pattern,'matched_text':m.group(0)[:120],
                         'statement_start':m.start(),'statement_end':m.end(),
                         'basis':'题干文字/公式线索触发的候选，尚未逐题核对；选项和章节标题不作肯定证据。'}
    return None, None

def quality(body):
    issues=[]
    if '![' in body:issues.append('IMAGE_REQUIRES_VISUAL_REVIEW')
    if len(re.sub(r'\s+','',body))<15:issues.append('SHORT_STEM_REQUIRES_REVIEW')
    if '�' in body:issues.append('OCR_REPLACEMENT_CHARACTER')
    if '$' not in body and re.search(r'[a-zA-Z]\)|[a-zA-Z]\d|\b(?:lim|sin|cos)\b',body):
        issues.append('UNSTRUCTURED_FORMULA_REQUIRES_REVIEW')
    return issues

def changed_type(r,body):
    if r['l0']['question_type']=='choice':return None
    if re.search(r'\\underline\s*\{\s*\\hspace|_{3,}|[＿]{2,}',body):return 'fill'
    return None

def create(project, review):
    base,blocks,inputs=inventory(project,review)
    profiles=read(review/'profiles_v1.json'); decisions=read(review/'semantic_reviews_v1.json')
    clusters=read(review/'isomorphic_clusters_v1.json'); cluster_by_q={}
    for c in clusters:
        for q in c['question_ids']:
            require(q not in cluster_by_q and q in decisions,'Invalid reviewed cluster membership')
            cluster_by_q[q]=c
    registry={'knowledge':{},'methods':{}}
    def ref(name,kind='knowledge'):
        prefix='M1_K_' if kind=='knowledge' else 'M1_METHOD_'
        ident=prefix+sha(name.encode())[:16]
        registry[kind][ident]={'id':ident,'name':name}
        return registry[kind][ident].copy()
    rows=[]; evidence=[]; changes=[]; queue=[]; tasks=[]
    # Preserve the user's processing priority explicitly, independent of lexicographic IDs.
    for q in sorted(base,key=lambda q:(0 if q.startswith('ZY30-') else 1,blocks[q]['source_file'],blocks[q]['line_start'])):
        b=blocks[q];r=copy.deepcopy(base[q]);d=decisions.get(q)
        if d: require(d['question_hash_sha256']==b['block_hash'],'Semantic review is stale: '+q)
        key,match=(d['profile'],None) if d else select_profile(q,b['body'],r['l0']['subject_area'],profiles)
        p=copy.deepcopy(profiles[key]) if key else None
        if p and d:
            for k in ('main','method','steps','hard'):
                if k in d:p[k]=d[k]
        flags=quality(b['body'])
        typ=changed_type(r,b['body'])
        if typ and typ!=r['l0']['question_type']:
            changes.append({'question_id':q,'field':'l0.question_type','before':r['l0']['question_type'],
                            'after':typ,'basis':'题干有明确填空占位符；选择题优先规则已应用。',
                            'source_file':b['source_file'],'line_start':b['line_start'],'question_hash_sha256':b['block_hash']})
            r['l0']['question_type']=typ
            r['l0']['review_status_by_field']['question_type']='verified'
        r.update(schema_version='question-annotation-v1.2.0',annotation_depth='L3',record_status='needs_review',field_omissions=[])
        r['review_flags']=sorted(set(r['review_flags']+flags+['NO_LOCAL_SOLUTION_OR_OFFICIAL_RUBRIC',
              'TEXTBOOK_POINTS_NOT_APPLICABLE']+([] if d else ['SEMANTIC_RULE_CANDIDATE_NOT_REVIEWED'])))
        layers={name:{'review_status_by_field':{f:'needs_review' for f in fields},
                      'confidence_by_field':{f:'unknown' for f in fields}}
                for name,fields in [('l2',L2),('l3',L3)]}
        def put(layer,field,value,status='verified',confidence='high'):
            layers[layer][field]=value
            layers[layer]['review_status_by_field'][field]=status
            layers[layer]['confidence_by_field'][field]=confidence
        def omit(layer,field,reason,reason_type='human_review_needed'):
            layers[layer].pop(field,None)
            layers[layer]['review_status_by_field'][field]='needs_review'
            layers[layer]['confidence_by_field'][field]='unknown'
            r['field_omissions'].append(dict(field_path=layer+'.'+field,reason=reason,reason_type=reason_type))
        unit=q+':S0'
        put('l3','score_units',[dict(unit_id=unit,points=None,point_status='not_applicable',
            description='教辅整题观察单元；原题无试卷分值，未制造小问或步骤分值。',
            source_evidence=f"{b['source_file']}#{q}；L0分值状态为not_applicable。",confidence='high')])
        if p:
            status='verified' if d else 'candidate'; conf='medium' if d else ('low' if flags else 'medium')
            main=ref(p['main'])
            put('l2','main_knowledge',main,status,conf)
            put('l2','assessed_construct','能'+'；并能'.join(p['steps'])+'。',status,conf)
            put('l2','primary_method',ref(p['method'],'methods'),status,conf)
            put('l2','prerequisites',dict(hard_prerequisite=[ref(x) for x in p['hard']],soft_prerequisite=[]),status,conf)
            if d:
                put('l2','secondary_knowledge',[ref(x) for x in d.get('secondary',[])],'verified','medium')
                put('l2','difficulty_band',d['difficulty_band'],'verified','medium')
            else:
                omit('l2','secondary_knowledge','候选规则不能判定哪些附带内容参与关键推理，待逐题判断。')
                omit('l2','difficulty_band','未逐题核对计算链、隐藏辨型及边界处理；不按来源或章节猜难度。')
            targets=[main]+layers['l2'].get('secondary_knowledge',[])
            put('l3','score_attribution',[dict(unit_id=unit,category='integrated_target' if len(targets)>1 else 'main_knowledge',
                target_knowledge_ids=[x['id'] for x in targets],status=status)],status,conf)
            put('l3','evidence_steps',[dict(unit_id=unit,steps=p['steps'],
                basis=f"{b['source_file']}#{q}；"+('已逐题核对题干中的任务与方法，记录可观察行为；无数值评分细则。' if d else
                '由题干线索匹配的候选行为模板；未经逐题核对，不作为正式阅卷标准。'))],status,conf)
        else:
            for f in L2:
                omit('l2',f,'题干未命中足以生成细粒度候选的规则；未用原章节冒充正式知识或教学标签。')
            for f in ('score_attribution','evidence_steps'):
                omit('l3',f,'未确认本题的具体任务与解法，不能生成可靠的评分目标或可观察步骤。')
        # Not checked is not equivalent to a confirmed absence.
        if d and d.get('alternatives'):
            put('l3','alternative_methods',[dict(ref(a['name'],'methods'),conditions=a['conditions']) for a in d['alternatives']],
                'verified','medium')
        else:
            omit('l3','alternative_methods','无本地解析；本题尚未完成独立的备选解法适用性核对。')
        if d:
            local=[] if 'l3.evidence_steps' in d.get('blocked',[]) else d.get('tasks',[p['steps']])
            for i,steps in enumerate(local,1):
                tasks.append(dict(task_id=f'{q}#T{i:02d}',question_id=q,task_index=i,
                                  description='；'.join(steps),kind='reasoning_reference_not_scoring_atom'))
            deps=[dict(from_question_id=f'{q}#T{a:02d}',to_question_id=f'{q}#T{b:02d}',
                       description='本轮所记录方法中后项调用前项得到的对象或结果；任务引用不是新增评分原子。',status='verified')
                  for a,b in d.get('dependencies',[])]
            put('l3','inter_question_dependency',dict(relations=deps,unresolved_legacy_note=None),'verified','high')
            if d.get('tasks'):
                layers['l3']['evidence_steps'][0]['steps']=[f'[{q}#T{i:02d}] {s}' for i,ss in enumerate(local,1) for s in ss]
        else:
            omit('l3','inter_question_dependency','尚未逐题核对是否直接调用另一具体题目的结果；章节先后不是题间依赖。')
        if q in cluster_by_q:
            c=cluster_by_q[q]
            put('l3','isomorphic_relation',{**{k:v for k,v in c.items() if k!='question_ids'},
                    'related_question_ids':[i for i in c['question_ids'] if i!=q]},'verified','medium')
        else:
            omit('l3','isomorphic_relation','未逐对比较并确认结构不变量；同章节或同知识点不自动组成同构簇。')
        if d:
            for path in d.get('blocked',[]):
                layer,field=path.split('.')
                # Replace an earlier omission, if any, without duplicate paths.
                r['field_omissions']=[o for o in r['field_omissions'] if o['field_path']!=path]
                omit(layer,field,d['source_issue'])
            if d.get('source_issue'): r['review_flags'].append('SOURCE_SEMANTIC_ISSUE')
        r['l2']=layers['l2'];r['l3']=layers['l3']
        # L1 remains a literal preserved historical candidate. Consumers must use field states.
        ev=dict(question_id=q,source_file=b['source_file'],source_locator=q,
            question_hash_sha256=b['block_hash'],statement_sha256=sha(b['body'].encode()),
            line_start=b['line_start'],line_end=b['line_end'],
            priority='CORE_L2' if book(q)=='zy30' else 'L1_FIRST',
            reviewer_kind='assistant_offline_semantic_review' if d else 'deterministic_candidate_generation',
            human_review_performed=False,profile_id=key,candidate_rule_match=match,
            source_issue=(d or {}).get('source_issue'),quality_flags=flags,
            field_status={layer:layers[layer]['review_status_by_field'] for layer in ('l2','l3')},
            field_omissions=r['field_omissions'])
        evidence.append(ev);rows.append(r)
        queue.append(dict(question_id=q,priority=ev['priority'],source_file=b['source_file'],line_start=b['line_start'],
                          semantic_review_performed=bool(d),source_issue=ev['source_issue'],
                          candidate_fields=[f'{l}.{f}' for l in ('l2','l3') for f,s in layers[l]['review_status_by_field'].items() if s=='candidate'],
                          missing_fields=[o['field_path'] for o in r['field_omissions']],quality_flags=flags))
    outputs={}
    for key in COUNTS:
        selected=[r for r in rows if book(r['question_id'])==key]
        bundle=dict(schema_version='question-annotations-bundle-v1.2.0',generated_at='2026-09-29T00:00:00+08:00',
                    source_file=BASE,source_schema_version='question-annotations-bundle-v1.0.0',
                    record_count=len(selected),records=selected)
        outputs[key+'/question_annotations_l3_v1.json']=dump(bundle)
        outputs[key+'/field_evidence_v1.jsonl']=''.join(json.dumps(e,ensure_ascii=False,sort_keys=True)+'\n' for e in evidence if book(e['question_id'])==key).encode()
    outputs['label_registry_v1.json']=dump({k:list(v.values()) for k,v in registry.items()})
    outputs['task_index_v1.json']=dump(dict(tasks=tasks))
    outputs['isomorphic_clusters_v1.json']=dump(dict(clusters=clusters))
    outputs['l0_type_corrections_v1.json']=dump(dict(changes=changes))
    outputs['review_queue_v1.json']=dump(dict(records=queue))
    report=dict(version=VERSION,record_count=len(rows),by_source={},field_coverage={},
                l0_type_correction_count=len(changes),isomorphic_cluster_count=len(clusters),
                isomorphic_question_count=len(cluster_by_q),external_api_calls=0,
                semantics=f'{len(decisions)}题有逐题语义核对输入，其余是明确标识的规则候选或字段留空；L3深度不代表精标完成。',
                alternative_method_question_count=sum(bool(r['l3'].get('alternative_methods')) for r in rows),
                dependency_count=sum(len(r['l3'].get('inter_question_dependency',{}).get('relations',[])) for r in rows),
                task_reference_count=len(tasks),
                official_points='全部1917题points=null，point_status=not_applicable；不设小问分值。',
                source_issues=[dict(question_id=e['question_id'],reason=e['source_issue']) for e in evidence if e['source_issue']],
                integration='独立增量批次；活动L1/L3发布与学习运行入口尚未切换。')
    for key in COUNTS:
        sr=[r for r in rows if book(r['question_id'])==key]
        report['by_source'][key]=dict(records=len(sr),individual_semantic_reviews=sum(q['question_id'] in decisions for q in sr),
             candidate_profiles=sum(r['l2']['review_status_by_field']['main_knowledge']=='candidate' for r in sr),
             no_profile=sum('main_knowledge' not in r['l2'] for r in sr))
    for layer,fields in [('l2',L2),('l3',L3)]:
        for f in fields:
            report['field_coverage'][layer+'.'+f]={'filled':sum(f in r[layer] for r in rows),
                **dict(collections.Counter(r[layer]['review_status_by_field'][f] for r in rows))}
    outputs['coverage_report.json']=dump(report)
    lines=['# 数学一配套题 L3 初标与复核报告','',
           '范围：张宇基础30讲876题（CORE_L2优先），张宇1000题1041题（L1_FIRST），共1917题。',
           '', '本批次已处理全部题号，完成逐题来源绑定、教辅整题观察单元及候选标签。',
           report['semantics'],'',
           '| 来源 | 记录 | 逐题语义核对 | 规则候选主标签 | 无可靠候选主标签 |',
           '|---|---:|---:|---:|---:|']
    for k,v in report['by_source'].items():lines.append(f"| {k} | {v['records']} | {v['individual_semantic_reviews']} | {v['candidate_profiles']} | {v['no_profile']} |")
    lines+=['','## 字段状态','', '| 字段 | 已填 | 已核对 | 候选 | 待复核/缺失 |','|---|---:|---:|---:|---:|']
    for f,v in report['field_coverage'].items():lines.append(f"| {f} | {v['filled']} | {v.get('verified',0)} | {v.get('candidate',0)} | {v.get('needs_review',0)} |")
    lines+=['','## 判读规则','',
       '- verified：本轮有逐题语义核对输入，或可机械核对的分值/来源事实；不等于人工签核。',
       '- candidate：只由题干线索匹配，尚未逐题验证，不能作为正式评分或硬前置阻断依据。',
       '- needs_review：未知或源文问题；缺失字段有原因，不能当作不存在或不适用。',
       '- 原题均无本地解析。只保存知识、方法骨架和可观察行为，不写答案或完整解答。',
       '- L0/L1保留原记录；仅对明确填空占位符造成的旧题型误判作有日志的L0修正。',
       '- 每题保留一个整题观察单元，无数值分值；它不证明题目已完成最小评分原子化。',
       '- 未检查的备选解法、题间依赖和同构关系均保持待复核。空次知识/软前置仅表示本轮未确认额外项目。',
       '- 本轮只确认4个具体同构簇；未按章节或共同关键词批量建立关系。',
       '', '## 源文待核对事项','']
    lines += [f"- {v['question_id']}：{v['reason']}" for v in report['source_issues']]
    lines += ['', '## 文件与复跑','',
       '- zy30/、zy1000/：累积L0—L3 JSON与每题证据。',
       '- review_queue_v1.json：按用户优先级排列的后续复核字段；候选也明确入队。',
       '- l0_type_corrections_v1.json：题型修正的前后值及题干位置。',
       '- coverage_report.json、validation_report.json、run_manifest.json：覆盖、结构/来源检查和哈希。',
       '- 规范v1.2只新增教辅score_unit.point_status=not_applicable，不覆盖旧规范。',
       '- build_zhangyu_l3.py check --project 项目目录：核验来源、输入、输出及字段语义约束。',
       '', report['integration'],
       '尚未完成：其余题目的逐题语义精标、完整备选解法审查、题内任务依赖和全范围同构配对。不能将本批次描述为1917题全部L3精标完成。','']
    outputs['执行与覆盖报告.md']='\n'.join(lines).encode()
    tsv=['question_id\tpriority\tmain_knowledge\tmain_status\tmethod\tevidence_status\tsource_file\tline_start']
    for r,e in zip(rows,evidence):
        tsv.append('\t'.join([r['question_id'],e['priority'],r['l2'].get('main_knowledge',{}).get('name',''),
            r['l2']['review_status_by_field']['main_knowledge'],r['l2'].get('primary_method',{}).get('name',''),
            r['l3']['review_status_by_field']['evidence_steps'],e['source_file'],str(e['line_start'])]))
    outputs['标签浏览.tsv']=('\n'.join(tsv)+'\n').encode()
    for name in ('build_l1.py','json_schema_runtime.py'):
        rel=TOOL+'/'+name;inputs[rel]=file_sha(project/rel)
    return outputs,inputs

def validate(project,output,review):
    base,blocks,_=inventory(project,review)
    schema=module('zy_schema',project/TOOL/'json_schema_runtime.py').SchemaRuntime(project/'系统文件/数据规范/question_annotations_bundle_v1.2.schema.json')
    decisions=read(review/'semantic_reviews_v1.json');registry=read(output/'label_registry_v1.json')
    task_rows=read(output/'task_index_v1.json')['tasks'];task_by_id={t['task_id']:t for t in task_rows}
    refs={x['id']:x['name'] for k in registry for x in registry[k]}
    errors=[];byid={};evs={};changes={r['question_id']:r for r in read(output/'l0_type_corrections_v1.json')['changes']}
    if len(task_by_id)!=len(task_rows):errors.append('Duplicate task ID')
    def walk(x,path='$'):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in FORBIDDEN:errors.append(path+': forbidden '+k)
                walk(v,path+'.'+k)
        elif isinstance(x,list):
            for v in x:walk(v,path)
    for key,count in COUNTS.items():
        b=read(output/key/'question_annotations_l3_v1.json');errors+=schema.validate(b);walk(b)
        if len(b['records'])!=count or b['record_count']!=count:errors.append(key+': count mismatch')
        for r in b['records']:
            q=r['question_id']
            if q in byid or book(q)!=key:errors.append(q+': duplicate/wrong cohort')
            byid[q]=r
        for line in (output/key/'field_evidence_v1.jsonl').read_text().splitlines():
            e=json.loads(line);q=e['question_id']
            if q in evs:errors.append(q+': duplicate evidence')
            evs[q]=e
    if set(byid)!=set(base) or set(evs)!=set(base):errors.append('Canonical/evidence coverage mismatch')
    for q,r in byid.items():
        if q not in base:continue
        expected=copy.deepcopy(base[q]['l0'])
        if q in changes:
            c=changes[q]
            if c['before']!=expected['question_type'] or c['after']!=changed_type(base[q],blocks[q]['body']):errors.append(q+': invalid type correction')
            expected['question_type']=c['after'];expected['review_status_by_field']['question_type']='verified'
        if r['l0']!=expected or r['l1']!=base[q]['l1']:errors.append(q+': cumulative layer changed without evidence')
        e=evs[q]
        if e['question_hash_sha256']!=blocks[q]['block_hash']:errors.append(q+': stale evidence')
        if e['line_start']!=blocks[q]['line_start'] or e['line_end']!=blocks[q]['line_end']:errors.append(q+': evidence lines changed')
        if (q in decisions)!=(e['reviewer_kind']=='assistant_offline_semantic_review'):errors.append(q+': fabricated reviewer')
        om=[o['field_path'] for o in r['field_omissions']]
        if len(om)!=len(set(om)):errors.append(q+': duplicate omission')
        if not set(om)<={l+'.'+f for l,fields in [('l2',L2),('l3',L3)] for f in fields}:errors.append(q+': invalid omission path')
        for layer,fields in [('l2',L2),('l3',L3)]:
            for f in fields:
                present=f in r[layer];status=r[layer]['review_status_by_field'][f];path=layer+'.'+f
                if present==(path in om):errors.append(q+': omission/content conflict '+path)
                if not present and status!='needs_review':errors.append(q+': missing field status '+path)
                if status=='verified' and q not in decisions and path!='l3.score_units':errors.append(q+': unreviewed semantic verification '+path)
        us=r['l3']['score_units']
        if len(us)!=1 or us[0]['unit_id']!=q+':S0' or us[0]['points'] is not None or us[0]['point_status']!='not_applicable':errors.append(q+': fabricated points/units')
        for v in r['l3'].get('score_attribution',[])+r['l3'].get('evidence_steps',[]):
            if v['unit_id']!=q+':S0':errors.append(q+': dangling score unit')
        if 'main_knowledge' in r['l2']:
            rr=[r['l2']['main_knowledge']]+r['l2'].get('secondary_knowledge',[])
            rr+=r['l2'].get('prerequisites',{}).get('hard_prerequisite',[])
            rr+=r['l2'].get('prerequisites',{}).get('soft_prerequisite',[])
            if 'primary_method' in r['l2']:rr.append(r['l2']['primary_method'])
            rr+=r['l3'].get('alternative_methods',[])
            if any(refs.get(a['id'])!=a['name'] for a in rr):errors.append(q+': bad label ref')
        for a in r['l3'].get('score_attribution',[]):
            if not set(a['target_knowledge_ids'])<=refs.keys():errors.append(q+': dangling attribution')
        for dep in r['l3'].get('inter_question_dependency',{}).get('relations',[]):
            a=task_by_id.get(dep['from_question_id']);b=task_by_id.get(dep['to_question_id'])
            if not a or not b or a['question_id']!=q or b['question_id']!=q or a['task_index']>=b['task_index']:
                errors.append(q+': dangling/backward/cyclic task dependency')
        iso=r['l3'].get('isomorphic_relation')
        if iso:
            for other in iso['related_question_ids']:
                rev=byid.get(other,{}).get('l3',{}).get('isomorphic_relation',{})
                if other==q or q not in rev.get('related_question_ids',[]) or iso['cluster_id']!=rev.get('cluster_id'):errors.append(q+': asymmetric isomorphism')
                if other in r['l1']['duplicate_candidate']['possible_duplicate_ids']:errors.append(q+': duplicate used as isomorphism')
    return dict(status='FAIL' if errors else 'PASS',record_count=len(byid),error_count=len(errors),errors=errors,
                checks=['1917 canonical IDs','v1.2 schema','source and question hashes','source-bound semantic review inputs',
                        'rule candidates never promoted to verified','L0 changes explained and L1 preserved',
                        'no invented points or scoring atomization','complete omission reasons','registered label references',
                        'reciprocal reviewed isomorphism','no answer/student/role payload'],
                semantic_limit='PASS只证明结构、来源及声明一致性，不将规则候选认定为逐题语义审核通过。')

def run(project,output,review,mode):
    project=Path(project).resolve();output=Path(output).resolve();review=Path(review).resolve()
    if mode=='check':
        manifest=read(output/'run_manifest.json');errors=[]
        if file_sha(Path(__file__))!=manifest['builder_sha256']:errors.append('Builder changed')
        for root,key in [(project,'input_sha256'),(output,'output_sha256')]:
            for rel,h in manifest[key].items():
                p=resolve(root,rel)
                if not p.is_file() or file_sha(p)!=h:errors.append('Changed input/output: '+rel)
        for rel,h in manifest['review_sha256'].items():
            p=resolve(review,rel)
            if not p.is_file() or file_sha(p)!=h:errors.append('Changed review: '+rel)
        if errors:return dict(status='FAIL',errors=errors)
        return validate(project,output,review)
    require(not output.exists(),'Refusing to overwrite an existing snapshot; use check or a new output path.')
    data,inputs=create(project,review)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.'+output.name+'-',dir=output.parent) as temp:
        staging=Path(temp)/'snapshot';staging.mkdir()
        for name,raw in data.items():
            dest=staging/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        result=validate(project,staging,review)
        (staging/'validation_report.json').write_bytes(dump(result));require(result['status']=='PASS',str(result))
        for name in ('question_annotation_v1.2.schema.json','question_annotations_bundle_v1.2.schema.json'):
            rel='系统文件/数据规范/'+name;inputs[rel]=file_sha(project/rel)
        hashes={p.relative_to(staging).as_posix():file_sha(p) for p in staging.rglob('*') if p.is_file()}
        manifest=dict(version=VERSION,builder_sha256=file_sha(Path(__file__)),input_sha256=inputs,
                      review_sha256={p.relative_to(review).as_posix():file_sha(p) for p in review.glob('*.json')},output_sha256=hashes)
        (staging/'run_manifest.json').write_bytes(dump(manifest))
        require(not output.exists(),'Snapshot appeared during build; refusing replacement')
        staging.rename(output)
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['build','check'])
    ap.add_argument('--project',type=Path,required=True);ap.add_argument('--output',type=Path)
    ap.add_argument('--review',type=Path,default=REVIEW);args=ap.parse_args()
    result=run(args.project,args.output or args.project/DEFAULT_OUTPUT,args.review,args.mode)
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
