#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover_inline_markers.py — 发现式统计**行内**标记（如 `【分析】`），而非只看整行。

## 为什么需要它（两次失败的方法论教训）

第 1 次：我先**猜**标记名（分析/方法总结/注），再去搜 → 系统性漏掉
        `良哥解读`(134)、`展示新知`(153)、`学习札记`(70)。M8 发现。
第 2 次：我改用 `discover_markers.py`，它统计**高频短整行**（len<=24）。
        但 `【评注】`(48)、`【提示】`(17) 是**行内**出现的，不是独立整行，
        所以行频方法**看不见它们**。M7 发现。

**根本教训**：发现式方法必须与被发现对象的**形态**匹配。
整行方法只能发现"独占一行"的标记；行内标记必须用**行内模式**去发现。

本工具不猜名字，直接抓全库所有 `【X】` / `〔X〕` 形态的短标记，按课程统计。
"""
import argparse
import io
import os
import re
import sys
from collections import Counter, defaultdict

SRC = r'E:\杂七杂八的垃圾堆\_dlp_src'
COURSE_DIRS = [
    ('高等数学', '讲义/高等数学'),
    ('线性代数', '讲义/线性代数'),
    ('概率论与数理统计', '讲义/概率论与数理统计'),
    ('数据结构', '讲义/数据结构'),
    ('操作系统', '讲义/操作系统'),
    ('计算机组成原理', '讲义/计算机组成原理'),
    ('计算机网络', '讲义/计算机网络'),
]

# 行内短标记：**只用中日韩括号**。
# ⚠️ 第一版把 ASCII 的 `[` `(` 也当开括号，结果把文本里每一个 `(x)`、`[1]`
# 都算成"标记"，跑出 1114 个"不同标记"（`【x】` 4802 次）——明显是工具错了。
# 与"全库都错的检查通常意味着检查写错了"是同一个判据。
INLINE_RE = re.compile(r'【([^】]{1,8})】')
# 独占一行的短标记（无括号），用于兼容旧方法
LINE_RE = re.compile(r'^\s*([\u4e00-\u9fa5A-Za-z]{2,10})\s*$')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-count', type=int, default=3,
                    help='低于该出现次数的标记不列（默认 3）')
    ap.add_argument('--out', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    inline = defaultdict(Counter)   # course -> marker -> count
    lineno = defaultdict(Counter)   # course -> standalone line token -> count
    files = Counter()
    lines = Counter()

    for course, rel in COURSE_DIRS:
        base = os.path.join(SRC, rel.replace('/', os.sep))
        if not os.path.isdir(base):
            continue
        for root, _d, fs in os.walk(base):
            for fn in fs:
                if not fn.lower().endswith('.md'):
                    continue
                files[course] += 1
                p = os.path.join(root, fn)
                t = io.open(p, encoding='utf-8', errors='replace').read().replace('\r\n', '\n')
                lines[course] += t.count('\n') + 1
                for m in INLINE_RE.finditer(t):
                    inner = m.group(1).strip()
                    if inner:
                        inline[course][inner] += 1
                for m in LINE_RE.finditer(t):
                    tok = m.group(1).strip()
                    if tok:
                        lineno[course][tok] += 1

    # 全库汇总
    allmark = Counter()
    for c in inline:
        allmark.update(inline[c])

    L = ['# 行内标记发现（不猜名字）', '']
    L.append('由 `discover_inline_markers.py` 生成。抓取全库所有 `【X】` 形态的行内短标记。')
    L.append('')
    L.append('## 为什么需要行内发现（两次失败的方法论教训）')
    L.append('')
    L.append('| 次数 | 方法 | 漏掉了什么 | 谁发现 |')
    L.append('|---|---|---|---|')
    L.append('| 1 | **猜**标记名再搜 | `良哥解读`(134)、`展示新知`(153)、`学习札记`(70) | M8 |')
    L.append('| 2 | 统计**高频短整行** | `【评注】`(48)、`【提示】`(17)——它们是**行内**的 | M7 |')
    L.append('')
    L.append('**根本教训**：发现式方法必须与被发现对象的**形态**匹配。')
    L.append('整行方法只能发现"独占一行"的标记；行内标记必须用行内模式去发现。')
    L.append('')
    L.append('## 各课程规模')
    L.append('')
    L.append('| 课程 | 文件 | 行数 |')
    L.append('|---|---:|---:|')
    for c, _ in COURSE_DIRS:
        if c in files:
            L.append('| %s | %d | %d |' % (c, files[c], lines[c]))
    L.append('')
    L.append('## 全库行内标记（出现 >= %d 次）' % args.min_count)
    L.append('')
    L.append('| 标记 | 全库次数 | 分布（课程:次数） |')
    L.append('|---|---:|---|')
    for mk, n in allmark.most_common():
        if n < args.min_count:
            continue
        dist = '、'.join('%s:%d' % (c, inline[c][mk]) for c in inline if inline[c][mk])
        L.append('| `【%s】` | %d | %s |' % (mk, n, dist))
    L.append('')
    L.append('## 按课程分列')
    L.append('')
    for c, _ in COURSE_DIRS:
        if c not in inline:
            continue
        L.append('### %s' % c)
        L.append('')
        L.append('| 标记 | 次数 |')
        L.append('|---|---:|')
        for mk, n in inline[c].most_common():
            if n < args.min_count:
                continue
            L.append('| `【%s】` | %d |' % (mk, n))
        L.append('')

    text = '\n'.join(L) + '\n'
    if args.out:
        with io.open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    if not args.quiet:
        sys.stdout.reconfigure(encoding='utf-8')
        print('distinct inline markers (>=%d): %d' % (
            args.min_count, sum(1 for _, n in allmark.items() if n >= args.min_count)))
        for mk, n in allmark.most_common(24):
            if n < args.min_count:
                break
            dist = ' '.join('%s=%d' % (c[:2], inline[c][mk]) for c in inline if inline[c][mk])
            print('  【%-10s】 %4d   %s' % (mk, n, dist))
    return 0


if __name__ == '__main__':
    sys.exit(main())
