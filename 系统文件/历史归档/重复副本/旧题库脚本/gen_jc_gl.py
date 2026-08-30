# -*- coding: utf-8 -*-
"""
Generator for Zhang Yu 1000: 基础篇 · 概率论与数理统计 (6章 选择题)
"""

import os

BASE_DIR = r"c:\Users\HP\Documents\antigravity\delightful-salk\张宇1000题"

def save_chapter(rel_path, title, intro, questions):
    full_path = os.path.join(BASE_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"> {intro}\n\n---\n\n")
        for q in questions:
            f.write(f"### 第 {q['num']} 题（P{q['page']}）\n\n")
            f.write(f"{q['num']}. {q['stem']}\n\n")
            f.write(f"{q['options']}\n\n")
            f.write(f"> **【课程】** {q['course']}\n")
            f.write(f"> **【章节】** {q['chapter']}\n\n---\n\n")
    print(f"Saved: {rel_path} ({len(questions)} questions)")

# 第1章 随机事件与概率
save_chapter(
    "01_基础篇/概率论与数理统计/第01章_随机事件与概率.md",
    "《张宇1000题》· 基础篇 · 概率论与数理统计 · 第1章 随机事件与概率",
    "本章节收录第 113 页至第 123 页共 8 道选择题。",
    [
        {
            "num": 1, "page": 113, "course": "概率论与数理统计", "chapter": "第1章 随机事件与概率",
            "stem": r"对于任意事件 $A,B,C$，若 $\overline{A+B} \supset C$，则（ ）.",
            "options": "A. $\\overline{A}+\\overline{B} \\supset \\overline{C}$\nB. $\\overline{A}\\overline{B} \\supset \\overline{C}$\nC. $A+B \\subset \\overline{C}$\nD. $AB \\subset C$"
        },
        {
            "num": 2, "page": 114, "course": "概率论与数理统计", "chapter": "第1章 随机事件与概率",
            "stem": r"甲、乙两个篮球队进行比赛，假设有三种可能的结局：甲胜，乙胜与平局。考虑事件 $A = \{\text{甲胜而乙负}\}$，则 $\overline{A} = $（ ）.",
            "options": "A. $B_1 = \\{\\text{甲负而乙胜}\\}$\nB. $B_2 = \\{\\text{平局}\\}$\nC. $B_3 = \\{\\text{甲胜或平局}\\}$\nD. $B_4 = \\{\\text{乙胜或平局}\\}$"
        },
        {
            "num": 3, "page": 115, "course": "概率论与数理统计", "chapter": "第1章 随机事件与概率",
            "stem": r"对于任意事件 $A$，“$P(A) = P(\overline{A})$” 是 “$P(A) = \frac{1}{4} + [P(A)]^2$” 的（ ）.",
            "options": "A. 充分非必要条件\nB. 必要非充分条件\nC. 充分必要条件\nD. 既非充分又非必要条件"
        },
        {
            "num": 4, "page": 116, "course": "概率论与数理统计", "chapter": "第1章 随机事件与概率",
            "stem": r"一平面质点从原点出发，每次走一个单位，只有向上、向右两种走法，且向上走的概率为 $p(0 < p < 1)$。现质点走到了点 $(3,2)$，则这 5 步按照：右，上，右，上，右的方式走的概率为（ ）.",
            "options": "A. $\\frac{3}{20}$\nB. $\\frac{1}{13}$\nC. $\\frac{1}{20}$\nD. $\\frac{1}{10}$"
        },
        {
            "num": 5, "page": 117, "course": "概率论与数理统计", "chapter": "第1章 随机事件与概率",
            "stem": r"设 $A,B$ 为随机事件，$0 < P(A) < 1, 0 < P(B) < 1$，且 $P(A-B) = 0$，则（ ）.",
            "options": "A. $\\overline{A} \\supset \\overline{B}$\nB. $P(\\overline{A}) < P(\\overline{B})$\nC. $P(\\overline{B}|\\overline{A}) = 0$\nD. $P(\\overline{A}|\\overline{B}) = 1$"
        },
        {
            "num": 6, "page": 118, "course": "概率论与数理统计", "chapter": "第1章 随机事件与概率",
            "stem": r"已知 $0 < P(A) < 1$ 且 $P(B+C|A) = P(B|A) + P(C|A)$，则以下结论：\n① $P(B+C) = P(B) + P(C)$；\n② $P(B+C) = P(B|A) + P(C|A)$；\n③ $P(B+C|\\overline{A}) = P(B|\\overline{A}) + P(C|\\overline{A})$；\n④ $P(BA+CA) = P(BA) + P(CA)$。\n正确结论的个数为（ ）.",
            "options": "A. 1\nB. 2\nC. 3\nD. 4"
        },
        {
            "num": 9, "page": 121, "course": "概率论与数理统计", "chapter": "第1章 随机事件与概率",
            "stem": r"对任意事件 $A,B$，下列结论正确的是（ ）.",
            "options": "A. $P(A)P(B) \\ge P(A \\cup B)P(AB)$\nB. $P(A)+P(B) \\le 2P(AB)$\nC. $P(A)+P(AB) \\ge P(A \\cup B)$\nD. $P(A)+P(B) \\le P(A \\cup B)P(AB)$"
        },
        {
            "num": 11, "page": 123, "course": "概率论与数理统计", "chapter": "第1章 随机事件与概率",
            "stem": r"设 $P[A|(A \cup BC)] = \frac{1}{2}, P(B) = P(C) = \frac{1}{2}$，其中 $A,B$ 互不相容，$B,C$ 相互独立，则 $P(A) = $（ ）.",
            "options": "A. $\\frac{1}{4}$\nB. $\\frac{3}{4}$\nC. $\\frac{1}{2}$\nD. 1"
        }
    ]
)

