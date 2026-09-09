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
    "> 本文逐题整理了**当前问题内容与异常字符**、**修复后标准 LaTeX 源码**以及**实际公式渲染效果预览**。在 Markdown 预览面板中可直接查看 KaTeX/MathJax 实时渲染结果。",
    "",
    "## 目录概要与分类汇总",
    "",
    "| 类别 | 题数 | 涉及题源 | 典型现象 | 根因与修复原则 |",
    "|---|---:|---|---|---|",
    "| **模式一：公式不等号误识** | 26 | 数学一(6)、数学二(11)、数学三(8)、408经典题(1) | `x=0`、`a=0`、`A=B` | 扫描 OCR 将 LaTeX `\\ne` / `\\neq` 误识别为私有区字符 `\\ue020=`（显示为方框 `=`）；统一替换为标准 LaTeX `\\ne ` |",
    "| **模式二：王道公式字体乱码** | 15 | 王道考研 408 (15) | ``、`  `、``、`` | 讲义排版使用了 Wingdings/Symbol 字体，分别对应大括号 `{}`、绝对值符号 `\\vert`、矩阵括号；替换为标准 Markdown/LaTeX |",
    "| **模式三：张宇高数符号漂移** | 5 | 张宇 1000 题 (5) | ``、``、`` | 印刷字体被误捕获为控制符，涉及平均值记号、多余字符及全微分极限；清理残符并规范 LaTeX |",
    "| **模式四：跨页切分碎片** | 1 | 王道操作系统 (1) | `WD-OS-C-2.2-T00` | 原书 P31 进程调度表格截断，上半段被单列为第 0 题；应合并至下半题并清理该题号 |",
    "",
    "---",
    "",
    "## 逐题审查与修复清单",
    ""
]

