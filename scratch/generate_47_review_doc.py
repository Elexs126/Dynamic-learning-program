import json, re
from pathlib import Path

PROJECT = Path('/home/elexs/Dynamic-learning-program')

with open(PROJECT / '系统文件/题目标注/L1/question_annotations_l1_v1.json') as f:
    data = json.load(f)

with open(PROJECT / '系统文件/题目标注/L1/l1_evidence_v1.jsonl') as f:
    evidence = {json.loads(line)['question_id']: json.loads(line) for line in f}

targets = [r for r in data['records'] if r['question_id'] == 'WD-OS-C-2.2-T00' or 'OCR_SUSPICIOUS_CHARACTERS' in r.get('review_flags', [])]

lines_out = [
    "# 47 道题干物理文本与 OCR 异常题目审查与修复方案",
    "",
    "> **编制说明**：本项目全库 8024 题经全量审计，共检出 47 道题目存在题干物理残缺或私有区 OCR 乱码（`OCR_SUSPICIOUS_CHARACTERS` 46 题 + 跨页切分碎片 1 题）。",
    "> 本文逐题整理了**当前错误题干**、**错误原因**及**拟修改方案**。所有改动均保持题意真实还原，不修改题目原意与考察考点。",
    "",
    "## 目录概要与分类汇总",
    "",
    "| 类别 | 题数 | 涉及题源 | 典型现象 | 根因与修复原则 |",
    "|---|---:|---|---|---|",
    "| **模式一：公式不等号误识** | 26 | 数学一(6)、数学二(11)、数学三(8)、408经典题(1) | `x=0`、`a=0`、`A=B` | 扫描 OCR 将 LaTeX `\\ne` / `\\neq` 转为私有区字符 `\\ue020=`；统一替换为标准 LaTeX `\\ne ` |",
    "| **模式二：王道公式字体乱码** | 15 | 王道考研 408 (15) | ``、`  `、``、`` | 讲义排版使用了 Wingdings/Symbol 字体，分别对应大括号 `{}`、绝对值 `\|`、矩阵括号；替换为标准 Markdown/LaTeX |",
    "| **模式三：张宇高数符号漂移** | 5 | 张宇 1000 题 (5) | ``、``、`` | 印刷字体被误捕获为控制符，涉及平均值记号、多余字符及全微分极限；清理残符并规范 LaTeX |",
    "| **模式四：跨页切分碎片** | 1 | 王道操作系统 (1) | `WD-OS-C-2.2-T00` | 原书 P31 进程调度表格截断，上半段被单列为第 0 题；应合并至下半题并清理该题号 |",
    "",
    "---",
    "",
    "## 逐题审查与修复清单",
    ""
]

