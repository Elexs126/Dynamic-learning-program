#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_coverage.py — 把大纲主题与实际 Episode 覆盖做交叉比对。

回答任务书 §21 的核心问题：
  "考研数学大纲中的问题世界，哪些已经有充分的问题轨迹覆盖？哪些仍然空白？"

方法：
  1. 读 _index/syllabus_map.json（46 个主题）
  2. 把每个 Episode 的 source.repo_path / section 映射到大纲主题
     （先按讲义文件名与主题名做词面匹配，再退回 section 匹配）
  3. 统计每个主题的 Episode 数，标出 0 覆盖与低覆盖主题

⚠️ 局限：讲义章节名与大纲主题名不是一一对应（例如"二重积分"属大纲的
   "多元函数积分学"）。词面匹配会漏掉一部分，脚本会把**未能映射**的
   源文件单独列出，供人工补映射——不要假装映射是全的。
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

PUNCT = re.compile(r'[、，。．,.\-—_（）()【】\[\]：:；;/\s]+')
NUM_PREFIX = re.compile(r'^(第\s*\d+\s*[讲章]\s*_?|附录_\d+_|附录_)')


def norm(s):
    return PUNCT.sub('', NUM_PREFIX.sub('', s or '')).lower()


def overlap_score(a, b):
    """两个规范化字符串的重合度（基于较短串被较长串覆盖的比例 + 字符集 Jaccard）"""
    if not a or not b:
        return 0.0
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    # 连续子串覆盖
    cover = 0
    for n in range(len(shorter), 1, -1):
        found = False
        for i in range(len(shorter) - n + 1):
            if shorter[i:i + n] in longer:
                cover = n
                found = True
                break
        if found:
            break
    sub = cover / len(shorter)
    jac = len(set(a) & set(b)) / max(1, len(set(a) | set(b)))
    return 0.6 * sub + 0.4 * jac


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--dir', default=os.path.abspath(os.path.join(here, '..', '..', 'raw_episodes')))
    ap.add_argument('--syllabus', default=os.path.abspath(os.path.join(here, '..', '..', '_index', 'syllabus_map.json')))
    ap.add_argument('--json', default=None)
    ap.add_argument('--md', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    syl = json.load(io.open(args.syllabus, encoding='utf-8'))
    topics = []          # (course, topic, norm_topic)
    for t in syl['tracks']:
        for c in t['courses']:
            for tp in c['topics']:
                topics.append((t['track'], c['course'], tp['topic'], norm(tp['topic'])))

    # 读 Episode
    episodes = []
    for fn in sorted(f for f in os.listdir(args.dir)
                     if f.endswith('.jsonl') and not f.startswith('_')):
        worker = os.path.splitext(fn)[0]
        with io.open(os.path.join(args.dir, fn), encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except Exception:
                    continue
                src = rec.get('source') or {}
                episodes.append({
                    'problem_id': rec.get('problem_id'),
                    'worker': worker,
                    'domain': rec.get('domain', ''),
                    'repo_path': src.get('repo_path', ''),
                    'section': src.get('section', ''),
                    'example': src.get('example_or_question', ''),
                })

    # 映射
    topic_eps = defaultdict(list)
    unmapped_files = Counter()
    file_to_topic = {}
    for ep in episodes:
        base = os.path.basename(ep['repo_path'] or '')
        stem = os.path.splitext(base)[0]
        ns = norm(stem)
        # 讲义文件名优先；真题/习题用 section
        best = None
        best_score = 0.0
        for track, course, topic, nt in topics:
            sc = overlap_score(ns, nt)
            if sc > best_score:
                best_score, best = sc, (track, course, topic)
            if ep['section']:
                sc2 = overlap_score(norm(ep['section']), nt)
                if sc2 > best_score:
                    best_score, best = sc2, (track, course, topic)
        if best and best_score >= 0.30:
            topic_eps[(best[0], best[1], best[2])].append(ep['problem_id'])
            file_to_topic[base] = best[2]
        else:
            unmapped_files[base or '(空路径)'] += 1

    # 汇总
    rows = []
    for track, course, topic, nt in topics:
        eps = topic_eps.get((track, course, topic), [])
        rows.append({
            'track': track, 'course': course, 'topic': topic,
            'episodes': len(eps),
            'problem_ids': eps,
            'status': ('充分' if len(eps) >= 5 else
                       '有覆盖' if len(eps) >= 2 else
                       '薄弱' if len(eps) == 1 else '空白'),
        })

    status_counts = Counter(r['status'] for r in rows)
    summary = {
        'total_episodes': len(episodes),
        'total_topics': len(rows),
        'status_counts': dict(status_counts),
        'unmapped_source_files': dict(unmapped_files.most_common()),
        'topics': rows,
    }

    if args.json:
        with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(summary, ensure_ascii=False, indent=1))

    L = ['# 大纲主题 × Episode 覆盖交叉比对', '']
    L.append('由 `analyze_coverage.py` 生成。把 `syllabus_map.json` 的每个大纲主题')
    L.append('与实际 Episode 做词面映射后统计覆盖量。')
    L.append('')
    L.append('## ⚠️ 方法局限（必须先读）')
    L.append('')
    L.append('- 讲义章节名与大纲主题名**不是一一对应**（如"二重积分"属大纲的"多元函数积分学"）。')
    L.append('- 本比对用词面重合度（阈值 0.30）做映射，**会漏也会错**。')
    L.append('- **未能映射的源文件在文末单独列出**——那是映射的缺口，不是"没有 Episode"。')
    L.append('- 因此本表用于**发现空白**，不能用于宣称"某主题已完全覆盖"。')
    L.append('')
    L.append('- Episode 总数：%d ｜ 大纲主题数：%d' % (len(episodes), len(rows)))
    for k in ('充分', '有覆盖', '薄弱', '空白'):
        L.append('- %s：%d 个主题' % (k, status_counts.get(k, 0)))
    L.append('')
    L.append('## 逐主题覆盖')
    L.append('')
    L.append('| 科目 | 主题 | Episode 数 | 状态 | 代表 problem_id |')
    L.append('|---|---|---:|---|---|')
    for r in rows:
        rep = '、'.join(r['problem_ids'][:4])
        L.append('| %s | %s | %d | %s | %s |' % (
            r['course'], r['topic'], r['episodes'], r['status'], rep))
    L.append('')
    L.append('## ⚠️ 零覆盖主题（真空白）')
    L.append('')
    blanks = [r for r in rows if r['episodes'] == 0]
    if blanks:
        for r in blanks:
            L.append('- **%s** / %s' % (r['course'], r['topic']))
    else:
        L.append('（无）')
    L.append('')
    L.append('## 未能映射的源文件（映射缺口，需人工补映射）')
    L.append('')
    if unmapped_files:
        L.append('| 源文件 | 涉及 Episode 数 |')
        L.append('|---|---:|')
        for k, v in unmapped_files.most_common(40):
            L.append('| `%s` | %d |' % (k, v))
    else:
        L.append('（无）')
    L.append('')

    text = '\n'.join(L) + '\n'
    if args.md:
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('topics=%d  %s' % (len(rows), json.dumps(dict(status_counts), ensure_ascii=False)))
        print('unmapped files: %d distinct' % len(unmapped_files))
    return 0


if __name__ == '__main__':
    sys.exit(main())
