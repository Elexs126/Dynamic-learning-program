#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover_markers.py — 系统性发现讲义里的"推理层标记词"，而不是靠猜名字。

背景：我早先的 survey_markers.py 是**猜**了几个标记名（分析/方法总结/注/…）去搜，
结果漏掉了概率讲义真正的标记 `良哥解读`（134 处），并错误地得出
"概率讲义推理层为 0"的结论。猜名字的方法不可靠。

本脚本改用**发现式**方法：统计全库重复出现的短行，找出真正的标记词。

用法: python discover_markers.py --src <源仓库根> [--min-count 20]
"""
import argparse
import io
import os
import re
import sys
from collections import Counter

COURSES = ['高等数学', '线性代数', '概率论与数理统计',
           '数据结构', '计算机组成原理', '操作系统', '计算机网络']

# 排除明显是公式/代码/图片的行
NOISE = re.compile(r'[\$\\{}<>\[\]`|]|^!\[|^\s*$|^\d+\s*$|^[（(]?\d+[）)]?\s*$')


def iter_md(src_root, course):
    base = os.path.join(src_root, '讲义', course)
    for root, _dirs, names in os.walk(base):
        for n in sorted(names):
            if n.lower().endswith('.md'):
                yield os.path.join(root, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--min-count', type=int, default=15)
    ap.add_argument('--md', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    # 全局短行频次 + 每科频次
    global_freq = Counter()
    per_course = {c: Counter() for c in COURSES}

    for course in COURSES:
        for path in iter_md(args.src, course):
            with io.open(path, encoding='utf-8', errors='replace') as f:
                for line in f:
                    s = line.strip()
                    if not s or len(s) > 24:
                        continue
                    if NOISE.search(s):
                        continue
                    global_freq[s] += 1
                    per_course[course][s] += 1

    # 只保留重复次数达标的候选
    cands = [(s, n) for s, n in global_freq.most_common() if n >= args.min_count]

    # 计算每个候选在哪些科目出现（用于判断是否科目专用）
    rows = []
    for s, n in cands:
        dist = {c: per_course[c].get(s, 0) for c in COURSES}
        present = [c for c in COURSES if dist[c] > 0]
        rows.append({'marker': s, 'total': n, 'courses': present, 'by_course': dist})

    if args.md:
        L = ['# 讲义推理层标记词：系统性发现结果', '']
        L.append('由 `discover_markers.py` 生成。')
        L.append('')
        L.append('## 为什么需要这个脚本')
        L.append('')
        L.append('早先的 `survey_markers.py` 是**先猜标记名再搜**（猜了 `分析`/`方法总结`/`注` 等），')
        L.append('结果**漏掉了概率讲义真正的标记 `良哥解读`（134 处）**，并错误地得出')
        L.append('"概率讲义推理层为 0"的结论。猜名字的方法不可靠。')
        L.append('')
        L.append('本脚本改为**发现式**：统计全库重复出现的短行（长度 <= 24、非公式/代码/图片），')
        L.append('按出现次数排序。真正的标记词会自然浮出来。')
        L.append('')
        L.append('- 阈值：出现 >= %d 次' % args.min_count)
        L.append('- 候选数：%d' % len(rows))
        L.append('')
        L.append('## 候选标记词')
        L.append('')
        L.append('| 标记 | 总次数 | 出现科目 | 是否科目专用 |')
        L.append('|---|---:|---|---|')
        for r in rows:
            spec = '是（仅 %s）' % r['courses'][0] if len(r['courses']) == 1 else '否'
            L.append('| `%s` | %d | %s | %s |' % (
                r['marker'], r['total'], '、'.join(r['courses']), spec))
        L.append('')
        L.append('## 逐科目分布')
        L.append('')
        hdr = '| 标记 | ' + ' | '.join(COURSES) + ' |'
        L.append(hdr)
        L.append('|---|' + '---:|' * len(COURSES))
        for r in rows:
            L.append('| `%s` | %s |' % (
                r['marker'], ' | '.join(str(r['by_course'][c]) for c in COURSES)))
        L.append('')
        text = '\n'.join(L) + '\n'
        with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)

    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('candidates (>=%d): %d' % (args.min_count, len(rows)))
        for r in rows[:40]:
            print('  %-22s %5d  %s' % (r['marker'], r['total'], '、'.join(r['courses'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