# Specific hand-curated fixes for complex items
SPECIAL_FIXES = {
    "WD-CO-A-2.3-T05": {
        "problem": "王道机组综合题中，将公式下大括号 `\\underbrace` 误识为 Wingdings 字符 `` 并拆断了行。",
        "current": "5. 【2017 统考真题】已知f n\n\n\n=\nn\ni=0\n2i\n∑\n= 2n+1 - 1 = 11⋯1\n\nn+1位\nB, 计算f n",
        "fixed": "5. 【2017 统考真题】已知 $f(n) = \\sum_{i=0}^n 2^i = 2^{n+1} - 1 = \\underbrace{11\\cdots 1}_{n+1\\text{位}}\\text{B}$，计算 $f(n)$ 的 C 语言函数 f1 如下：",
        "rationale": "还原 2017 年 408 统考真题第 43 题的标准数学公式与下括号标注。"
    },
    "WD-DS-A-2.2-T14": {
        "problem": "2020 年统考真题第 41 题中，绝对值符号 `|` 被 OCR 转成了两两配对的独立行 `` 字符。",
        "current": "(a,b,c 均为整数) 的距离D = a-b\n\n+ b-c\n\n+ c-a\n\n。给定\n3 个非空整数集合S1、S2 和S3...",
        "fixed": "(a, b, c 均为整数) 的距离 $D = |a - b| + |b - c| + |c - a|$。给定 3 个非空整数集合 $S_1$、$S_2$ 和 $S_3$...",
        "rationale": "将分散成多行的私有区字符 `` 还原为内联数学公式绝对值 $|a-b| + |b-c| + |c-a|$。"
    },
    "WD-DS-A-2.3-T06": {
        "problem": "线性表元组大括号被识为 ` `。",
        "current": "设线性表 L = (a1, b1, a2, b2, ⋯, an, bn)   为线性表，采用带头结点的...",
        "fixed": "设线性表 $L = (a_1, b_1, a_2, b_2, \\cdots, a_n, b_n)$，采用带头结点的...",
        "rationale": "剔除末尾多余的 Wingdings 括号乱码。"
    },
    "WD-DS-A-4.2-T01": {
        "problem": "KMP 算法 next 数组定义中的集合括号被识为 ` `。",
        "current": "'p j-k+1⋯p j-1'   , 集合不为空",
        "fixed": "$\\{'p_{j-k+1}\\cdots p_{j-1}'\\}$ 集合不为空",
        "rationale": "将集合定义规范为 LaTeX 数学集合表示。"
    },
    "WD-DS-A-6.2-T07": {
        "problem": "边集大小 $|E|$ 的绝对值线被识为 ``。",
        "current": "由顶点集V 和边集E 组成，E  > 0，当G 中度为奇数的顶点",
        "fixed": "由顶点集 $V$ 和边集 $E$ 组成，$|E| > 0$，当 $G$ 中度为奇数的顶点",
        "rationale": "还原集合基数（边数）$|E| > 0$。"
    },
    "WD-DS-A-7.2-T06": {
        "problem": "散列表/矩阵排版被转译为连续的私有区括号 `    `。",
        "current": "为 1 4 7 2 5 8 3 6 9           ,",
        "fixed": "为 $\\begin{pmatrix} 1 & 4 & 7 \\\\ 2 & 5 & 8 \\\\ 3 & 6 & 9 \\end{pmatrix}$，",
        "rationale": "将混乱的 Wingdings 矩阵括号替换为标准 3×3 矩阵。"
    },
    "WD-DS-A-8.3-T04": {
        "problem": "集合定义花括号与集合元素个数被识为 `` 和 ``。",
        "current": "集合A = ak∣0≤k<n   , 将其划分为两个不相交子集 A1  , A2  ",
        "fixed": "集合 $A = \\{a_k \\mid 0 \\le k < n\\}$，将其划分为两个不相交子集 $A_1$ 和 $A_2$（元素个数分别为 $|A_1|, |A_2|$）",
        "rationale": "还原 2016 年 408 统考第 41 题的标准集合与子集规模描述。"
    },
    "WD-DS-C-6.1-T18": {
        "problem": "图论选项中顶点数 $|V|$ 与边数 $|E|$ 的绝对值线被识为 ``。",
        "current": "A. 当V  > E  时, G 一定是连通的\nB. 当V  < E  时, G 一定是连通的",
        "fixed": "- **A.** 当 $|V| > |E|$ 时，$G$ 一定是连通的\n- **B.** 当 $|V| < |E|$ 时，$G$ 一定是连通的",
        "rationale": "将私有区符号替换为顶点数 $|V|$ 与边数 $|E|$。"
    },
    "WD-DS-C-6.2-T06": {
        "problem": "3×3 邻接矩阵括号被识为 `  `。",
        "current": "= 0 1 0 1 0 1 0 1 0           可知",
        "fixed": "邻接矩阵 $A = \\begin{pmatrix} 0 & 1 & 0 \\\\ 1 & 0 & 1 \\\\ 0 & 1 & 0 \\end{pmatrix}$ 可知",
        "rationale": "重构为标准的 LaTeX 3×3 矩阵。"
    },
    "WD-DS-C-6.2-T19": {
        "problem": "4×4 邻接矩阵括号被识为 `  `。",
        "current": "0 1 1 0 1 0 0 1 0 0 0 1 0 0 0 0            ",
        "fixed": "$A = \\begin{pmatrix} 0 & 1 & 1 & 0 \\\\ 1 & 0 & 0 & 1 \\\\ 0 & 0 & 0 & 1 \\\\ 0 & 0 & 0 & 0 \\end{pmatrix}$",
        "rationale": "重构为标准的 LaTeX 4×4 矩阵。"
    },
    "WD-DS-C-6.3-T17": {
        "problem": "图顶点集合大括号被转为 ``。",
        "current": "顶点集V = V0,V1,V2,V3   , 边集E = <v0,v1>...",
        "fixed": "顶点集 $V = \\{v_0, v_1, v_2, v_3\\}$，边集 $E = \\{ \\langle v_0, v_1 \\rangle, \\dots \\}$",
        "rationale": "规范图顶点集与边集的标准集合表示。"
    },
    "WD-DS-C-6.4-T09": {
        "problem": "图的拓扑排序顶点集和边集被转为 ``。",
        "current": "V = v1,v2,v3,v4,v5,v6,v7   , E = ...",
        "fixed": "$V = \\{v_1, v_2, v_3, v_4, v_5, v_6, v_7\\}$，边集 $E = \\{ \\dots \\}$",
        "rationale": "还原集合花括号。"
    },
    "WD-DS-C-6.4-T17": {
        "problem": "拓扑排序选项中的箭头或括号被转为 ``。",
        "current": "- **A.** v1,v3,v2,v4,v6,v5,v7  \n- **B.** v1,v3,v2,v6,v4,v5,v7  ",
        "fixed": "- **A.** $v_1, v_3, v_2, v_4, v_6, v_5, v_7$\n- **B.** $v_1, v_3, v_2, v_6, v_4, v_5, v_7$",
        "rationale": "剔除末尾多余的私有区乱码。"
    },
    "WD-DS-C-6.4-T23": {
        "problem": "关键路径题干中的边集合括号被转为 ``。",
        "current": "V = v1,v2,...,v10   , E = <v1,v2>5,...",
        "fixed": "$V = \\{v_1, v_2, \\dots, v_{10}\\}, E = \\{\\langle v_1, v_2\\rangle_5, \\dots\\}$",
        "rationale": "规范为标准带权有向边集合表达。"
    },
    "WD-OS-C-2.4-T26": {
        "problem": "死锁银行家算法题干中的进程集合被转为 ``。",
        "current": "进程集合P = P0,P1,P2,P3,P4   , 系统中有三类资源",
        "fixed": "进程集合 $P = \\{P_0, P_1, P_2, P_3, P_4\\}$，系统中有三类资源",
        "rationale": "还原进程集合花括号。"
    },
    "ZY1000-JC-GS18-T02": {
        "problem": "形心竖坐标后面多出无意义控制字符 ``。",
        "current": "则\\Omega的形心竖  坐标z=_____.",
        "fixed": "则 $\\Omega$ 的形心竖坐标 $\\bar{z} = \\underline{\\hspace{2em}}$。",
        "rationale": "剔除 `` 并将填空横线规范化。"
    },
    "ZY1000-QH-GS10-T24": {
        "problem": "题干包含印刷附带的残存私有区字符 ``。",
        "current": "占据的区域是曲线y=f(x)  与直线x=a以及x轴围成的平面图形",
        "fixed": "占据的区域是曲线 $y = f(x)$ 与直线 $x = a$ 以及 $x$ 轴围成的平面图形",
        "rationale": "删除误识的印刷标记 ``。"
    },
    "ZY1000-QH-GS14-T04": {
        "problem": "平均值符号附近多出 ` 1` 乱码。",
        "current": "设f(x) 是[0, 1] 上的连续函数且其在[0, 1]  1 上的平均值 f = ,满足f)x",
        "fixed": "设 $f(x)$ 是 $[0, 1]$ 上的连续函数，且其在 $[0, 1]$ 上的平均值 $\\bar{f} = \\frac{1}{2}$，满足 $f(x)$ ...",
        "rationale": "修复断裂的平均值符号与杂质字符。"
    },
    "ZY1000-QH-GS14-T26": {
        "problem": "积分区域定义尾部多出私有区图标 ``。",
        "current": "|x|+|y∣\\le 1 } |y|  ,求\\iint e|x|+|y|d\\sigma",
        "fixed": "$D = \\{(x, y) \\mid |x| + |y| \\le 1\\}$，求 $\\iint_D e^{|x|+|y|} d\\sigma$",
        "rationale": "清理残存特殊字符并补全积分表达式。"
    },
    "ZY1000-QH-GS17-T13": {
        "problem": "多元函数全微分极限式中，范数及内积公式被转成大量 `` 及断裂方括号。",
        "current": "lim p\\to p0 ) + f(p_0)  [ [ ]] -gradf| p ∘p_0 p 0 [][ f)p  =0",
        "fixed": "$\\lim_{p \\to p_0} \\frac{f(p) - f(p_0) - \\nabla f|_{p_0} \\cdot (p - p_0)}{|p - p_0|} = 0$",
        "rationale": "还原多元函数在点 $p_0$ 处可微的全微分等价定义式。"
    }
}