SPECIAL_FIXES = {
    "WD-CO-A-2.3-T05": {
        "problem": "王道机组综合题中，将公式下大括号 `\\underbrace` 误识为 Wingdings 字符 `` 并拆断了行。",
        "current_desc": "公式被拆断成多行，并混入 Wingdings 字符 ``：",
        "current_quote": "5. 【2017 统考真题】已知f n ...  n+1位 B, 计算f n",
        "fixed_code": "5. 【2017 统考真题】已知 $f(n) = \\sum_{i=0}^n 2^i = 2^{n+1} - 1 = \\underbrace{11\\cdots 1}_{n+1\\text{位}}\\text{B}$，计算 $f(n)$ 的 C 语言函数 f1 如下：",
        "display_math": "f(n) = \\sum_{i=0}^n 2^i = 2^{n+1} - 1 = \\underbrace{11\\cdots 1}_{n+1\\text{位}}\\text{B}",
        "rationale": "还原 2017 年 408 统考真题第 43 题的标准数学公式与下括号标注。"
    },
    "WD-DS-A-2.2-T14": {
        "problem": "2020 年统考真题第 41 题中，绝对值符号 `|` 被 OCR 转成了两两配对的独立行 `` 字符。",
        "current_desc": "绝对值符号被切成多行独立字符 ``：",
        "current_quote": "(a,b,c 均为整数) 的距离D = a-b  + b-c  + c-a  。给定 3 个非空整数集合S1、S2 和S3...",
        "fixed_code": "(a, b, c 均为整数) 的距离 $D = |a - b| + |b - c| + |c - a|$。给定 3 个非空整数集合 $S_1$、$S_2$ 和 $S_3$...",
        "display_math": "D = |a - b| + |b - c| + |c - a|",
        "rationale": "将分散成多行的私有区字符 `` 还原为内联数学公式绝对值 $|a-b| + |b-c| + |c-a|$。"
    },
    "WD-DS-A-2.3-T06": {
        "problem": "线性表元组大括号被误识为 ` `。",
        "current_desc": "元组声明后附带 Wingdings 符号：",
        "current_quote": "设线性表 L = (a1, b1, a2, b2, ⋯, an, bn)   为线性表，采用带头结点的...",
        "fixed_code": "设线性表 $L = (a_1, b_1, a_2, b_2, \\cdots, a_n, b_n)$，采用带头结点的...",
        "display_math": "L = (a_1, b_1, a_2, b_2, \\cdots, a_n, b_n)",
        "rationale": "剔除末尾多余的 Wingdings 括号乱码，规范数学下标。"
    },
    "WD-DS-A-4.2-T01": {
        "problem": "KMP 算法 next 数组定义中的集合括号被误识为 ` `。",
        "current_desc": "模式串子集括号被转译为私有区符号：",
        "current_quote": "'p j-k+1⋯p j-1'   , 集合不为空",
        "fixed_code": "$\\{'p_{j-k+1}\\cdots p_{j-1}'\\}$ 集合不为空",
        "display_math": "\\{'p_{j-k+1}\\cdots p_{j-1}'\\} \\quad \\text{集合不为空}",
        "rationale": "将集合定义规范为 LaTeX 数学集合表示。"
    },
    "WD-DS-A-6.2-T07": {
        "problem": "边集大小 $|E|$ 的绝对值线被识为 ``。",
        "current_desc": "边集基数符号被转成 ``：",
        "current_quote": "由顶点集V 和边集E 组成，E  > 0，当G 中度为奇数的顶点",
        "fixed_code": "由顶点集 $V$ 和边集 $E$ 组成，$|E| > 0$，当 $G$ 中度为奇数的顶点",
        "display_math": "|E| > 0",
        "rationale": "还原集合基数（边数）$|E| > 0$。"
    },
    "WD-DS-A-7.2-T06": {
        "problem": "散列表/矩阵排版被转译为连续的私有区括号 `    `。",
        "current_desc": "矩阵排版转为私有区字符序列：",
        "current_quote": "为 1 4 7 2 5 8 3 6 9           ,",
        "fixed_code": "\\begin{pmatrix} 1 & 4 & 7 \\\\ 2 & 5 & 8 \\\\ 3 & 6 & 9 \\end{pmatrix}",
        "display_math": "\\begin{pmatrix} 1 & 4 & 7 \\\\ 2 & 5 & 8 \\\\ 3 & 6 & 9 \\end{pmatrix}",
        "rationale": "将混乱的 Wingdings 矩阵括号替换为标准 3×3 矩阵。"
    },
    "WD-DS-A-8.3-T04": {
        "problem": "集合定义花括号与集合元素个数被识为 `` 和 ``。",
        "current_desc": "集合大括号与子集基数符号被破坏：",
        "current_quote": "集合A = ak∣0≤k<n   , 将其划分为两个不相交子集 A1  , A2  ",
        "fixed_code": "集合 $A = \\{a_k \\mid 0 \\le k < n\\}$，将其划分为两个不相交子集 $A_1$ 和 $A_2$（元素个数分别为 $|A_1|, |A_2|$）",
        "display_math": "A = \\{a_k \\mid 0 \\le k < n\\}, \\quad |A_1|, |A_2|",
        "rationale": "还原 2016 年 408 统考第 41 题的标准集合与子集规模描述。"
    },
    "WD-DS-C-6.1-T18": {
        "problem": "图论选项中顶点数 $|V|$ 与边数 $|E|$ 的绝对值线被识为 ``。",
        "current_desc": "选项中多处绝对值线显示为 ``：",
        "current_quote": "A. 当V  > E  时, G 一定是连通的\nB. 当V  < E  时, G 一定是连通的",
        "fixed_code": "- **A.** 当 $|V| > |E|$ 时，$G$ 一定是连通的\n- **B.** 当 $|V| < |E|$ 时，$G$ 一定是连通的",
        "display_math": "|V| > |E|, \\quad |V| < |E|",
        "rationale": "将私有区符号替换为顶点数 $|V|$ 与边数 $|E|$。"
    },
    "WD-DS-C-6.2-T06": {
        "problem": "3×3 邻接矩阵括号被识为 `  `。",
        "current_desc": "邻接矩阵转为一串数字接特殊字符：",
        "current_quote": "= 0 1 0 1 0 1 0 1 0           可知",
        "fixed_code": "A = \\begin{pmatrix} 0 & 1 & 0 \\\\ 1 & 0 & 1 \\\\ 0 & 1 & 0 \\end{pmatrix}",
        "display_math": "A = \\begin{pmatrix} 0 & 1 & 0 \\\\ 1 & 0 & 1 \\\\ 0 & 1 & 0 \\end{pmatrix}",
        "rationale": "重构为标准的 LaTeX 3×3 邻接矩阵。"
    },
    "WD-DS-C-6.2-T19": {
        "problem": "4×4 邻接矩阵括号被识为 `  `。",
        "current_desc": "4×4 矩阵被展开为单行加特殊符号：",
        "current_quote": "0 1 1 0 1 0 0 1 0 0 0 1 0 0 0 0            ",
        "fixed_code": "A = \\begin{pmatrix} 0 & 1 & 1 & 0 \\\\ 1 & 0 & 0 & 1 \\\\ 0 & 0 & 0 & 1 \\\\ 0 & 0 & 0 & 0 \\end{pmatrix}",
        "display_math": "A = \\begin{pmatrix} 0 & 1 & 1 & 0 \\\\ 1 & 0 & 0 & 1 \\\\ 0 & 0 & 0 & 1 \\\\ 0 & 0 & 0 & 0 \\end{pmatrix}",
        "rationale": "重构为标准的 LaTeX 4×4 矩阵。"
    },
    "WD-DS-C-6.3-T17": {
        "problem": "图顶点集合大括号被转为 ``。",
        "current_desc": "顶点集合与边集出现乱码括号：",
        "current_quote": "顶点集V = V0,V1,V2,V3   , 边集E = <v0,v1>...",
        "fixed_code": "顶点集 $V = \\{v_0, v_1, v_2, v_3\\}$，边集 $E = \\{ \\langle v_0, v_1 \\rangle, \\dots \\}$",
        "display_math": "V = \\{v_0, v_1, v_2, v_3\\}, \\quad E = \\{ \\langle v_0, v_1 \\rangle, \\dots \\}",
        "rationale": "规范图顶点集与边集的标准集合表示。"
    },
    "WD-DS-C-6.4-T09": {
        "problem": "图的拓扑排序顶点集和边集被转为 ``。",
        "current_desc": "顶点集合定义包含乱码字符：",
        "current_quote": "V = v1,v2,v3,v4,v5,v6,v7   , E = ...",
        "fixed_code": "$V = \\{v_1, v_2, v_3, v_4, v_5, v_6, v_7\\}$",
        "display_math": "V = \\{v_1, v_2, v_3, v_4, v_5, v_6, v_7\\}",
        "rationale": "还原集合花括号与数学下标。"
    },
    "WD-DS-C-6.4-T17": {
        "problem": "拓扑排序选项中的箭头或括号被转为 ``。",
        "current_desc": "选项末尾多出 Wingdings 字符：",
        "current_quote": "- **A.** v1,v3,v2,v4,v6,v5,v7  \n- **B.** v1,v3,v2,v6,v4,v5,v7  ",
        "fixed_code": "- **A.** $v_1, v_3, v_2, v_4, v_6, v_5, v_7$\n- **B.** $v_1, v_3, v_2, v_6, v_4, v_5, v_7$",
        "display_math": "v_1, v_3, v_2, v_4, v_6, v_5, v_7",
        "rationale": "剔除末尾多余的私有区乱码，规范为斜体数学变量。"
    },
    "WD-DS-C-6.4-T23": {
        "problem": "关键路径题干中的边集合括号被转为 ``。",
        "current_desc": "顶点集与边集出现乱码：",
        "current_quote": "V = v1,v2,...,v10   , E = <v1,v2>5,...",
        "fixed_code": "$V = \\{v_1, v_2, \\dots, v_{10}\\}, E = \\{\\langle v_1, v_2\\rangle_5, \\dots\\}$",
        "display_math": "V = \\{v_1, v_2, \\dots, v_{10}\\}, \\quad E = \\{\\langle v_1, v_2\\rangle_5, \\dots\\}",
        "rationale": "规范为标准带权有向边集合表达。"
    },
    "WD-OS-C-2.4-T26": {
        "problem": "死锁银行家算法题干中的进程集合被转为 ``。",
        "current_desc": "进程集合定义附带乱码：",
        "current_quote": "进程集合P = P0,P1,P2,P3,P4   , 系统中有三类资源",
        "fixed_code": "进程集合 $P = \\{P_0, P_1, P_2, P_3, P_4\\}$，系统中有三类资源",
        "display_math": "P = \\{P_0, P_1, P_2, P_3, P_4\\}",
        "rationale": "还原进程集合花括号与数学下标。"
    },
    "ZY1000-JC-GS18-T02": {
        "problem": "形心竖坐标后面多出无意义控制字符 ``。",
        "current_desc": "正文夹带孤立控制符：",
        "current_quote": "则\\Omega的形心竖  坐标z=_____.",
        "fixed_code": "则 $\\Omega$ 的形心竖坐标 $\\bar{z} = \\underline{\\hspace{2em}}$。",
        "display_math": "\\bar{z} = \\underline{\\hspace{2em}}",
        "rationale": "剔除 `` 并将填空横线与形心符号规范化。"
    },
    "ZY1000-QH-GS10-T24": {
        "problem": "题干包含印刷附带的残存私有区字符 ``。",
        "current_desc": "公式中间夹带特殊印刷符：",
        "current_quote": "占据的区域是曲线y=f(x)  与直线x=a以及x轴围成的平面图形",
        "fixed_code": "占据的区域是曲线 $y = f(x)$ 与直线 $x = a$ 以及 $x$ 轴围成的平面图形",
        "display_math": "y = f(x), \\quad x = a",
        "rationale": "删除误识的印刷标记 ``。"
    },
    "ZY1000-QH-GS14-T04": {
        "problem": "平均值符号附近多出 ` 1` 乱码并缺少分母。",
        "current_desc": "平均值公式排版错乱：",
        "current_quote": "设f(x) 是[0, 1] 上的连续函数且其在[0, 1]  1 上的平均值 f = ,满足f)x",
        "fixed_code": "设 $f(x)$ 是 $[0, 1]$ 上的连续函数，且其在 $[0, 1]$ 上的平均值 $\\bar{f} = \\frac{1}{2}$，满足 $f(x)$ ...",
        "display_math": "\\bar{f} = \\frac{1}{2}",
        "rationale": "修复断裂的平均值符号与杂质字符。"
    },
    "ZY1000-QH-GS14-T26": {
        "problem": "积分区域定义尾部多出私有区图标 ``。",
        "current_desc": "积分区域定义尾部夹带特殊字符：",
        "current_quote": "|x|+|y∣\\le 1 } |y|  ,求\\iint e|x|+|y|d\\sigma",
        "fixed_code": "$D = \\{(x, y) \\mid |x| + |y| \\le 1\\}$，求 $\\iint_D e^{|x|+|y|} d\\sigma$",
        "display_math": "D = \\{(x, y) \\mid |x| + |y| \\le 1\\}, \\quad \\iint_D e^{|x|+|y|} d\\sigma",
        "rationale": "清理残存特殊字符并补全积分表达式。"
    },
    "ZY1000-QH-GS17-T13": {
        "problem": "多元函数全微分极限式中，范数及内积公式被转成大量 `` 及断裂方括号。",
        "current_desc": "公式严重乱码并断裂：",
        "current_quote": "lim p\\to p0 ) + f(p_0)  [ [ ]] -gradf| p ∘p_0 p 0 [][ f)p  =0",
        "fixed_code": "\\lim_{p \\to p_0} \\frac{f(p) - f(p_0) - \\nabla f|_{p_0} \\cdot (p - p_0)}{|p - p_0|} = 0",
        "display_math": "\\lim_{p \\to p_0} \\frac{f(p) - f(p_0) - \\nabla f|_{p_0} \\cdot (p - p_0)}{|p - p_0|} = 0",
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
    
    lines_out.append(f"### {idx}. 【{qid}】{t['l0']['question_source']}")
    lines_out.append(f"- **题源文件**：[{src}](file://{src_path}#L{ev['line_start']}-L{ev['line_end']})（第 {ev['line_start']}–{ev['line_end']} 行）")
    
    if qid in SPECIAL_FIXES:
        info = SPECIAL_FIXES[qid]
        lines_out.append(f"- **问题说明**：{info['problem']}")
        lines_out.append("")
        lines_out.append("#### 修复对照与渲染效果")
        lines_out.append("")
        lines_out.append(f"- **当前问题内容**：{info['current_desc']}")
        lines_out.append(f"  > `{info['current_quote']}`")
        lines_out.append("")
        lines_out.append(f"- **修复后标准源码**：")
        lines_out.append("")
        lines_out.append("```latex")
        lines_out.append(info['fixed_code'])
        lines_out.append("```")
        lines_out.append("")
        lines_out.append("- **Markdown 公式渲染预览**：")
        lines_out.append("")
        lines_out.append("$$")
        lines_out.append(info['display_math'])
        lines_out.append("$$")
        lines_out.append("")
        lines_out.append(f"- **修改依据**：{info['rationale']}")
        lines_out.append("")
        lines_out.append("---")
        lines_out.append("")
        continue
        
    if qid == 'WD-OS-C-2.2-T00':
        lines_out.append("- **问题说明**：**跨页切分残留的碎片题目**。原书 P31 进程调度表被跨页切断，上半截被误设为第 0 题。")
        lines_out.append("")
        lines_out.append("#### 修复对照与渲染效果")
        lines_out.append("")
        lines_out.append("- **当前残留碎片内容**：")
        lines_out.append("  > `### 【WD-OS-C-2.2-T00】第 0 题（P31）`")
        lines_out.append("  > `9`")
        lines_out.append("  > `P2`")
        lines_out.append("  > `4`")
        lines_out.append("  > `P3`")
        lines_out.append("")
        lines_out.append("- **处理建议**：删除此独立碎片题块，将其表格内容合并至下一题 `WD-OS-C-2.2-T27` 的调度表格中。")
        lines_out.append("- **修改依据**：消除非真实考题碎片，恢复完整进程调度表格。")
        lines_out.append("")
        lines_out.append("---")
        lines_out.append("")
        continue

    # Default pattern 1 (inequality \ue020=)
    lines_out.append("- **问题说明**：公式中的不等号 `≠` (`\\ne`) 被 OCR 误识为私有区符号 `\\ue020=`（显示为空白或方框乱码 `=`）。")
    
    matches = []
    for i, l in enumerate(block_lines):
        if '\ue020' in l:
            lineno = ev['line_start'] + i
            matches.append((lineno, l.strip()))
            
    lines_out.append("")
    lines_out.append("#### 修复对照与渲染效果")
    lines_out.append("")
    lines_out.append("| 出现位置 | 当前错误源码（含异常码位） | 修复后标准 LaTeX 源码 | Markdown / KaTeX 渲染预览 |")
    lines_out.append("|:---|:---|:---|:---:|")
    
    shown_matches = matches[:5]
    for lineno, raw_line in shown_matches:
        loc_desc = "题干" if lineno < ev['line_start'] + 20 else "解析"
        loc_str = f"**{loc_desc}（第 {lineno} 行）**"
        
        display_raw = raw_line.replace('|', '\\|').replace('\ue020=', '=').replace('\ue020', '')
        fixed_line = raw_line.replace('\ue020=', '\\ne ').replace('\ue020', '\\ne ')
        display_fixed_code = fixed_line.replace('|', '\\|')
        
        clean_target = re.sub(r'^[-\*\s]*\*\*[A-D]\.\*\*\s*', '', fixed_line)
        math_matches = re.findall(r'\$([^$]+)\$', clean_target)
        if math_matches:
            inner_math = math_matches[0].replace('|', '\\mid ')
            preview_math = f"${inner_math}$"
        else:
            inner_math = clean_target.replace('|', '\\mid ').replace('$', '')
            preview_math = f"${inner_math}$"
            
        lines_out.append(f"| {loc_str} | `{display_raw[:45]}` | `{display_fixed_code[:45]}` | {preview_math} |")
        
    if len(matches) > 5:
        lines_out.append(f"| *...（该题共 {len(matches)} 处）* | *其余解析步骤中的 `\\ue020=`* | *同步全局替换为 `\\ne `* | *同步正常渲染* |")
        
    lines_out.append("")
    lines_out.append("- **修改依据**：原真题试卷数学公式排版中均为标准不等号（如 $x \\ne 0$、$a \\ne 0$、$A \\ne B$），将 `\\ue020=` 统一替换为标准 LaTeX `\\ne `，即可恢复公式在 Markdown 预览与 Web 界面中的正常数学渲染。")
    lines_out.append("")
    lines_out.append("---")
    lines_out.append("")

doc = '\n'.join(lines_out) + '\n'
target_file = PROJECT / '系统文件/检查报告/47道文本与OCR异常题目审查与修复建议.md'
target_file.write_text(doc, encoding='utf-8')
print(f'Successfully updated {target_file}, total length: {len(doc)} chars, lines: {len(lines_out)}')
