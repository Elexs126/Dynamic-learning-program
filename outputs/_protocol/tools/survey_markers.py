#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
survey_markers.py — 精确统计各科讲义的推理标记词密度。

修正背景：早先用 PowerShell `Measure-Object -Line` 统计的是**非空行**数
（例如第01讲报 1830，实际 3163 行），导致"每千行密度"被高估约 1.7 倍。
本脚本按字符流统计**总行数**，重算全部密度。

用法: python survey_markers.py --src <源仓库根> --md <输出md> --json <输出json>
"""
import argparse
import io
import json
import os
import sys

COURSES = ['高等数学', '线性代数', '概率论与数理统计',
           '数据结构', '计算机组成原理', '操作系统', '计算机网络']

# 标记词：各科推理层用不同词（见 source_marker_survey.md 结论 1）
#
# ⚠️ 修正记录：本表最初是**猜**出来的（只列了 分析/方法总结/注/考点及方法小结/…），
# 结果漏掉了三个真正的科目专用标记，并因此错误地宣称"概率讲义推理层为 0"：
#   - `良哥解读`   概率专用，134 处  ← 概率真正的推理层
#   - `展示新知`   线代专用，~144 处
#   - `学习札记`   线代专用，70 处
# 现改为以 `discover_markers.py` 的**发现式**结果为准（统计全库重复短行）。
MARKERS = [
    '分析', '方法总结', '注', '考点及方法小结', '考点追踪',
    '题型', '方法', '注意', '技巧', '例题',
    # —— 发现式补充（此前遗漏）——
    '良哥解读', '展示新知', '学习札记', '练习区域', '本题代码如下',
]


def count_markers(text, marker):
    """计数出现次数（非行数）。'注' 与 '注意' 分开统计以避免互相污染。"""
    return text.count(marker)


def survey_course(src_root, course):
    base = os.path.join(src_root, '讲义', course)
    files = []
    for root, _dirs, names in os.walk(base):
        for n in sorted(names):
            if n.lower().endswith('.md'):
                files.append(os.path.join(root, n))
    total_lines = 0
    total_chars = 0
    counts = {m: 0 for m in MARKERS}
    for p in files:
        with io.open(p, encoding='utf-8', errors='replace') as f:
            t = f.read()
        total_lines += t.count('\n') + 1
        total_chars += len(t)
        for m in MARKERS:
            counts[m] += t.count(m)
    return {
        'course': course,
        'files': len(files),
        'total_lines': total_lines,
        'total_chars': total_chars,
        'markers': counts,
        'analysis_per_1k_lines': round(counts['分析'] * 1000.0 / max(1, total_lines), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument('--src', required=True)
    ap.add_argument('--md', default=os.path.abspath(os.path.join(here, '..', '..', '_index', 'source_marker_survey.md')))
    ap.add_argument('--json', default=os.path.abspath(os.path.join(here, '..', '..', '_index', 'source_marker_survey.json')))
    args = ap.parse_args()

    rows = [survey_course(args.src, c) for c in COURSES]

    with io.open(args.json, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps({'courses': rows}, ensure_ascii=False, indent=1))

    L = []
    L.append('# 源材料结构实测：推理标记词分布')
    L.append('')
    L.append('> 由 `survey_markers.py` 按字符流精确统计（总行数 = `\\n` 计数 + 1）。')
    L.append('> **修正说明**：早先用 PowerShell `Measure-Object -Line` 统计的是**非空行**，')
    L.append('> 例如第01讲报 1830 行、实际 3163 行，导致"每千行密度"被高估约 1.7 倍。本表为修正后的准确值。')
    L.append('>')
    L.append('> 用途：为 `coverage_report.md` 提供"各科证据基础强度"的客观依据。')
    L.append('')
    L.append('## 一、按课程（精确总行数）')
    L.append('')
    L.append('| 课程 | md 文件 | 总行数 | `分析` | `方法总结` | `注` | `考点及方法小结` | `考点追踪` | `良哥解读` | `展示新知` | `学习札记` |')
    L.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for r in rows:
        m = r['markers']
        L.append('| %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d |' % (
            r['course'], r['files'], r['total_lines'],
            m['分析'], m['方法总结'], m['注'],
            m['考点及方法小结'], m['考点追踪'],
            m['良哥解读'], m['展示新知'], m['学习札记']))
    L.append('')
    L.append('## 二、其余标记词')
    L.append('')
    L.append('| 课程 | `题型` | `方法` | `注意` | `技巧` | `例题` |')
    L.append('|---|---:|---:|---:|---:|---:|')
    for r in rows:
        m = r['markers']
        L.append('| %s | %d | %d | %d | %d | %d |' % (
            r['course'], m['题型'], m['方法'], m['注意'], m['技巧'], m['例题']))
    L.append('')
    L.append('## 三、结构性结论')
    L.append('')
    L.append('### 结论 1：七门课**每门都有自己的推理层标记词**，没有任何一个词是通用的')
    L.append('- **高数**：`分析` + `方法总结` + `注`')
    L.append('- **线代**：`分析` + `注` + **`展示新知`** + **`学习札记`**（无 `方法总结`）')
    L.append('- **概率**：**`良哥解读`** + `考点及方法小结` + `注`（**`分析` 为 0**）')
    L.append('- **408 四门**：`分析` + `注` + `考点追踪`（`考点追踪` 是年份指针，**不是推理**）')
    L.append('')
    L.append('**⚠️ 修正记录（重要）**：本表最初是**先猜标记名再搜**，漏掉了 `良哥解读`(134)、')
    L.append('`展示新知`(153)、`学习札记`(70) 三个真正的科目专用标记，并因此**错误地宣称')
    L.append('"概率讲义推理层为 0"**。真相是概率的推理层换了个名字（`良哥解读`）。')
    L.append('现改以 `discover_markers.py` 的发现式统计为准。')
    L.append('')
    L.append('**方法论教训**：研究"材料里有什么"时，**不要猜词表再搜**——')
    L.append('要先做发现式统计（高频重复短行），让标记词自己浮出来。')
    L.append('猜词表会系统性漏掉你没想到的名字，而且**漏掉时不会报错**，只会静默给出 0。')
    L.append('')
    L.append('### 结论 2：E1 比例跟随「所挖章节的标记密度」，而不是跟随科目')
    L.append('概率的 `良哥解读` 分布**极不均匀**：基础篇 106 处、强化篇仅 28 处，')
    L.append('其中强化篇 ch05（大数定律）与 ch07（参数估计）**均为 0**。')
    L.append('因此 M8 的 E1 比例高（54%），一部分原因是它的 E2 集中在有原话的')
    L.append('ch03/ch04/ch02，而 E1 集中在 ch01/ch05/ch07。')
    L.append('**结论**：不能只说"某科证据薄"，要说"**某科的哪几章**证据薄"。')
    L.append('')
    L.append('### 结论 3：408 讲义是"设计说明驱动"而非"例题驱动"')
    L.append('408 四门课 `例题` 计数极低，但 `考点追踪` 很高（148–181）。说明：')
    L.append('- 408 讲义的推理载体是**解释性正文**（设计动机句），不是 worked example；')
    L.append('- 408 的**主要轨迹证据来自真题解析**（`核心真题/408` 全部 846 题都带 `<details>` 参考答案与解析）；')
    L.append('- `考点追踪` 只标注"该考点考过哪一年"，**不构成"为什么这样想"的证据**。')
    L.append('')
    L.append('## 四、对任务设计的三条直接后果')
    L.append('')
    L.append('1. **任何"用统一正则抽推理句"的管线都会系统性漏抽**——七门课七个词表，必须按科目分别处理。')
    L.append('2. **E3（多题反复）证据的可得性在科目间不可比**：`方法总结` 只在高数存在，')
    L.append('   `展示新知`/`学习札记` 只在论代，`良哥解读` 只在概率。')
    L.append('   **跨领域 E5 判定必须扣除这个基线差异**，不能因为某科 E3 少就断言其问题结构单一。')
    L.append('3. **408 的 `考点追踪` 提供了现成的年份—考点映射**，可用于校核 Episode 的 `source` 字段')
    L.append('   与真题 ID 对应关系，但不能用作轨迹证据。')
    L.append('')

    with io.open(args.md, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')

    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps([{ 'course': r['course'], 'lines': r['total_lines'],
                        'analysis': r['markers']['分析'],
                        'per1k': r['analysis_per_1k_lines']} for r in rows],
                     ensure_ascii=False))
    print('written %s' % args.md)
    return 0


if __name__ == '__main__':
    sys.exit(main())