for idx, t in enumerate(targets, 1):
    qid = t['question_id']
    src = t['l0']['source_file']
    ev = evidence[qid]
    src_path = PROJECT / src
    all_lines = src_path.read_text(encoding='utf-8').splitlines()
    block_lines = all_lines[ev['line_start']-1:ev['line_end']]
    block_text = '\n'.join(block_lines)
    
    lines_out.append(f"### {idx}. 【{qid}】")
    lines_out.append(f"- **题源文件**：[{src}](file://{src_path}#L{ev['line_start']}-L{ev['line_end']})（第 {ev['line_start']}–{ev['line_end']} 行）")
    lines_out.append(f"- **所属题卷**：{t['l0']['question_source']}")
    
    if qid in SPECIAL_FIXES:
        info = SPECIAL_FIXES[qid]
        lines_out.append(f"- **问题说明**：{info['problem']}")
        lines_out.append("- **当前错误题干片段**：")
        lines_out.append("```markdown")
        lines_out.append(info['current'])
        lines_out.append("```")
        lines_out.append("- **拟修改为（正确题干/片段）**：")
        lines_out.append("```markdown")
        lines_out.append(info['fixed'])
        lines_out.append("```")
        lines_out.append(f"- **修改依据**：{info['rationale']}")
        lines_out.append("")
        lines_out.append("---")
        lines_out.append("")
        continue
        
    if qid == 'WD-OS-C-2.2-T00':
        lines_out.append("- **问题说明**：**跨页表格切分残留的碎片题目**")
        lines_out.append("- **当前错误题干片段**：")
        lines_out.append("```markdown")
        lines_out.append("### 【WD-OS-C-2.2-T00】第 0 题（P31）\n\n9\nP2\n4\nP3\n\n> **【唯一编号】** `WD-OS-C-2.2-T00`\n> **【课程】** 操作系统\n> **【章节】** 第2章 进程与线程 · 2.2 CPU调度")
        lines_out.append("```")
        lines_out.append("- **拟修改为（正确题干/片段）**：")
        lines_out.append("```markdown")
        lines_out.append("（建议操作：删除此碎片块，并将其表格信息合并入下一题 WD-OS-C-2.2-T27 题干）")
        lines_out.append("```")
        lines_out.append("- **修改依据**：王道操作系统选择题第 2.2 节原书 P31 进程调度表被截断，上半截被误切为第 0 题，不是真正的考题。")
        lines_out.append("")
        lines_out.append("---")
        lines_out.append("")
        continue

    # Default pattern 1 (inequality \ue020=)
    lines_out.append("- **问题说明**：公式中的不等号 `≠` (`\\ne`) 被 OCR 误识为私有区符号 `\\ue020=`（显示为 `=`）。")
    err_lines = [l.strip() for l in block_lines if '\ue020=' in l or '\ue020' in l]
    fixed_lines = [l.replace('\ue020=', '\\ne ').replace('\ue020', '\\ne ') for l in err_lines]
    lines_out.append("- **当前错误题干片段**：")
    lines_out.append("```markdown")
    for l in err_lines[:3]:
        lines_out.append(l)
    lines_out.append("```")
    lines_out.append("- **拟修改为（正确题干/片段）**：")
    lines_out.append("```markdown")
    for l in fixed_lines[:3]:
        lines_out.append(l)
    lines_out.append("```")
    lines_out.append("- **修改依据**：原真题试卷数学公式排版中均为标准不等号（如 $x \\ne 0$、$a \\ne 0$、$A \\ne B$），将 `\\ue020=` 统一替换为标准 LaTeX `\\ne ` 即可恢复公式正常渲染。")
    lines_out.append("")
    lines_out.append("---")
    lines_out.append("")

doc = '\n'.join(lines_out) + '\n'
target_file = PROJECT / '系统文件/检查报告/47道文本与OCR异常题目审查与修复建议.md'
target_file.write_text(doc, encoding='utf-8')
print(f'Successfully wrote {len(doc)} chars to {target_file}')
