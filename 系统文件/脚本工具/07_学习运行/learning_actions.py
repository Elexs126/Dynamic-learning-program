"""Small, evidence-based extensions to the existing daily learning loop."""
from datetime import datetime
from collections import defaultdict

import learning_runtime as lr

MAP_PATH = '系统文件/系统配置/capability_map_v1.json'
MODES = {'repair': '建立能力 / 修补缺口', 'maintenance': '混合调用 / 延迟保持',
         'exam': '考试范围 / 题型 / 时间练习'}
ERRORS = {
    'concept': ('补最少必要定义，并用代表例子确认', '能否解释条件、符号和对象分别指什么？'),
    'method': ('对比容易混淆的题，练习方法选择条件', '告诉你方法后，能否独立完成剩下步骤？'),
    'procedure': ('单练卡住的步骤，再放回完整题', '方法选定后，第一处无法独立完成的步骤是什么？'),
    'transfer': ('比较只改变关键条件的题，并检查方法失效的边界', '改变哪个条件后，原来的方法不再成立？'),
    'speed': ('定位具体耗时环节，再限时练习执行', '时间主要用在辨型、计算，还是反复检查？'),
    'retention': ('间隔后主动回忆，再做少量混合检查', '不给章节或方法提示，隔几天还能独立调用吗？'),
}


def stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def knowledge(q):
    l2 = q.get('l2') or {}
    if l2.get('main_knowledge') and l2.get('review_status_by_field', {}).get('main_knowledge') == 'verified':
        return l2['main_knowledge']['id']
    return 'scope:' + q['l1']['official_scope_coarse']


def load_map(project, records):
    path = project / MAP_PATH
    empty = {'version': 'capability-map-v1', 'mechanisms': {}, 'abilities': {}, 'questions': {}}
    if not path.exists():
        return empty
    data = lr.read(path)
    if set(data) != set(empty) or data['version'] != empty['version']:
        raise ValueError('共享能力映射版本或字段无效')
    for key in ('mechanisms', 'abilities', 'questions'):
        if not isinstance(data[key], dict):
            raise ValueError('共享能力映射必须使用对象: ' + key)
    for mid, mechanism in data['mechanisms'].items():
        if set(mechanism) != {'name', 'model', 'boundaries', 'decision_use'} or not all(
                isinstance(mechanism[k], str) and mechanism[k].strip() for k in mechanism):
            raise ValueError('共同机制需要解释、适用边界和近期决策用途: ' + mid)
    for aid, ability in data['abilities'].items():
        if (set(ability) != {'name', 'exam_track', 'mechanism_id', 'decision_use'}
                or ability['exam_track'] not in {'MATH1', 'CS408'}
                or ability['mechanism_id'] not in data['mechanisms']
                or not ability['name'] or not ability['decision_use']):
            raise ValueError('共享能力定义无效: ' + aid)
    for qid, link in data['questions'].items():
        if (qid not in records or set(link) != {'primary_ability_id', 'ability_ids', 'score_supports_primary', 'question_hash_sha256', 'basis'}
                or not isinstance(link['score_supports_primary'], bool)
                or not isinstance(link['ability_ids'], list) or not link['ability_ids']
                or len(set(link['ability_ids'])) != len(link['ability_ids'])
                or link['primary_ability_id'] not in link['ability_ids']
                or any(a not in data['abilities'] for a in link['ability_ids'])
                or any(data['abilities'][a]['exam_track'] != records[qid]['l0']['exam_track'] for a in link['ability_ids'])
                or records[qid]['l0']['question_hash_sha256'] != link['question_hash_sha256']
                or not isinstance(link['basis'], str) or not link['basis'].strip()):
            raise ValueError('共享能力题目关系未知、过期或跨科: ' + qid)
    return data


def targets(q, mapping):
    return mapping['questions'].get(q['question_id'], {}).get('ability_ids', [knowledge(q)])


def primary(q, mapping):
    return mapping['questions'].get(q['question_id'], {}).get('primary_ability_id', knowledge(q))