# 第2章 一维随机变量及其分布
save_chapter(
    "01_基础篇/概率论与数理统计/第02章_一维随机变量及其分布.md",
    "《张宇1000题》· 基础篇 · 概率论与数理统计 · 第2章 一维随机变量及其分布",
    "本章节收录第 128 页至第 134 页共 7 道选择题。",
    [
        {
            "num": 2, "page": 128, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设随机变量 $X \sim B(n, \frac{1}{3}), Y \sim B(2n, \frac{1}{3})$，若 $P\{X \ge 1\} = \frac{5}{9}$，则 $P\{Y \ge 1\} = $（ ）.",
            "options": "A. $\\frac{5}{27}$\nB. $\\frac{16}{81}$\nC. $\\frac{64}{81}$\nD. $\\frac{65}{81}$"
        },
        {
            "num": 3, "page": 129, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设 $X \sim N(0,1), Y = X+|X|$，则 $P\{Y > 1\} = $（ ）.",
            "options": "A. $\\Phi(\\frac{1}{2})$\nB. $1-\\Phi(\\frac{1}{2})$\nC. $\\Phi(1)$\nD. $1-\\Phi(1)$"
        },
        {
            "num": 4, "page": 130, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"随机试验 $E$ 有三种两两不相容的结果 $A_1, A_2, A_3$，且三种结果发生的概率均为 $\frac{1}{3}$。将试验 $E$ 独立重复做 2 次，$X$ 表示 2 次试验中结果 $A_1$ 发生的次数，$Y$ 表示 2 次试验中结果 $A_2$ 发生的次数，则 $X+Y$ 服从（ ）.",
            "options": "A. $B(2, \\frac{1}{3})$\nB. $B(2, \\frac{2}{3})$\nC. $B(4, \\frac{1}{3})$\nD. $B(4, \\frac{2}{3})$"
        },
        {
            "num": 5, "page": 131, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设随机变量 $X,Y$ 分别服从正态分布 $N(\mu, 9), N(\mu, 4)$，记 $p_1 = P\{X \le \mu-3\}, p_2 = P\{Y \ge \mu+4\}$，则（ ）.",
            "options": "A. 对于任何实数 $\\mu$，都有 $p_1 = p_2$\nB. 对于任何实数 $\\mu$，都有 $p_1 < p_2$\nC. 对于任何实数 $\\mu$，都有 $p_1 > p_2$\nD. 对于 $\\mu$ 的个别值，有 $p_1 = p_2$"
        },
        {
            "num": 6, "page": 132, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设随机变量 $X$ 服从正态分布，其概率密度 $f(x)$ 在 $x=1$ 处有驻点，且 $f(1) = 1$，则 $X$ 服从（ ）.",
            "options": "A. $N(1, 1)$\nB. $N(1, \\frac{1}{\\sqrt{2\\pi}})$\nC. $N(1, \\frac{1}{2\\pi})$\nD. $N(0, 1)$"
        },
        {
            "num": 7, "page": 133, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设随机变量 $X$ 服从 $(0,1)$ 上的均匀分布，则 $Y = -\ln X$ 服从（ ）.",
            "options": "A. 几何分布\nB. 标准正态分布\nC. $t$ 分布\nD. 指数分布"
        },
        {
            "num": 8, "page": 134, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设随机变量 $X$ 服从正态分布 $N(1, 2)$，其分布函数和概率密度分别记作 $F(x)$ 和 $f(x)$，则下列各选项的性质中错误的是（ ）.",
            "options": "A. $f(x)$ 的曲线关于直线 $x = 1$ 对称\nB. $F(x)$ 是 $f(x)$ 在 $(-\\infty, x)$ 上的积分\nC. $F(x)$ 在点 $x = 0$ 处的值等于 $0.5$\nD. 概率密度 $f(x)$ 的最大值等于 $\\frac{1}{2\\sqrt{\\pi}}$"
        }
    ]
)

