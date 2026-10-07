#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pick_blind.py — 列出 blind test 候选（写 UTF-8 文件，避免控制台编码问题）。"""
import io
import json
import os
import sys

INV_M1 = r'E:\杂七杂八的垃圾堆\LearningOS\outputs\_index\inv_math1.json'
INV_408 = r'E:\杂七杂八的垃圾堆\LearningOS\outputs\_index\inv_408.json'
OUT = r'E:\杂七杂八的垃圾堆\LearningOS\outputs\_index\blind_candidates.md'


def load(p):
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)['questions']


def main():
    m1 = load(INV_M1)
    c408 = load(INV_408)
    lines = ['# Blind test 候选清单', '']
    lines.append('## 数学一 · 解答题（M1-YY-A-*）')
    lines.append('')
    lines.append('| id | 年份 | 科目 | 考点 |')
    lines.append('|---|---|---|---|')
    for q in m1:
        if 'A-' in q['id']:
            lines.append('| %s | %s | %s | %s |' % (q['id'], q['year'], q['subject'], q['kp']))
    lines.append('')
    lines.append('## 408 · 综合题（408-YY-A-*）')
    lines.append('')
    lines.append('| id | 年份 | 科目 | 考点 |')
    lines.append('|---|---|---|---|')
    for q in c408:
        if '-A-' in q['id']:
            lines.append('| %s | %s | %s | %s |' % (q['id'], q['year'], q['subject'], q['kp']))
    lines.append('')
    lines.append('## 408 · 选择题按科目计数')
    lines.append('')
    from collections import Counter
    c = Counter(q['subject'] for q in c408 if '-C-' in q['id'])
    for k, v in c.most_common():
        lines.append('- %s: %d' % (k, v))
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('written', OUT)


if __name__ == '__main__':
    main()