def aliases(records, mapping):
    # A legacy tag is an alias only when every question carrying it supports
    # the same observable ability. One checked question cannot rename a broader
    # tag, and a composite whole score cannot certify its separate parts.
    routes = defaultdict(set)
    for qid, q in records.items():
        kid = knowledge(q)
        link = mapping['questions'].get(qid)
        routes[kid].add(link['primary_ability_id'] if link and link['score_supports_primary'] else kid)
    return {kid: next(iter(ids)) for kid, ids in routes.items() if len(ids) == 1 and kid not in ids}


def observations(a, q, mapping):
    if a['schema_version'] == 'attempt-record-v1.1.0':
        return a['ability_observations']
    link = mapping['questions'].get(q['question_id'])
    aid = primary(q, mapping) if link and link['score_supports_primary'] else knowledge(q)
    return [{'ability_id': aid, 'first_score_pct': a['first_score_pct'], 'dimensions': a['dimensions'],
             'error_code': a['primary_error_code'], 'checked_error_codes': []}]


def review_queue(records, rows, mapping, cutoff, threshold):
    tasks = {}
    for a in rows:
        if a['usage_role'] not in {'TRAIN', 'AUX_OFFPOLICY'}:
            continue
        q = records[a['question_id']]
        for obs in observations(a, q, mapping):
            aid, error = obs['ability_id'], obs['error_code']
            covered = {error}
            if (obs['first_score_pct'] >= threshold and a['highest_hint_level_used'] == 'L0'
                    and not any(v in {'partial', 'fail'} for v in obs['dimensions'].values())):
                covered.update(code for code in obs['checked_error_codes'] if (aid, code) in tasks)
            for code in covered:
                key = (aid, code)
                old = tasks.get(key, {})
                tasks[key] = {'task_id': aid + (':error:' + code if code else ':general'), 'ability_id': aid,
                              'exam_track': a['exam_track'], 'error_code': code,
                              'question_ids': sorted(set(old.get('question_ids', [])) | {a['question_id']}),
                              'next_review_at': a['next_review_at'],
                              'due': stamp(a['next_review_at']) < cutoff}
    return sorted(tasks.values(), key=lambda t: (stamp(t['next_review_at']), t['task_id']))


def action_for(ability, mapping):
    error = ability.get('primary_error_code')
    dims = ability['dimensions']
    if error not in ERRORS:
        error = next((code for dim, code in [('independent_recognition', 'method'),
                    ('procedural_execution', 'procedure'), ('transfer', 'transfer'),
                    ('timed_fluency', 'speed'), ('delayed_retention', 'retention')]
                    if dims[dim] in {'partial', 'fail'}), None)
    action, probe = ERRORS.get(error, ('先补一个足以改变教学选择的短问题',
                                     '告诉你方法后，能否独立完成？若不能，卡在哪一步？'))
    info = mapping['abilities'].get(ability['knowledge_id'], {})
    return {'ability_id': ability['knowledge_id'], 'ability_name': ability['name'],
            'obstacle': error or '尚待区分', 'action': action, 'diagnostic_question': probe,
            'expected_change': '减少当前障碍，并在未练过、要求相近的题上独立完成',
            'verification': '先检查陌生题表现，再检查间隔后的混合调用；无改善时重新诊断',
            'mechanism_id': info.get('mechanism_id')}


def learning_blocks(paper, state, mapping):
    if paper['mode'] != 'repair':
        return []
    ids = list(dict.fromkeys(q['target_ability_id'] for q in paper['questions']))
    result = []
    for aid in ids:
        ability = state['abilities'].get(aid)
        if ability and not ability['weak'] and ability['stage'] == '工作掌握':
            continue
        if not ability:
            name = next(q['ability_names'][aid] for q in paper['questions'] if aid in q['ability_names'])
            ability = {'knowledge_id': aid, 'name': name,
                       'dimensions': {d: None for d in lr.DIMENSIONS}}
        item = action_for(ability, mapping)
        item['mechanism'] = mapping['mechanisms'].get(item['mechanism_id'])
        result.append(item)
    return result