# 第3章 多维随机变量及其分布
save_chapter(
    "01_基础篇/概率论与数理统计/第03章_多维随机变量及其分布.md",
    "《张宇1000题》· 基础篇 · 概率论与数理统计 · 第3章 多维随机变量及其分布",
    "本章节收录第 138 页至第 144 页共 4 道选择题。",
    [
        {
            "num": 1, "page": 138, "course": "概率论与数理统计", "chapter": "第3章 多维随机变量及其分布",
            "stem": r"设随机变量 $X$ 和 $Y$ 相互独立且均服从分布：$\begin{pmatrix} -1 & 1 \\ q & p \end{pmatrix} (p+q=1)$，则下列随机变量服从二项分布的是（ ）.",
            "options": "A. $X+Y$\nB. $X-Y$\nC. $XY$\nD. $\\frac{X-Y}{2}-1$"
        },
        {
            "num": 2, "page": 139, "course": "概率论与数理统计", "chapter": "第3章 多维随机变量及其分布",
            "stem": r"设随机变量 $X$ 与 $Y$ 相互独立，且 $X \sim B(1, \frac{1}{2}), Y \sim N(0,1)$，则 $P\{XY \le 0\} = $（ ）.",
            "options": "A. 0\nB. $\\frac{1}{4}$\nC. $\\frac{1}{2}$\nD. $\\frac{3}{4}$"
        },
        {
            "num": 3, "page": 140, "course": "概率论与数理统计", "chapter": "第3章 多维随机变量及其分布",
            "stem": r"设随机变量 $X$ 与 $Y$ 相互独立，且 $X$ 服从二项分布 $B(1, \frac{1}{2})$，$Y$ 服从指数分布 $E(1)$，则 $P\{X+Y \ge 1\} = $（ ）.",
            "options": "A. $1+e^{-1}$\nB. $1-e^{-1}$\nC. $\\frac{1}{2}(1+e^{-1})$\nD. $\\frac{1}{2}(1-e^{-1})$"
        },
        {
            "num": 7, "page": 144, "course": "概率论与数理统计", "chapter": "第3章 多维随机变量及其分布",
            "stem": r"设随机变量 $X$ 与 $Y$ 相互独立，且均服从正态分布 $N(0, \frac{1}{2})$。记随机变量 $Z = |X-Y|$ 的概率密度为 $f(z)$，则（ ）.",
            "options": "A. $f(z) = \\frac{1}{\\sqrt{2\\pi}} e^{-\\frac{z^2}{2}}, -\\infty < z < +\\infty$\nB. $f(z) = \\sqrt{\\frac{2}{\\pi}} e^{-\\frac{z^2}{2}}, -\\infty < z < +\\infty$\nC. $f(z) = \\begin{cases} \\frac{1}{\\sqrt{2\\pi}} e^{-\\frac{z^2}{2}}, & z > 0 \\ 0, & z \\le 0 \\end{cases}$\nD. $f(z) = \\begin{cases} \\sqrt{\\frac{2}{\\pi}} e^{-\\frac{z^2}{2}}, & z > 0 \\ 0, & z \\le 0 \\end{cases}$"
        }
    ]
)

