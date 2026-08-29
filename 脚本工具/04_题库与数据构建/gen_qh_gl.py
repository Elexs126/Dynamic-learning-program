# -*- coding: utf-8 -*-
"""
Generator for Zhang Yu 1000: 强化篇 · 概率论与数理统计 (9章 选择题)
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

# 第1章 随机事件和概率
save_chapter(
    "02_强化篇/概率论与数理统计/第01章_随机事件和概率.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第1章 随机事件和概率",
    "本章节收录第 317 页至第 320 页共 4 道选择题。",
    [
        {
            "num": 1, "page": 317, "course": "概率论与数理统计", "chapter": "第1章 随机事件和概率",
            "stem": r"设口袋中有 10 个球，其中 6 个红球，4 个白球，每次不放回地从中任取一个，取两次。若取出的两个球中有 1 个是白球，则两个都是白球的概率为（ ）.",
            "options": "A. $\\frac{1}{3}$\nB. $\\frac{1}{5}$\nC. $\\frac{1}{4}$\nD. $\\frac{1}{6}$"
        },
        {
            "num": 2, "page": 318, "course": "概率论与数理统计", "chapter": "第1章 随机事件和概率",
            "stem": r"设 $A,B$ 为随机事件，且 $0 < P(B) < 1$。下列命题中为假命题的是（ ）.",
            "options": "A. 若 $P(A|B) > P(A)$，则 $P(\\overline{A}|\\overline{B}) > P(\\overline{A})$\nB. 若 $P(A|B) = P(A)$，则 $P(A|\\overline{B}) = P(A)$\nC. 若 $P(A|B) > P(A|\\overline{B})$，则 $P(A|B) > P(A)$\nD. 若 $P(A|A \\cup B) > P(\\overline{A}|A \\cup B)$，则 $P(A) > P(B)$"
        },
        {
            "num": 3, "page": 319, "course": "概率论与数理统计", "chapter": "第1章 随机事件和概率",
            "stem": r"设随机事件 $A,B$ 满足 $0 < P(A) < 1, 0 < P(B) < 1$，则 $P(AB) > P(A)P(B)$ 的充要条件是（ ）.",
            "options": "A. $P(A\\overline{B}) > P(A)P(\\overline{B})$\nB. $P(\\overline{A}\\overline{B}) > P(\\overline{A})P(\\overline{B})$\nC. $P(B|\\overline{A}) > P(B|A)$\nD. $P(A|\\overline{B}) > P(A|B)$"
        },
        {
            "num": 4, "page": 320, "course": "概率论与数理统计", "chapter": "第1章 随机事件和概率",
            "stem": r"对于下列命题：\n① 若事件 $A,B$ 相互独立，且 $B,C$ 相互独立，则 $A,C$ 相互独立；\n② 若事件 $A,B$ 相互独立，且 $C \subset A, D \subset B$，则 $C,D$ 相互独立。\n说法正确的是（ ）.",
            "options": "A. ①正确，②不正确\nB. ②正确，①不正确\nC. ①②都正确\nD. ①②都不正确"
        }
    ]
)

# 第2章 一维随机变量及其分布
save_chapter(
    "02_强化篇/概率论与数理统计/第02章_一维随机变量及其分布.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第2章 一维随机变量及其分布",
    "本章节收录第 323 页至第 329 页共 5 道选择题。",
    [
        {
            "num": 1, "page": 323, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设 $X$ 是随机变量，$s,t$ 是正数，$m,n$ 是正整数。\n① 若 $X \sim G(p)$，则 $P\{X > m+n \mid X > m\}$ 与 $m$ 无关；\n② 若 $X \sim P\{X=k\} = \frac{1}{k(k+1)}, k=1,2,\cdots$，则 $P\{X \ge 2n \mid X \ge n\}$ 与 $n$ 无关；\n③ 若 $X \sim E(\lambda)$，则 $P\{X > s+t \mid X > s\}$ 与 $s$ 无关；\n④ 若 $X \sim f(x) = \begin{cases} \frac{1}{x^2}, & x > 1 \\ 0, & \text{其他} \end{cases}$，则当 $t > 1$ 时，$P\{X \ge 2t \mid X \ge t\}$ 与 $t$ 无关。\n上述结论中正确的个数为（ ）.",
            "options": "A. 1\nB. 2\nC. 3\nD. 4"
        },
        {
            "num": 2, "page": 324, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设 $X$ 服从参数为 $\lambda(\lambda > 0)$ 的泊松分布，$p_1, p_2, p_3$ 分别是 $X$ 取整数、偶数与奇数的概率，则（ ）.",
            "options": "A. $p_1 = p_2 = p_3$\nB. $p_1 = p_2 > p_3$\nC. $p_1 > p_2 > p_3$\nD. $p_1 > p_2 = p_3$"
        },
        {
            "num": 3, "page": 325, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设 $X,Y$ 分别服从参数为 $n,m$ 的泊松分布，且 $n > m$，$F_X(x), F_Y(y)$ 分别是 $X,Y$ 的分布函数，$-\infty < z < +\infty$，则（ ）.",
            "options": "A. $P\{X \ge Y\} = 1$\nB. $P\{X \le Y\} = 1$\nC. $F_X(z) \ge F_Y(z)$\nD. $F_X(z) \le F_Y(z)$"
        },
        {
            "num": 4, "page": 326, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设随机变量 $X$ 的概率密度 $f(x) \neq 1 (x \in \mathbb{R})$，则 $X$ 不可能服从（ ）.",
            "options": "A. $N(1,1)$\nB. $N(0,2)$\nC. $E(2)$\nD. $U(-1,1)$"
        },
        {
            "num": 7, "page": 329, "course": "概率论与数理统计", "chapter": "第2章 一维随机变量及其分布",
            "stem": r"设随机变量 $X$ 的概率分布为 $P\{X=1\} = a, P\{X=2\} = 1-a$。在给定 $X=i$ 的条件下，随机变量 $Y$ 服从均匀分布 $U(0,i) (i=1,2)$，且当 $0 \le y < 1$ 时，$Y$ 的分布函数为 $F_Y(y) = \frac{2}{3}y$，则 $a = $（ ）.",
            "options": "A. $\\frac{1}{3}$\nB. $\\frac{2}{3}$\nC. $\\frac{1}{2}$\nD. $\\frac{1}{4}$"
        }
    ]
)

# 第3章 一维随机变量函数的分布
save_chapter(
    "02_强化篇/概率论与数理统计/第03章_一维随机变量函数的分布.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第3章 一维随机变量函数的分布",
    "本章节收录第 332 页至第 334 页共 3 道选择题。",
    [
        {
            "num": 1, "page": 332, "course": "概率论与数理统计", "chapter": "第3章 一维随机变量函数的分布",
            "stem": r"设 $X \sim E(1), Y = [X+1]$，其中 $[\cdot]$ 表示取整符号，则 $Y$ 服从（ ）.",
            "options": "A. 参数为 $e^{-1}$ 的几何分布\nB. 参数为 $1-e^{-1}$ 的几何分布\nC. 参数为 $e^{-1}$ 的泊松分布\nD. 参数为 $1-e^{-1}$ 的泊松分布"
        },
        {
            "num": 2, "page": 333, "course": "概率论与数理统计", "chapter": "第3章 一维随机变量函数的分布",
            "stem": r"设 $X,Y$ 与 $X+Y$ 均服从同一种分布，其中 $X,Y$ 相互独立，则下列分布一定可以成立的是（ ）.",
            "options": "A. 均匀分布\nB. 泊松分布\nC. 指数分布\nD. 二项分布"
        },
        {
            "num": 3, "page": 334, "course": "概率论与数理统计", "chapter": "第3章 一维随机变量函数的分布",
            "stem": r"设随机变量 $X \sim N(0,1)$，则与 $Y = \begin{cases} X, & |X| \le 1 \\ -X, & |X| > 1 \end{cases}$ 同分布的是（ ）.",
            "options": "A. $X$\nB. $2X$\nC. $\\frac{X+Y}{2}$\nD. $X+Y$"
        }
    ]
)

# 第4章 多维随机变量及其分布
save_chapter(
    "02_强化篇/概率论与数理统计/第04章_多维随机变量及其分布.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第4章 多维随机变量及其分布",
    "本章节收录第 339 页至第 341 页共 3 道选择题。",
    [
        {
            "num": 1, "page": 339, "course": "概率论与数理统计", "chapter": "第4章 多维随机变量及其分布",
            "stem": r"设 $X,Y$ 独立同分布，$P\{X=k\} = \frac{1}{a^k}, k=1,2,\cdots$，则 $P\{X > Y\} = $（ ）.",
            "options": "A. $\\frac{1}{2}$\nB. $\\frac{1}{2a}$\nC. $\\frac{1}{3}$\nD. $\\frac{1}{3a}$"
        },
        {
            "num": 2, "page": 340, "course": "概率论与数理统计", "chapter": "第4章 多维随机变量及其分布",
            "stem": r"设随机变量 $X,Y$ 相互独立，且 $X \sim U(-2,4), Y \sim \begin{pmatrix} -2 & 2 \\ \frac{3}{4} & \frac{1}{4} \end{pmatrix}$，则 $P\{XY > 2\} = $（ ）.",
            "options": "A. $\\frac{1}{6}$\nB. $\\frac{1}{4}$\nC. $\\frac{1}{3}$\nD. $\\frac{1}{2}$"
        },
        {
            "num": 3, "page": 341, "course": "概率论与数理统计", "chapter": "第4章 多维随机变量及其分布",
            "stem": r"设二维随机变量 $(X,Y)$ 的概率密度为 $f(x,y) = \begin{cases} \frac{1}{4}, & -1 \le x < 1, 0 \le y < 2 \\ 0, & \text{其他} \end{cases}$，$g(x_1,x_2,x_3) = x_1^2+2x_2^2+Yx_3^2+2x_1x_2+2Xx_1x_3$ 正定的概率为（ ）.",
            "options": "A. $\\frac{2}{3}$\nB. $\\frac{1}{2}$\nC. $\\frac{1}{3}$\nD. $\\frac{1}{4}$"
        }
    ]
)

# 第5章 多维随机变量函数的分布
save_chapter(
    "02_强化篇/概率论与数理统计/第05章_多维随机变量函数的分布.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第5章 多维随机变量函数的分布",
    "本章节收录第 346 页至第 349 页共 4 道选择题。",
    [
        {
            "num": 1, "page": 346, "course": "概率论与数理统计", "chapter": "第5章 多维随机变量函数的分布",
            "stem": r"设 $X_1, X_2$ 是来自标准正态总体 $X$ 的简单随机样本，则 $Y = \frac{X_1}{X_2}$ 的概率密度 $f_Y(y) = $（ ）.",
            "options": "A. $\\frac{1}{\\pi(1+y^2)}$\nB. $\\frac{1}{\\pi(1+y)}$\nC. $\\frac{1}{1+y^2}$\nD. $\\frac{1}{\\sqrt{\\pi}} e^{-y^2}$"
        },
        {
            "num": 2, "page": 347, "course": "概率论与数理统计", "chapter": "第5章 多维随机变量函数的分布",
            "stem": r"设 $X_1, X_2$ 相互独立，$X_1 \sim \begin{pmatrix} 1 & 0 \\ \frac{1}{2} & \frac{1}{2} \end{pmatrix}, X_2 \sim N(0,1), Y = 2X_1X_2-X_2$，则 $Y$ 的分布函数为（ ）.",
            "options": "A. $1-\\Phi(2y)$\nB. $1-\\Phi(y)$\nC. $\\Phi(2y)$\nD. $\\Phi(y)$"
        },
        {
            "num": 3, "page": 348, "course": "概率论与数理统计", "chapter": "第5章 多维随机变量函数的分布",
            "stem": r"设 $X,Y$ 独立同分布于参数为 $\lambda$ 的指数分布，令 $Z = \max\{X,Y\}$，则与 $Z$ 同分布的是（ ）.",
            "options": "A. $\\frac{X+Y}{2}$\nB. $\\frac{2X+Y}{2}$\nC. $\\frac{2X+Y}{3}$\nD. $Y$"
        },
        {
            "num": 4, "page": 349, "course": "概率论与数理统计", "chapter": "第5章 多维随机变量函数的分布",
            "stem": r"设随机变量 $X,Y$ 独立同分布于 $E(\lambda)$，其中 $\lambda > 0$，$F(x)$ 为 $X$ 的分布函数，则与 $F(X)$ 同分布的是（ ）.",
            "options": "A. $\\frac{2X}{X+Y}$\nB. $\\frac{X}{Y}$\nC. $\\frac{X+Y}{2X}$\nD. $\\frac{Y}{X+Y}$"
        }
    ]
)

# 第6章 数字特征
save_chapter(
    "02_强化篇/概率论与数理统计/第06章_数字特征.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第6章 数字特征",
    "本章节收录第 358 页至第 376 页共 9 道选择题。",
    [
        {
            "num": 1, "page": 358, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"将 2 个红球和 1 个白球随机放入 3 个盒子中，每个盒子可放任意多个球，记 $X$ 为没有红球的盒子个数，则 $E(X) = $（ ）.",
            "options": "A. $\\frac{17}{9}$\nB. $\\frac{4}{9}$\nC. $\\frac{3}{4}$\nD. $\\frac{4}{3}$"
        },
        {
            "num": 2, "page": 359, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"设 $X$ 服从参数为 1 的泊松分布，则 $E(\\frac{1}{X+1}) = $（ ）.",
            "options": "A. $\\frac{1}{e}$\nB. $1-\\frac{1}{e}$\nC. $\\frac{2}{e}$\nD. $1+\\frac{1}{e}$"
        },
        {
            "num": 3, "page": 360, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"设随机变量 $X$ 服从参数为 $\mu, \sigma^2$ 的正态分布，其概率密度为 $f(x)$，则 $\int_{-\infty}^{+\infty} f(x)\ln f(x) dx$（ ）.",
            "options": "A. 与 $\\mu$ 有关，与 $\\sigma$ 无关\nB. 与 $\\mu$ 有关，与 $\\sigma$ 有关\nC. 与 $\\mu$ 无关，与 $\\sigma$ 无关\nD. 与 $\\mu$ 无关，与 $\\sigma$ 有关"
        },
        {
            "num": 7, "page": 364, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"设总体 $X$ 服从参数为 1 的指数分布，$X_1, X_2, \cdots, X_n$ 为来自总体 $X$ 的简单随机样本，记 $\nu_n(1)$ 为 $n$ 个观测值中不大于 1 的个数，则 $\frac{\nu_n(1)}{n}$ 的方差为（ ）.",
            "options": "A. $\\frac{e-1}{ne^2}$\nB. $\\frac{e-1}{ne}$\nC. $\\frac{e(e-1)}{n}$\nD. $\\frac{e-1}{n}$"
        },
        {
            "num": 15, "page": 372, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"独立重复抛掷一枚均匀硬币两次，记 $X_i = \begin{cases} 1, & \text{出现正面} \\ 0, & \text{出现反面} \end{cases} (i=1,2)$，则 $X_1+X_2$ 与 $X_1-X_2$（ ）.",
            "options": "A. 独立，不相关\nB. 不独立，不相关\nC. 独立，相关\nD. 不独立，相关"
        },
        {
            "num": 16, "page": 373, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"设随机变量 $(X,Y)$ 在椭圆域 $\frac{x^2}{a^2}+\frac{y^2}{b^2} \le 1 (a > 0, b > 0)$ 上服从均匀分布，则（ ）.",
            "options": "A. $X$ 在区间 $[-a,a]$ 上均匀分布\nB. $X$ 和 $Y$ 必不相关\nC. $Y$ 在区间 $[-b,b]$ 上均匀分布\nD. $X$ 和 $Y$ 相互独立"
        },
        {
            "num": 17, "page": 374, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"设连续型随机变量 $X$ 与 $Y$ 独立同分布，且其分布函数 $F(x)$ 为严格单调增加函数。若 $E(X)$ 存在，且 $E(|X-Y|) = 1$，则 $X$ 与 $F(X)$ 的协方差为（ ）.",
            "options": "A. 0\nB. $\\frac{1}{4}$\nC. $\\frac{1}{2}$\nD. 1"
        },
        {
            "num": 18, "page": 375, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"设随机变量 $X,Y$ 独立同分布于参数为 1 的指数分布，令 $Z = \max\{X,Y\}, W = \min\{X,Y\}$，则 $Z$ 与 $W$ 的相关系数为（ ）.",
            "options": "A. $\\frac{\\sqrt{2}}{2}$\nB. $\\frac{\\sqrt{3}}{3}$\nC. $\\frac{\\sqrt{5}}{5}$\nD. 1"
        },
        {
            "num": 19, "page": 376, "course": "概率论与数理统计", "chapter": "第6章 数字特征",
            "stem": r"设总体 $X$ 服从参数为 $\lambda(\lambda > 0)$ 的泊松分布，$X_1, X_2, \cdots, X_n$ 为来自总体 $X$ 的简单随机样本，且对任意的正数 $\varepsilon$，有 $\lim_{n \to \infty} P\left\{ \left|\frac{1}{n}\sum_{i=1}^n X_i^2 - 2\right| < \varepsilon \right\} = 1$，则 $D[|X-D(X)|] = $（ ）.",
            "options": "A. $1-\\frac{2}{e}$\nB. $1+\\frac{2}{e}$\nC. $1-\\frac{4}{e^2}$\nD. $1+\\frac{4}{e^2}$"
        }
    ]
)

# 第7章 大数定律与中心极限定理
save_chapter(
    "02_强化篇/概率论与数理统计/第07章_大数定律与中心极限定理.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第7章 大数定律与中心极限定理",
    "本章节收录第 379 页至第 381 页共 2 道选择题。",
    [
        {
            "num": 1, "page": 379, "course": "概率论与数理统计", "chapter": "第7章 大数定律与中心极限定理",
            "stem": r"设 $X_1, X_2, \cdots, X_n$ 是来自总体 $X \sim \begin{pmatrix} 0 & 1 & 2 & 3 \\ \frac{1}{16} & \frac{3}{8} & \frac{1}{16} & \frac{1}{2} \end{pmatrix}$ 的简单随机样本，若取值为 2 的样本个数 $K$ 满足 $\lim_{n \to \infty} P\left\{ \frac{K-a}{b} \le x \right\} = \Phi(x)$，其中 $\Phi(x)$ 为标准正态分布函数，则 $a,b$ 分别是（ ）.",
            "options": "A. $\\frac{1}{16}, \\frac{\\sqrt{15}}{16}$\nB. $\\frac{n}{16}, \\frac{\\sqrt{15n}}{16}$\nC. $\\frac{1}{16}, \\frac{\\sqrt{15n}}{16}$\nD. $\\frac{n}{16}, \\frac{\\sqrt{15}}{16}$"
        },
        {
            "num": 3, "page": 381, "course": "概率论与数理统计", "chapter": "第7章 大数定律与中心极限定理",
            "stem": r"设总体 $X$ 服从参数为 1 的泊松分布，$X_1, X_2, \cdots, X_n, \cdots$ 为来自总体 $X$ 的简单随机样本。记 $\nu_n(1)$ 为 $n$ 个观测值中不大于 1 的个数，则 $\frac{\nu_n(1)}{n}$ 依概率收敛于（ ）.",
            "options": "A. $\\frac{1}{e}$\nB. $\\frac{2}{e}$\nC. $1-\\frac{1}{e}$\nD. $1-\\frac{2}{e}$"
        }
    ]
)

# 第8章 统计量及其分布
save_chapter(
    "02_强化篇/概率论与数理统计/第08章_统计量及其分布.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第8章 统计量及其分布",
    "本章节收录第 383 页至第 393 页共 10 道选择题。",
    [
        {
            "num": 1, "page": 383, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设 $X \sim B(1, \frac{1}{2})$，$X_1, X_2, X_3$ 为来自总体 $X$ 的简单随机样本，$\overline{X}$ 为样本均值，则 $P\{\overline{X} > \frac{1}{3}\} = $（ ）.",
            "options": "A. $\\frac{3}{8}$\nB. $\\frac{1}{2}$\nC. $\\frac{5}{8}$\nD. $\\frac{7}{8}$"
        },
        {
            "num": 2, "page": 384, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设 $X_1, X_2, \cdots, X_n$ 是来自总体 $X \sim B(1, \frac{1}{5})$ 的简单随机样本，$\overline{X} = \frac{1}{n}\sum_{i=1}^n X_i$，若 $E[(\overline{X}-\frac{1}{5})^2] < 0.01$，则样本容量 $n$ 的最小值为（ ）.",
            "options": "A. 17\nB. 18\nC. 19\nD. 20"
        },
        {
            "num": 3, "page": 385, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设 $X_1, \cdots, X_n$ 与 $Y_1, \cdots, Y_n$ 是来自正态总体 $N(\mu, \sigma^2)$ 的两个相互独立的简单随机样本，$\overline{X} = \frac{1}{n}\sum_{i=1}^n X_i, \overline{Y} = \frac{1}{n}\sum_{i=1}^n Y_i$，且满足 $P\{|\overline{X}-\overline{Y}| > \sigma\} \le 0.05, \Phi(1.96) = 0.975$，则样本容量 $n$ 的最小值为（ ）.",
            "options": "A. 7\nB. 8\nC. 9\nD. 10"
        },
        {
            "num": 4, "page": 386, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设 $X_1, X_2, \cdots, X_n$ 是来自总体 $N(0,1)$ 的简单随机样本，记 $\overline{X} = \frac{1}{n}\sum_{i=1}^n X_i, S^2 = \frac{1}{n-1}\sum_{i=1}^n (X_i-\overline{X})^2, T = (\overline{X}+1)(S^2+1)$，则 $E(T)$ 的值为（ ）.",
            "options": "A. 0\nB. 1\nC. 2\nD. 4"
        },
        {
            "num": 5, "page": 387, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设 $X_1, X_2, \cdots, X_{10}$ 是来自标准正态总体 $X$ 的简单随机样本，$Y = \frac{9}{10}(X_{10}-\frac{1}{9}\sum_{i=1}^9 X_i)^2$，则 $D(Y) = $（ ）.",
            "options": "A. 2\nB. 1\nC. $\\frac{1}{100}$\nD. $\\frac{81}{100}$"
        },
        {
            "num": 6, "page": 388, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设 $X_1, X_2, \cdots, X_n (n \ge 2)$ 为来自正态总体 $X$ 的简单随机样本，$E(X) = \mu, D(X) = \sigma^2, \sigma > 0$，记 $Y = \frac{1}{n}\sum_{i=1}^n |X_i-\mu|$，则 $D(Y) = $（ ）.",
            "options": "A. $\\frac{\\sigma^2}{n}(1-\\frac{2}{\\pi})$\nB. $\\frac{\\sigma^2}{n}(1-\\frac{\\pi}{2})$\nC. $\\frac{\\sigma^2}{n^2}(1-\\frac{2}{\\pi})$\nD. $\\frac{\\sigma^2}{n^2}(1-\\frac{\\pi}{2})$"
        },
        {
            "num": 8, "page": 390, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设总体 $(X,Y)$ 服从 $N(0,0; 1,2; 1)$，$(X_1,Y_1), (X_2,Y_2)$ 是来自总体 $(X,Y)$ 的简单随机样本，$\overline{X} = \frac{X_1+X_2}{2}, \overline{Y} = \frac{Y_1+Y_2}{2}$，则 $E[(\overline{X}-\overline{Y})^2] = $（ ）.",
            "options": "A. $\\frac{3}{2}$\nB. $\\frac{3}{2}-\\sqrt{2}$\nC. $\\frac{3}{2}-\\frac{\\sqrt{2}}{2}$\nD. $\\frac{3}{2}+\\frac{\\sqrt{2}}{2}$"
        },
        {
            "num": 9, "page": 391, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设随机变量 $X \sim N(0,4)$，若 $X_1, X_2, \cdots, X_n (n > 2)$ 是来自总体 $X$ 的简单随机样本，则（ ）.",
            "options": "A. $\\frac{1}{2n}(\\sum_{i=1}^n X_i)^2 \\sim \\chi^2(1)$\nB. $\\frac{1}{16}\\sum_{i=1}^n X_i^2 \\sim \\chi^2(n)$\nC. $\\frac{(n-1)X_n^2}{\\sum_{i=1}^n X_i^2} \\sim t(n-1)$\nD. $\\frac{(n-1)X_1^2}{\\sum_{i=2}^n X_i^2} \\sim F(1,n-1)$"
        },
        {
            "num": 10, "page": 392, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"已知随机变量 $X,Y$，且 $(X,Y)$ 的概率密度为 $f(x,y) = \frac{1}{4\pi} e^{-\frac{x^2(y-1)^2}{8}}$，则 $\frac{4X^2}{(Y-1)^2}$ 服从（ ）.",
            "options": "A. $\\chi^2(2)$\nB. $t(1)$\nC. $N(0, 2^2)$\nD. $F(1,1)$"
        },
        {
            "num": 11, "page": 393, "course": "概率论与数理统计", "chapter": "第8章 统计量及其分布",
            "stem": r"设随机变量 $X_1, X_2, X_3, X_4$ 相互独立且都服从标准正态分布 $N(0,1)$，已知 $Y = \frac{X_1^2+X_2^2}{X_3^2+X_4^2}$，对给定的 $\alpha (0 < \alpha < 1)$，数 $y_\alpha$ 满足 $P\{Y > y_\alpha\} = \alpha$，则有（ ）.",
            "options": "A. $y_\\alpha y_{1-\\alpha} = 1$\nB. $y_\\alpha y_{\\frac{\\alpha}{1-2}} = 1$\nC. $y_\\alpha y_{1-\\alpha} = \\frac{1}{2}$\nD. $y_\\alpha y_{1-\\frac{\\alpha}{2}} = \\frac{1}{2}$"
        }
    ]
)

# 第9章 参数估计与假设检验
save_chapter(
    "02_强化篇/概率论与数理统计/第09章_参数估计与假设检验.md",
    "《张宇1000题》· 强化篇 · 概率论与数理统计 · 第9章 参数估计与假设检验",
    "本章节收录第 395 页至第 424 页共 11 道选择题。",
    [
        {
            "num": 1, "page": 395, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设 $X_1, X_2, \cdots, X_n$ 是来自总体 $X$ 的简单随机样本，总体 $X$ 的概率分布为 $P\{X=k\} = -\frac{\theta^k}{k\ln(1-\theta)}, k=1,2,\cdots$，其中 $\theta(0 < \theta < 1)$ 是未知参数，$\mu_m = \frac{1}{n}\sum_{i=1}^n X_i^m, m=1,2,3$，则 $\theta$ 的矩估计量为（ ）.",
            "options": "A. $1+\\frac{\\mu_1}{\\mu_2}$\nB. $1-\\frac{\\mu_1}{\\mu_2}$\nC. $1+\\frac{\\mu_2}{\\mu_3}$\nD. $1-\\frac{\\mu_2}{\\mu_3}$"
        },
        {
            "num": 2, "page": 396, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设袋中红球数与黑球数之比为 $r$，且无其他颜色的球，现有放回地抽取 $n$ 次，每次取一球，共取出 $k$ 个红球，则 $r$ 的最大似然估计值为（ ）.",
            "options": "A. $\\frac{n}{k}$\nB. $\\frac{n-k}{k}$\nC. $\\frac{k}{n}$\nD. $\\frac{k}{n-k}$"
        },
        {
            "num": 3, "page": 397, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设 $(X_1,Y_1), (X_2,Y_2), \cdots, (X_n,Y_n)$ 是来自总体 $(X,Y)$ 的简单随机样本，且 $(X,Y) \sim f(x,y) = \begin{cases} \frac{1}{2\theta^2} e^{-\frac{2x+y}{2\theta}}, & x > 0, y > 0 \\ 0, & \text{其他} \end{cases}$，其中 $\theta$ 为大于 0 的参数。记 $\overline{X} = \frac{1}{n}\sum_{i=1}^n X_i, \overline{Y} = \frac{1}{n}\sum_{j=1}^n Y_j$，则 $\theta$ 的最大似然估计量 $\hat{\theta}$ 与 $D(\hat{\theta})$ 分别为（ ）.",
            "options": "A. $\\overline{X}+\\frac{\\overline{Y}}{2}, \\frac{\\theta^2}{4n}$\nB. $\\frac{\\overline{X}}{2}+\\frac{\\overline{Y}}{4}, \\frac{\\theta^2}{2n}$\nC. $\\overline{X}+\\frac{\\overline{Y}}{2}, \\frac{\\theta^2}{2n}$\nD. $\\frac{\\overline{X}}{2}+\\frac{\\overline{Y}}{4}, \\frac{\\theta^2}{4n}$"
        },
        {
            "num": 22, "page": 416, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设总体 $X$ 服从参数为 $\lambda(\lambda > 0)$ 的泊松分布，取容量为 1 的简单随机样本 $X_1$，其样本值 $x_1 = 3$，则 $e^{-2\lambda}$ 的无偏估计量与无偏估计值分别为（ ）.",
            "options": "A. $e^{-2X_1}, e^{-6}$\nB. $e^{-X_1}, e^{-3}$\nC. 1, 1\nD. $(-1)^{X_1}, -1$"
        },
        {
            "num": 23, "page": 417, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设总体 $X$ 的未知参数 $\theta$ 有两个相互独立的无偏估计量 $\hat{\theta}_1$ 与 $\hat{\theta}_2$，且 $D(\hat{\theta}_2) = 2D(\hat{\theta}_1)$，记 $\hat{\theta} = a\hat{\theta}_1+b\hat{\theta}_2$，则以下使得 $\hat{\theta}$ 最有效的是（ ）.",
            "options": "A. $a = \\frac{1}{3}, b = \\frac{1}{3}$\nB. $a = \\frac{2}{3}, b = \\frac{1}{3}$\nC. $a = \\frac{1}{3}, b = \\frac{2}{3}$\nD. $a = \\frac{2}{3}, b = \\frac{2}{3}$"
        },
        {
            "num": 24, "page": 418, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设总体 $X$ 的数学期望存在且方差为 1，根据来自 $X$ 的容量为 16 的简单随机样本测得样本均值为 $a$，$\Phi(1.96) = 0.975$，则 $X$ 的数学期望的置信度等于 0.95 的置信区间为（ ）.",
            "options": "A. $(a-0.49, a+0.49)$\nB. $(a-0.327, a+0.327)$\nC. $(a-0.196, a+0.196)$\nD. $(a-0.025, a+0.025)$"
        },
        {
            "num": 25, "page": 419, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设总体 $X \sim N(\mu, 2^2)$，其中 $\mu$ 为未知参数，$X_1, X_2, \cdots, X_9$ 是来自总体 $X$ 的简单随机样本，记关于 $\mu$ 的置信度为 0.95 的置信区间长度为 $L$，则 $L$ 的数学期望 $E(L) = $（ ）.",
            "options": "A. $\\frac{2}{3} z_{0.025}$\nB. $\\frac{4}{3} z_{0.025}$\nC. $\\frac{2}{3} z_{0.05}$\nD. $\\frac{4}{3} z_{0.05}$"
        },
        {
            "num": 26, "page": 420, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设总体 $X \sim N(\mu, 1), H_0: \mu = 0, H_1: \mu = 1$。来自总体 $X$ 的样本容量为 9 的简单随机样本均值为 $\overline{X}$，设拒绝域为 $W = \{\overline{X} \ge 0.55\}$，则不犯第二类错误的概率为（ ）.",
            "options": "A. $1-\\Phi(1.35)$\nB. $\\Phi(1.35)$\nC. $\\Phi(1.65)$\nD. $1-\\Phi(1.65)$"
        },
        {
            "num": 27, "page": 421, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设 $X_1, X_2, \cdots, X_n$ 是来自均匀分布总体 $U(0,\theta) (\theta > 0)$ 的简单随机样本，原假设 $H_0: \theta \ge 2$，备择假设 $H_1: \theta < 2$，拒绝域为 $W = \{X_{(n)} \le a\}$，其中 $a > 0, X_{(n)} = \max\{X_1, X_2, \cdots, X_n\}$。若犯第一类错误的概率的最大值为 $\frac{1}{3^n}$，则 $a = $（ ）.",
            "options": "A. $\\frac{4}{3}$\nB. $\\frac{2}{3}$\nC. $\\frac{3}{4}$\nD. $\\frac{3}{2}$"
        },
        {
            "num": 29, "page": 423, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"设随机变量 $X \sim N(\mu_1, \sigma_1^2)$ 和 $Y \sim N(\mu_2, \sigma_2^2)$，现检验总体 $X$ 的均值是否大于 $Y$ 的均值，则应检验假设（ ）.",
            "options": "A. $H_0: \\mu_1 \\le \\mu_2; H_1: \\mu_1 > \\mu_2$\nB. $H_0: \\mu_1 \\ge \\mu_2; H_1: \\mu_1 < \\mu_2$\nC. $H_0: \\mu_1 < \\mu_2; H_1: \\mu_1 \\ge \\mu_2$\nD. $H_0: \\mu_1 > \\mu_2; H_1: \\mu_1 \\le \\mu_2$"
        },
        {
            "num": 30, "page": 424, "course": "概率论与数理统计", "chapter": "第9章 参数估计与假设检验",
            "stem": r"关于总体 $X$ 的假设 $H$ 属于简单假设的是（ ）.",
            "options": "A. 已知 $X$ 服从正态分布, $H: E(X) = 0$\nB. 已知 $X$ 服从指数分布, $H: E(X) \\ge 1$\nC. 已知 $X$ 服从二项分布, $H: D(X) = 5$\nD. 已知 $X$ 服从泊松分布, $H: D(X) = 3$"
        }
    ]
)

print("Finished 强化篇 · 概率论与数理统计")
