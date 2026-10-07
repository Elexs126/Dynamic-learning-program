#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inspect_svg.py — 检查盲测示意图 SVG 是否可被浏览器正确解析，并验证 PNG 渲染结果。"""
import io
import os
import re
import sys

IMG = r'E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\images'
NAMES = ['408_2026_q44_220', '408_2022_q47_183', '408_2018_q44_128', '408_2026_q47_222']

# XML 属性名合法字符：字母、数字、下划线、连字符、冒号
ATTR_RE = re.compile(r'([^\s=<>/]+)\s*=\s*["\']')


def main():
    for n in NAMES:
        svg = os.path.join(IMG, n + '.svg')
        png = os.path.join(IMG, n + '.png')
        if not os.path.isfile(svg):
            print('MISSING svg', n)
            continue
        t = io.open(svg, encoding='utf-8', errors='replace').read()
        lines = t.split('\n')
        print('=== %s' % n)
        print('    svg lines=%d chars=%d' % (len(lines), len(t)))
        if os.path.isfile(png):
            print('    png bytes=%d' % os.path.getsize(png))

        # 找出非法属性名（含非法字符的）
        bad = []
        for m in ATTR_RE.finditer(t):
            name = m.group(1)
            if not re.match(r'^[A-Za-z_:][A-Za-z0-9_:.\-]*$', name):
                bad.append(name[:40])
        print('    illegal attr names: %d' % len(bad))
        for b in bad[:8]:
            print('       -> %r' % b)

        # 定位首个非法属性所在行
        if bad:
            idx = t.find(bad[0] + '=')
            if idx < 0:
                idx = t.find(bad[0])
            lineno = t[:idx].count('\n') + 1 if idx >= 0 else -1
            print('    first illegal attr at line %d' % lineno)

        # SVG 里的文字节点（用于判断标注是否存在）
        texts = re.findall(r'<text[^>]*>(.*?)</text>', t, re.S)
        cleaned = [re.sub(r'<[^>]+>', '', x).strip() for x in texts]
        cleaned = [x for x in cleaned if x]
        print('    <text> nodes: %d  (non-empty: %d)' % (len(texts), len(cleaned)))
        for c in cleaned[:6]:
            print('       text: %r' % c[:60])
        print()


if __name__ == '__main__':
    main()