# 第4章 随机变量的数字特征
save_chapter(
    "01_基础篇/概率论与数理统计/第04章_随机变量的数字特征.md",
    "《张宇1000题》· 基础篇 · 概率论与数理统计 · 第4章 随机变量的数字特征",
    "本章节收录第 153 页至第 169 页共 14 道选择题。",
    [
        {
            "num": 2, "page": 153, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设随机变量 $X \sim E(1)$，记 $Y = \max\{X, 1\}$，则 $E(Y) = $（ ）.",
            "options": "A. 1\nB. $1-e^{-1}$\nC. $1+e^{-1}$\nD. $1+2e^{-1}$"
        },
        {
            "num": 3, "page": 154, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设随机变量 $X_1, X_2, X_3$ 的概率密度图像分别如图 (a)~图 (c) 所示，则（ ）.",
            "options": "A. $D(X_1) < D(X_2) < D(X_3)$\nB. $D(X_1) < D(X_3) < D(X_2)$\nC. $D(X_2) < D(X_1) < D(X_3)$\nD. $D(X_2) < D(X_3) < D(X_1)$"
        },
        {
            "num": 4, "page": 155, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设随机变量 $X$ 服从参数为 $p(0 < p < 1)$ 的几何分布，则 $E(\frac{1}{X}) = $（ ）.",
            "options": "A. $p(1-p)$\nB. $-p\\ln p$\nC. $-(1-p)\\ln p$\nD. $-\\frac{p\\ln p}{1-p}$"
        },
        {
            "num": 5, "page": 156, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设 10 个球中有 3 个红球，7 个白球，现从这 10 个球中无放回地抽取 3 个球，记取到白球的个数为 $X$，则 $E(X) = $（ ）.",
            "options": "A. $\\frac{7}{10}$\nB. $\\frac{21}{10}$\nC. $\\frac{7}{5}$\nD. $\\frac{21}{5}$"
        },
        {
            "num": 10, "page": 161, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设 $X,Y$ 是两个相互独立且均服从正态分布 $N(0, (\frac{1}{\sqrt{2}})^2)$ 的随机变量，则随机变量 $|X-Y|$ 的数学期望 $E(|X-Y|) = $（ ）.",
            "options": "A. $\\frac{1}{\\sqrt{3\\pi}}$\nB. $\\frac{1}{\\sqrt{2\\pi}}$\nC. $\\frac{2}{\\sqrt{\\pi}}$\nD. $\\sqrt{\\frac{2}{\\pi}}$"
        },
        {
            "num": 11, "page": 162, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设随机变量 $X$ 与 $Y$ 独立同分布，且都服从参数为 1 的指数分布。若 $Z = \begin{cases} 2X, & X \ge Y \\ Y-1, & X < Y \end{cases}$，则 $E(Z) = $（ ）.",
            "options": "A. $\\frac{2}{7}$\nB. $\\frac{7}{2}$\nC. $\\frac{7}{4}$\nD. $\\frac{4}{7}$"
        },
        {
            "num": 12, "page": 163, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"随机试验 $E$ 有三种两两不相容的结果 $A_1, A_2, A_3$，且三种结果发生的概率均为 $\frac{1}{3}$。将试验 $E$ 独立重复做 2 次，$X$ 表示 2 次试验中结果 $A_1$ 发生的次数，$Y$ 表示 2 次试验中结果 $A_2$ 发生的次数，则 $X$ 与 $Y$ 的相关系数为（ ）.",
            "options": "A. $-\\frac{1}{2}$\nB. $-\\frac{1}{3}$\nC. $\\frac{1}{3}$\nD. $\\frac{1}{2}$"
        },
        {
            "num": 13, "page": 164, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设随机变量 $X$ 和 $Y$ 的方差存在，则 $D(X+Y) = D(X)+D(Y)$ 是 $X$ 和 $Y$（ ）.",
            "options": "A. 不相关的充分非必要条件\nB. 不相关的充分必要条件\nC. 独立的充分非必要条件\nD. 独立的充分必要条件"
        },
        {
            "num": 14, "page": 165, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"已知随机变量 $X \sim U(0,4)$，实数 $c \in [0,4]$，且 $X$ 与 $|X-c|$ 不相关，则 $c = $（ ）.",
            "options": "A. 1\nB. 2\nC. 3\nD. 4"
        },
        {
            "num": 15, "page": 166, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设随机变量 $X,Y$ 独立同分布于 $\begin{pmatrix} -1 & 1 \\ \frac{1}{2} & \frac{1}{2} \end{pmatrix}$，$Z_1 = XY, Z_2 = \frac{X}{Y}$，则（ ）.",
            "options": "A. $X,Y,Z_1$ 相互独立\nB. $Y,Z_1,Z_2$ 相互独立\nC. $X,Z_1,Z_2$ 两两独立\nD. $X,Y,Z_2$ 不相互独立"
        },
        {
            "num": 16, "page": 167, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"对于任意随机变量 $X$ 和 $Y$，如果 $D(X+Y) = D(X-Y)$，则（ ）.",
            "options": "A. $X$ 和 $Y$ 相互独立\nB. $D(XY) = D(X)D(Y)$\nC. $X$ 和 $Y$ 相关\nD. $E(XY) = E(X)E(Y)$"
        },
        {
            "num": 17, "page": 168, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设随机变量 $(X_1, X_2) \sim N(0,0;\sigma_1^2,\sigma_2^2;\rho)$，$\sigma_1,\sigma_2 > 0$，且 $\sigma_1 \neq \sigma_2$。若 $Y_1 = X_1\cos\alpha+X_2\sin\alpha$ 与 $Y_2 = X_2\cos\alpha-X_1\sin\alpha$ 相互独立，$\cos 2\alpha \neq 0$，则 $\tan 2\alpha = $（ ）.",
            "options": "A. $\\rho\\frac{\\sigma_1^2\\sigma_2^2}{\\sigma_1^2-\\sigma_2^2}$\nB. $\\rho\\frac{\\sigma_1^2\\sigma_2^2}{\\sigma_2^2-\\sigma_1^2}$\nC. $2\\rho\\frac{\\sigma_1\\sigma_2}{\\sigma_1^2-\\sigma_2^2}$\nD. $2\\rho\\frac{\\sigma_1\\sigma_2}{\\sigma_2^2-\\sigma_1^2}$"
        },
        {
            "num": 18, "page": 169, "course": "概率论与数理统计", "chapter": "第4章 随机变量的数字特征",
            "stem": r"设存在非零常数 $a$ 使得 $P\{aX+Y=0\} = 1$，则随机变量 $X$ 与 $Y$ 的相关系数 $\rho$ 满足（ ）.",
            "options": "A. $\\rho = \\frac{a}{|a|}$\nB. $\\rho = -\\frac{a}{|a|}$\nC. $-1 < \\rho < 1$\nD. $|\\rho| = |a|$"
        }
    ]
)

