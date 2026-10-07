#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_syllabus.py — 把两份考试大纲解析成结构化覆盖边界。

用途：coverage_report.md 需要回答"哪些 problem geometry 仍然空白"，
必须先把大纲的考点边界结构化，才能逐条比对 Episode 覆盖。

用法:
  python parse_syllabus.py --src <源仓库根> --json <输出json> --md <输出md>

产出 syllabus_map.json 结构:
{
  "tracks": [
    {"track":"MATH1","file":"...","courses":[
      {"course":"高等数学","topics":[
        {"topic":"函数、极限、连续",
         "content_items":[...],      # 考试内容
         "requirement_items":[...]}  # 考试要求
      ]}
    ]}
  ],
  "stats": {...}
}
"""
import argparse
import io
import json
import os
import re
import sys

MATH_COURSES = ['高等数学', '线性代数', '概率论与数理统计']
CS_COURSES = ['数据结构', '计算机组成原理', '操作系统', '计算机网络']

# 去掉标题里的 "一、" "（一）" 等编号前缀
NUM_PREFIX = re.compile(r'^[（(]?[一二三四五六七八九十百\d]+[）)]?\s*[、.．]?\s*')
HEADING = re.compile(r'^(#{1,6})\s+(.*)$')
ITEM_SPLIT = re.compile(r'(?:(?<=[；;。])|(?=\b\d+[.．、]))')


def strip_num(s):
    return NUM_PREFIX.sub('', s).strip()


def match_course(title, names):
    t = strip_num(title)
    for n in names:
        if t == n or t.startswith(n):
            return n
    return None


def split_items(text):
    """把一段正文切成条目列表。"""
    text = text.strip()
    if not text:
        return []
    # 优先按编号切
    if re.search(r'\b\d+[.．、]', text):
        parts = re.split(r'\s*(?=\b\d+[.．、])', text)
    else:
        parts = ITEM_SPLIT.split(text)
    out = []
    for p in parts:
        p = p.strip()
        p = re.sub(r'^\d+[.．、]\s*', '', p)
        if len(p) >= 2:
            out.append(p)
    return out


def parse_math(lines):
    courses = []
    cur_course = None
    cur_topic = None
    mode = None
    buf = []

    def flush():
        nonlocal buf
        if cur_topic is not None and mode:
            key = 'content_items' if mode == 'content' else 'requirement_items'
            cur_topic[key] = split_items('\n'.join(buf))
        buf = []

    for ln in lines:
        m = HEADING.match(ln)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if level == 1:
                c = match_course(title, MATH_COURSES)
                if c:
                    flush()
                    cur_course = {'course': c, 'topics': []}
                    courses.append(cur_course)
                    cur_topic = None
                    mode = None
                    continue
            if level == 2 and cur_course is not None:
                flush()
                cur_topic = {'topic': strip_num(title),
                             'content_items': [], 'requirement_items': []}
                cur_course['topics'].append(cur_topic)
                mode = None
                continue
            if level == 3 and cur_topic is not None:
                flush()
                if '考试内容' in title:
                    mode = 'content'
                elif '考试要求' in title:
                    mode = 'req'
                else:
                    mode = None
                continue
        elif mode:
            buf.append(ln)
    flush()
    return courses


def parse_cs(lines):
    """408 大纲结构：### 课程 → #### 主题 → ##### 子主题，正文挂在子主题下。
    正文一律累加到当前主题的 content_items，不因进入子主题而重置。"""
    courses = []
    cur_course = None
    cur_topic = None
    in_goal = False
    buf = []

    def flush():
        nonlocal buf
        if buf and cur_topic is not None:
            cur_topic['content_items'].extend(split_items('\n'.join(buf)))
        elif buf and in_goal and cur_course is not None:
            cur_course['exam_goal'].extend(split_items('\n'.join(buf)))
        buf = []

    for ln in lines:
        m = HEADING.match(ln)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if level == 3:
                c = match_course(title, CS_COURSES)
                if c:
                    flush()
                    cur_course = {'course': c, 'topics': [], 'exam_goal': []}
                    courses.append(cur_course)
                    cur_topic = None
                    in_goal = False
                    continue
            if level == 4 and cur_course is not None:
                flush()
                in_goal = False
                if '考察目标' in title or '考试目标' in title:
                    cur_topic = None
                    in_goal = True
                    continue
                cur_topic = {'topic': strip_num(title),
                             'content_items': [], 'subtopics': []}
                cur_course['topics'].append(cur_topic)
                continue
            if level == 5 and cur_topic is not None:
                # 进入子主题：先结算上一段正文，但**不重置** content_items
                flush()
                cur_topic['subtopics'].append(strip_num(title))
                continue
        else:
            if ln.strip():
                buf.append(ln)
    flush()
    return courses


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--src', required=True)
    ap.add_argument('--json', default=os.path.abspath(os.path.join(here, '..', '..', '_index', 'syllabus_map.json')))
    ap.add_argument('--md', default=os.path.abspath(os.path.join(here, '..', '..', '_index', 'syllabus_map.md')))
    args = ap.parse_args()

    specs = [
        ('MATH1', '考试大纲/2026考研数学一考试大纲.md', parse_math),
        ('CS408', '考试大纲/2026考研408考试大纲.md', parse_cs),
    ]

    tracks = []
    for track, rel, fn in specs:
        path = os.path.join(args.src, rel.replace('/', os.sep))
        if not os.path.isfile(path):
            print('MISSING %s' % path, file=sys.stderr)
            continue
        with io.open(path, encoding='utf-8', errors='replace') as f:
            lines = f.read().split('\n')
        courses = fn(lines)
        tracks.append({'track': track, 'file': rel, 'courses': courses})

    total_topics = sum(len(c['topics']) for t in tracks for c in t['courses'])
    total_items = 0
    for t in tracks:
        for c in t['courses']:
            for tp in c['topics']:
                total_items += len(tp.get('content_items', []))
                total_items += len(tp.get('requirement_items', []))

    payload = {
        'source_files': [s[1] for s in specs],
        'tracks': tracks,
        'stats': {
            'tracks': len(tracks),
            'courses': sum(len(t['courses']) for t in tracks),
            'topics': total_topics,
            'items': total_items,
        },
    }
    with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=1))

    L = ['# 考试大纲覆盖边界（结构化）', '']
    L.append('由 `parse_syllabus.py` 从源仓库 `考试大纲/` 两份文件解析。')
    L.append('**仅用于确定覆盖边界**，不作为学习内容或掌握证据。')
    L.append('')
    L.append('- 科目数：%d ｜ 主题数：%d ｜ 条目数：%d' % (
        payload['stats']['courses'], total_topics, total_items))
    L.append('')
    for t in tracks:
        L.append('## %s' % t['track'])
        L.append('')
        L.append('来源：`%s`' % t['file'])
        L.append('')
        for c in t['courses']:
            n_items = sum(len(tp.get('content_items', [])) + len(tp.get('requirement_items', []))
                          for tp in c['topics'])
            L.append('### %s（%d 主题 / %d 条目）' % (c['course'], len(c['topics']), n_items))
            L.append('')
            L.append('| 主题 | 考试内容条数 | 考试要求条数 | 子主题 |')
            L.append('|---|---:|---:|---|')
            for tp in c['topics']:
                subs = '、'.join(tp.get('subtopics', [])) or ''
                L.append('| %s | %d | %d | %s |' % (
                    tp['topic'], len(tp.get('content_items', [])),
                    len(tp.get('requirement_items', [])), subs))
            L.append('')
    with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')

    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(payload['stats'], ensure_ascii=False))
    print('written %s' % args.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
