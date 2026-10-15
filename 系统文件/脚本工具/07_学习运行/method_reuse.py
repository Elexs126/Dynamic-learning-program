"""On-demand method relationships, separate from knowledge and learner state.

Checked means a source-grounded applicability review, not mathematical proof,
personal mastery, a scoring guarantee or global optimality. No answer keys.
"""
from collections import defaultdict
import re

import learning_runtime as lr
import learning_actions as la

LIBRARY_PATH = '系统文件/系统配置/method_reuse_v1.json'
VERSION = 'method-reuse-v1'


def load_library(project, records):
    empty = {'version': VERSION, 'methods': {}, 'links': []}
    path = project / LIBRARY_PATH
    if not path.exists():
        return empty
    data = lr.read(path)
    if (not isinstance(data, dict) or set(data) != set(empty) or data['version'] != VERSION
            or not isinstance(data['methods'], dict) or not isinstance(data['links'], list)):
        raise ValueError('方法复用库版本或结构无效')
    fields = {'name', 'exam_track', 'principle', 'conditions', 'boundaries', 'decision_use'}
    for mid, method in data['methods'].items():
        if (not mid or not isinstance(method, dict) or set(method) != fields
                or any(not isinstance(v, str) or not v.strip() for v in method.values())
                or method['exam_track'] not in {'MATH1', 'CS408'}):
            raise ValueError('方法需要原理、适用条件、边界和近期用途: ' + mid)
    seen = set()
    for link in data['links']:
        if (not isinstance(link, dict) or set(link) != {'question_id', 'method_id',
                'question_hash_sha256', 'status', 'extent', 'basis'}
                or any(not isinstance(v, str) or not v.strip() for v in link.values())):
            raise ValueError('题目与方法关系字段无效')
        qid, mid = link['question_id'], link['method_id']
        if (qid not in records or mid not in data['methods'] or (qid, mid) in seen
                or data['methods'][mid]['exam_track'] != records[qid]['l0']['exam_track']
                or link['status'] not in {'candidate', 'checked', 'rejected'}
                or link['extent'] not in {'step', 'whole'}
                or not re.fullmatch('[0-9a-f]{64}', link['question_hash_sha256'])):
            raise ValueError('方法关系未知、重复或跨科: ' + qid + '/' + mid)
        seen.add((qid, mid))
    return data


def effective_status(link, records):
    q = records.get(link['question_id'])
    if q is None or q['l0']['question_hash_sha256'] != link['question_hash_sha256']:
        return 'stale'
    return link['status']


def checked_index(library, records):
    """Only checked, unchanged applicability may affect a training choice."""
    index = defaultdict(list)
    for link in library['links']:
        if effective_status(link, records) == 'checked':
            index[link['question_id']].append(link)
    return index


def report(library, records, question_id=None, method_id=None, knowledge_id=None):
    if question_id is not None and question_id not in records:
        raise ValueError('未知或不可用题号: ' + question_id)
    if method_id is not None and method_id not in library['methods']:
        raise ValueError('未知方法: ' + method_id)
    grouped = defaultdict(list)
    for link in library['links']:
        if link['question_id'] in records:
            grouped[link['question_id']].append(link)
    # An explicit knowledge query also returns its unlinked questions. Missing
    # links mean unreviewed, not unusable and never unnecessary to learn.
    qids = ({question_id} if question_id else
            {qid for qid, q in records.items() if la.knowledge(q) == knowledge_id}
            if knowledge_id else set(grouped))
    items = []
    for qid in sorted(qids):
        q = records[qid]
        if knowledge_id is not None and la.knowledge(q) != knowledge_id:
            continue
        links = [dict(link, effective_status=effective_status(link, records))
                 for link in grouped[qid] if method_id is None or link['method_id'] == method_id]
        if method_id is not None and not links:
            continue
        l2 = q.get('l2') or {}
        items.append({'question_id': qid, 'knowledge_id': la.knowledge(q),
                      'annotated_method': l2.get('primary_method'),
                      'annotated_method_status': l2.get('review_status_by_field', {}).get('primary_method'),
                      'source_file': q['l0']['source_file'], 'source_locator': q['l0']['source_locator'],
                      'links': links})
    relevant = {link['method_id'] for item in items for link in item['links']}
    if method_id is not None:
        relevant.add(method_id)
    return {'version': VERSION, 'status': 'PASS', 'writes': 0,
            'methods': {mid: library['methods'][mid] for mid in sorted(relevant)},
            'questions': items,
            'checked_whole_question_ids': [item['question_id'] for item in items if any(
                l['effective_status'] == 'checked' and l['extent'] == 'whole' for l in item['links'])],
            'checked_step_question_ids': [item['question_id'] for item in items if any(
                l['effective_status'] == 'checked' and l['extent'] == 'step' for l in item['links'])],
            'notes': ['适用性、单题效率、整库复用收益和个人掌握分别判断；这里不评定最优。',
                      '子步骤关联不等于完整解法；无关联或过期保持未核对，不删除学习任务。']}


def learning_blocks(paper, library, records):
    """Explain explicit Teacher choices only at the repair entrance."""
    if paper['mode'] != 'repair':
        return []
    index = checked_index(library, records)
    selected = defaultdict(list)
    for q in paper['questions']:
        for link in index[q['question_id']]:
            if link['method_id'] in q.get('preferred_method_ids', []):
                selected[link['method_id']].append({'question_id': q['question_id'], 'extent': link['extent']})
    return [dict(library['methods'][mid], method_id=mid, questions=questions,
                 verification='检查能否自己识别适用条件、完成其余步骤，并用陌生题与延迟表现验证；不因共用方法合并掌握证据。')
            for mid, questions in sorted(selected.items())]