# 第5章 大数定律与中心极限定理
save_chapter(
    "01_基础篇/概率论与数理统计/第05章_大数定律与中心极限定理.md",
    "《张宇1000题》· 基础篇 · 概率论与数理统计 · 第5章 大数定律与中心极限定理",
    "本章节收录第 175 页至第 177 页共 3 道选择题。",
    [
        {
            "num": 3, "page": 175, "course": "概率论与数理统计", "chapter": "第5章 大数定律与中心极限定理",
            "stem": r"设随机变量 $X_1, X_2, \cdots, X_n, \cdots$ 相互独立且均服从 $U[1,4]$，$\Phi(x)$ 是标准正态分布的分布函数，则 $\lim_{n \to \infty} P\left\{ \frac{2\sum_{i=1}^n X_i - 5n}{\sqrt{n}} \le x \right\} = $（ ）.",
            "options": "A. $\\Phi(x)$\nB. $\\Phi(\\sqrt{3}x)$\nC. $\\Phi(\\frac{x}{\\sqrt{3}})$\nD. $\\Phi(\\frac{2x}{\\sqrt{3}})$"
        },
        {
            "num": 4, "page": 176, "course": "概率论与数理统计", "chapter": "第5章 大数定律与中心极限定理",
            "stem": r"设生产每件产品的时间服从指数分布，且平均时间为 10 分钟，生产各件产品的时间相互独立。由中心极限定理，在 15 小时至 20 小时之间生产 100 件产品的概率约为（ ）.",
            "options": "A. $\\Phi(2)-\\Phi(1)$\nB. $2\\Phi(1)-\\Phi(2)$\nC. $\\Phi(1)+\\Phi(2)-1$\nD. $2[\\Phi(1)-\\Phi(-2)]$"
        },
        {
            "num": 5, "page": 177, "course": "概率论与数理统计", "chapter": "第5章 大数定律与中心极限定理",
            "stem": r"设有 5 个盒子，100 个球，每个球等可能地放入任一盒子中。根据中心极限定理，指定的某一个盒子中不超过 22 个球的概率近似为（ ）.",
            "options": "A. $1-\\Phi(1)$\nB. $\\Phi(1)$\nC. $1-\\Phi(0.5)$\nD. $\\Phi(0.5)$"
        }
    ]
)

