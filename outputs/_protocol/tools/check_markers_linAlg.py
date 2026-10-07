#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_markers_linAlg.py — 核验 M7 对线代讲义推理标记的统计。"""
import io
import os
import re

BASE = r'E:\杂七杂八的垃圾堆\_dlp_src\讲义\线性代数'

PATTERNS = [
    ('【分析】', re.compile(r'【分析】')),
    ('行首 分析', re.compile(r'^\s*分析', re.M)),
    ('【注】', re.compile(r'【注】')),
    ('【方法总结】', re.compile(r'【方法总结】')),
    ('【评注】', re.compile(r'【评注】')),
    ('【提示】', re.compile(r'【提示】')),
    ('解题笔记', re.compile(r'解题笔记')),
    ('良哥解读', re.compile(r'良哥解读')),
    ('展示新知', re.compile(r'展示新知')),
    ('学习札记', re.compile(r'学习札记')),
]


def main():
    total = {k: 0 for k, _ in PATTERNS}
    nfiles = 0
    lines_total = 0
    for root, _d, files in os.walk(BASE):
        for fn in files:
            if not fn.lower().endswith('.md'):
                continue
            nfiles += 1
            p = os.path.join(root, fn)
            t = io.open(p, encoding='utf-8', errors='replace').read().replace('\r\n', '\n')
            lines_total += t.count('\n') + 1
            for k, rx in PATTERNS:
                total[k] += len(rx.findall(t))
    print('files=%d  lines=%d' % (nfiles, lines_total))
    for k, _ in PATTERNS:
        print('  %-14s %d' % (k, total[k]))


if __name__ == '__main__':
    main()