# 第6章 数理统计
save_chapter(
    "01_基础篇/概率论与数理统计/第06章_数理统计.md",
    "《张宇1000题》· 基础篇 · 概率论与数理统计 · 第6章 数理统计",
    "本章节收录第 181 页至第 203 页共 14 道选择题。",
    [
        {
            "num": 1, "page": 181, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $X_1, X_2$ 是取自正态总体 $X \sim N(1,1)$ 的简单随机样本，则 $\frac{X_1-1}{|1-X_2|}$ 服从（ ）.",
            "options": "A. $t(1)$\nB. $F(1,1)$\nC. $\\chi^2(1)$\nD. $N(1,1)$"
        },
        {
            "num": 2, "page": 182, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $X_1, X_2, \cdots, X_{10}$ 是来自正态总体 $X \sim N(0, \sigma^2) (\sigma > 0)$ 的简单随机样本，$Y^2 = \frac{1}{9}\sum_{i=2}^{10} X_i^2$，则（ ）.",
            "options": "A. $X_1^2 \sim \\chi^2(1)$\nB. $Y^2 \sim \\chi^2(9)$\nC. $\\frac{X_1}{|Y|} \\sim t(9)$\nD. $\\frac{X_1^2}{Y^2} \\sim F(9,1)$"
        },
        {
            "num": 3, "page": 183, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设总体 $X$ 和 $Y$ 相互独立，且都服从正态分布 $N(0, \sigma^2)$，$X_1, \cdots, X_n$ 和 $Y_1, \cdots, Y_n$ 分别是来自总体 $X$ 和 $Y$ 且容量都为 $n$ 的两个简单随机样本，样本均值、样本方差分别为 $\overline{X}, S_X^2$ 和 $\overline{Y}, S_Y^2$，则（ ）.",
            "options": "A. $\\overline{X}-\\overline{Y} \\sim N(0, \\sigma^2)$\nB. $S_X^2+S_Y^2 \\sim \\chi^2(2n-2)$\nC. $\\frac{\\overline{X}-\\overline{Y}}{\\sqrt{S_X^2+S_Y^2}} \\sim t(2n-2)$\nD. $\\frac{S_X^2}{S_Y^2} \\sim F(n-1, n-1)$"
        },
        {
            "num": 4, "page": 184, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设随机变量 $X \sim N(0,1), Y \sim N(0,1)$，则（ ）.",
            "options": "A. $X+Y$ 服从正态分布\nB. $X^2+Y^2$ 服从 $\\chi^2$ 分布\nC. $X^2/Y^2$ 服从 $F$ 分布\nD. $X^2$ 和 $Y^2$ 服从 $\\chi^2$ 分布"
        },
        {
            "num": 5, "page": 185, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $n$ 为正整数，随机变量 $X \sim t(n), Y \sim F(1,n)$，常数 $c$ 满足 $P\{X > c\} = \frac{2}{5}$，则 $P\{Y \le c^2\} = $（ ）.",
            "options": "A. $\\frac{1}{5}$\nB. $\\frac{2}{5}$\nC. $\\frac{3}{5}$\nD. $\\frac{4}{5}$"
        },
        {
            "num": 6, "page": 186, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $X_1, X_2, \cdots, X_n (n \ge 2)$ 为来自标准正态总体 $X$ 的简单随机样本，记 $\overline{X} = \frac{1}{n}\sum_{i=1}^n X_i, S^2 = \frac{1}{n-1}\sum_{i=1}^n (X_i-\overline{X})^2, Y = \overline{X}-S$，则 $E(Y^2) = $（ ）.",
            "options": "A. $1-\\frac{1}{n}$\nB. $1+\\frac{1}{n}$\nC. $1-\\frac{1}{n-1}$\nD. $1+\\frac{1}{n-1}$"
        },
        {
            "num": 7, "page": 187, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $X,Y$ 独立同分布于 $N(0, \sigma^2)$，$X_1, \cdots, X_9$ 与 $Y_1, \cdots, Y_{11}$ 是分别来自总体 $X$ 与 $Y$ 的简单随机样本，样本方差分别为 $S_X^2$ 与 $S_Y^2$，记 $S_1^2 = \frac{1}{2}(S_X^2+S_Y^2), S_2^2 = \frac{1}{9}(4S_X^2+5S_Y^2)$，则方差最小的是（ ）.",
            "options": "A. $S_X^2$\nB. $S_Y^2$\nC. $S_1^2$\nD. $S_2^2$"
        },
        {
            "num": 8, "page": 188, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设总体 $X$ 的概率密度为 $f(x;\sigma) = \begin{cases} \frac{2x}{\sigma} e^{-\frac{x^2}{\sigma}}, & x > 0 \\ 0, & x \le 0 \end{cases}$，其中 $\sigma$ 为大于零的未知参数。已知 $X_1, X_2, \cdots, X_n$ 是来自总体 $X$ 的简单随机样本，则 $\sigma$ 的最大似然估计量为（ ）.",
            "options": "A. $\\hat{\\sigma} = \\frac{1}{n-1} \\sum_{i=1}^n X_i$\nB. $\\hat{\\sigma} = \\frac{1}{n-1} \\sum_{i=1}^n X_i^2$\nC. $\\hat{\\sigma} = \\frac{1}{n} \\sum_{i=1}^n X_i$\nD. $\\hat{\\sigma} = \\frac{1}{n} \\sum_{i=1}^n X_i^2$"
        },
        {
            "num": 14, "page": 194, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"在数集 $\Omega = \{0,1,2,\cdots,N\}$ 中有放回地抽取 $n$ 次，得 $X_1, X_2, \cdots, X_n$，则 $N$ 的最大似然估计量是（ ）.",
            "options": "A. $\\max\\{X_1, X_2, \\cdots, X_n\\}$\nB. $\\min\\{X_1, X_2, \\cdots, X_n\\}$\nC. $\\frac{1}{n} \\sum_{i=1}^n X_i$\nD. $n$"
        },
        {
            "num": 16, "page": 196, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设总体 $X$ 的数学期望 $E(X) = 0$，方差 $D(X) = \sigma^2$，而 $X_1, X_2, \cdots, X_n (n > 2)$ 是来自总体 $X$ 的简单随机样本，$\overline{X} = \frac{1}{n}\sum_{i=1}^n X_i, S^2 = \frac{1}{n-1}\sum_{i=1}^n (X_i-\overline{X})^2$，则下列属于 $\sigma^2$ 的无偏估计量的是（ ）.",
            "options": "A. $n\\overline{X}^2+S^2$\nB. $\\frac{1}{2}(n\\overline{X}^2+S^2)$\nC. $\\frac{1}{3}(n\\overline{X}^2+S^2)$\nD. $\\frac{1}{4}(n\\overline{X}^2+S^2)$"
        },
        {
            "num": 17, "page": 197, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $\mu$ 是总体 $X$ 的数学期望，$\sigma$ 是总体 $X$ 的标准差，$X_1, X_2, \cdots, X_n$ 是来自总体 $X$ 的简单随机样本，则总体方差 $\sigma^2$ 的无偏估计量是（ ）.",
            "options": "A. $\\frac{1}{n-1} \\sum_{i=1}^n (X_i-\\mu)^2, \\mu \\text{未知}$\nB. $\\frac{1}{n} \\sum_{i=1}^n (X_i-\\mu)^2, \\mu \\text{未知}$\nC. $\\frac{1}{n-1} \\sum_{i=1}^n (X_i-\\mu)^2, \\mu \\text{已知}$\nD. $\\frac{1}{n} \\sum_{i=1}^n (X_i-\\mu)^2, \\mu \\text{已知}$"
        },
        {
            "num": 18, "page": 198, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $\sigma$ 是总体 $X$ 的标准差，$X_1, X_2, \cdots, X_n$ 是来自总体 $X$ 的简单随机样本，则样本标准差 $S$ 是总体标准差 $\sigma$ 的（ ）.",
            "options": "A. 无偏估计量\nB. 最大似然估计量\nC. 相合估计量\nD. 最小方差估计量"
        },
        {
            "num": 21, "page": 201, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设一批零件的长度服从正态分布 $N(\mu, \sigma^2)$，其中 $\sigma^2$ 已知，$\mu$ 未知。现从中随机抽取 $n$ 个零件，测得样本均值为 $\overline{x}$，则当置信度为 $0.90$ 时，$\mu$ 大于 $\mu_0$ 的接受条件为（ ）.",
            "options": "A. $\\overline{x} > \\mu_0 - \\frac{\\sigma}{\\sqrt{n}} z_{0.10}$\nB. $\\overline{x} > \\mu_0 + \\frac{\\sigma}{\\sqrt{n}} z_{0.05}$\nC. $\\overline{x} > \\mu_0 + \\frac{\\sigma}{\\sqrt{n}} z_{0.10}$\nD. $\\overline{x} > \\mu_0 - \\frac{\\sigma}{\\sqrt{n}} z_{0.05}$"
        },
        {
            "num": 22, "page": 202, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $X_1, X_2, \cdots, X_n$ 是来自总体 $X$ 的简单随机样本，$\overline{X}$ 为样本均值，$E(X) = \theta$。检验 $H_0: \theta = 0; H_1: \theta \neq 0$，且拒绝域 $W_1 = \{|\overline{X}| > 1\}$ 和 $W_2 = \{|\overline{X}| > 2\}$ 分别对应显著性水平 $\alpha_1$ 和 $\alpha_2$，则（ ）.",
            "options": "A. $\\alpha_1 = \\alpha_2$\nB. $\\alpha_1 > \\alpha_2$\nC. $\\alpha_1 < \\alpha_2$\nD. $\\alpha_1$ 和 $\\alpha_2$ 的大小关系不确定"
        },
        {
            "num": 23, "page": 203, "course": "概率论与数理统计", "chapter": "第6章 数理统计",
            "stem": r"设 $X_1, X_2$ 是来自正态总体 $N(\mu, 1)$ 的简单随机样本，并设原假设 $H_0: \mu = 2$，备择假设 $H_1: \mu = 4$。若拒绝域为 $W = \{\overline{X} > 3\}, \overline{X} = \frac{1}{2}\sum_{i=1}^2 X_i$，记 $\alpha, \beta$ 分别为犯第一类错误和第二类错误的概率，则（ ）.",
            "options": "A. $\\alpha = \\beta = 1 - \\Phi(\\sqrt{2})$\nB. $\\alpha = 1 - \\Phi(\\sqrt{2}), \\beta = \\Phi(\\sqrt{2})$\nC. $\\alpha = \\Phi(\\sqrt{2}), \\beta = 1 - \\Phi(\\sqrt{2})$\nD. $\\alpha = \\beta = \\Phi(\\sqrt{2})$"
        }
    ]
)

print("Finished 基础篇 · 概率论与数理统计")
