# -*- coding: utf-8 -*-
"""
Generator for Zhang Yu 1000: 强化篇 · 线性代数 (9章 选择题)
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

# 第1章 行列式
save_chapter(
    "02_强化篇/线性代数/第01章_行列式.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第1章 行列式",
    "本章节收录第 208 页至第 210 页共 2 道选择题。",
    [
        {
            "num": 4, "page": 208, "course": "线性代数", "chapter": "第1章 行列式",
            "stem": r"设 $A = [\alpha_1, \alpha_2, \alpha_3]$，$\alpha_1, \alpha_2, \alpha_3$ 为线性无关的 3 维列向量，$P$ 为 3 阶矩阵，且 $PA = [-\alpha_1, -2\alpha_2, -3\alpha_3]$，则 $|P-E| = $（ ）.",
            "options": "A. 6\nB. -6\nC. 24\nD. -24"
        },
        {
            "num": 6, "page": 210, "course": "线性代数", "chapter": "第1章 行列式",
            "stem": r"设 $A$ 为 3 阶矩阵，若 $|E-A| = |E+A| = |2E-A| = 0$，则 $|3E-A| = $（ ）.",
            "options": "A. -2\nB. -8\nC. 8\nD. 11"
        }
    ]
)

# 第2章 余子式和代数余子式的计算
save_chapter(
    "02_强化篇/线性代数/第02章_余子式和代数余子式的计算.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第2章 余子式和代数余子式的计算",
    "本章节收录第 212 页共 1 道选择题。",
    [
        {
            "num": 1, "page": 212, "course": "线性代数", "chapter": "第2章 余子式和代数余子式的计算",
            "stem": r"设 $D = \begin{vmatrix} 1 & -3 & 1 & -2 \\ 2 & -5 & -2 & -2 \\ 0 & -4 & 5 & 1 \\ -3 & 9 & -6 & 7 \end{vmatrix}$，$M_{3j}$ 表示 $D$ 中第 3 行第 $j$ 列元素的余子式 $(j=1,2,3,4)$，则 $M_{31}+3M_{32}-2M_{33}+2M_{34} = $（ ）.",
            "options": "A. 0\nB. 1\nC. -2\nD. -3"
        }
    ]
)

# 第3章 矩阵运算
save_chapter(
    "02_强化篇/线性代数/第03章_矩阵运算.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第3章 矩阵运算",
    "本章节收录第 216 页至第 222 页共 3 道选择题。",
    [
        {
            "num": 1, "page": 216, "course": "线性代数", "chapter": "第3章 矩阵运算",
            "stem": r"设 $A$ 是 $n$ 阶矩阵，则下列说法错误的是（ ）.",
            "options": "A. 对任意的 $n$ 维列向量 $\\xi$，有 $A\\xi = 0$，则 $A = 0$\nB. 对任意的 $n$ 维列向量 $\\xi$，有 $\\xi^T A \\xi = 0$，则 $A = 0$\nC. 对任意的 $n$ 阶矩阵 $B$，有 $A^T B = O$，则 $A = O$\nD. 对任意的 $n$ 阶矩阵 $B$，有 $B^T AB = O$，则 $A = O$"
        },
        {
            "num": 6, "page": 221, "course": "线性代数", "chapter": "第3章 矩阵运算",
            "stem": r"设 $A$ 是 $n$ 阶矩阵，$E+A$ 是可逆矩阵，则下列等式不成立的是（ ）.",
            "options": "A. $(A+E)(A-E) = (A-E)(A+E)$\nB. $(A+E)^{-1}(A-E) = (A-E)(A+E)^{-1}$\nC. $(A+E)^*(A-E) = (A-E)(A+E)^*$\nD. $(A+E)^T(A-E) = (A-E)(A+E)^T$"
        },
        {
            "num": 7, "page": 222, "course": "线性代数", "chapter": "第3章 矩阵运算",
            "stem": r"设 $A$ 为 2 阶方阵，$\alpha$ 为 2 维非零列向量，且 $\alpha$ 不是 $A$ 的特征向量，$P = [\alpha, A\alpha]$，$A^2\alpha+A\alpha-2\alpha = 0$。若矩阵 $B$ 满足 $AP = PB$，则 $B = $（ ）.",
            "options": "A. $\\begin{bmatrix} -1 & 0 \\ 1 & 2 \\end{bmatrix}$\nB. $\\begin{bmatrix} 0 & 1 \\ 2 & -1 \\end{bmatrix}$\nC. $\\begin{bmatrix} -1 & 1 \\ 0 & 2 \\end{bmatrix}$\nD. $\\begin{bmatrix} 0 & 2 \\ 1 & -1 \\end{bmatrix}$"
        }
    ]
)

# 第4章 矩阵的秩
save_chapter(
    "02_强化篇/线性代数/第04章_矩阵的秩.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第4章 矩阵的秩",
    "本章节收录第 226 页至第 233 页共 8 道选择题。",
    [
        {
            "num": 1, "page": 226, "course": "线性代数", "chapter": "第4章 矩阵的秩",
            "stem": r"设 $A$ 是 3 阶非零矩阵，满足 $A^2 = A$，且 $A \neq E$，则必有（ ）.",
            "options": "A. $r(A) = 1$\nB. $r(A-E) = 2$\nC. $[r(A)-1][r(A-E)-2] = 0$\nD. $[r(A)-1][r(A-E)-1] = 0$"
        },
        {
            "num": 2, "page": 227, "course": "线性代数", "chapter": "第4章 矩阵的秩",
            "stem": r"若 $A, A^*, B$ 都是 $n(n > 2)$ 阶非零矩阵，且 $A^*$ 是 $A$ 的伴随矩阵，$AB = O$，则 $r(B) = $（ ）.",
            "options": "A. 1\nB. $n-1$\nC. $n$\nD. $n-1$ 或 $n$"
        },
        {
            "num": 3, "page": 228, "course": "线性代数", "chapter": "第4章 矩阵的秩",
            "stem": r"设矩阵 $A = \begin{bmatrix} 1 & -1 & 1 \\ -2 & 2 & 1 \\ 1 & -1 & k \end{bmatrix}$，$r((3E-A)^2) < r(3E-A)$，其中 $E$ 是 3 阶单位矩阵，则常数 $k = $（ ）.",
            "options": "A. 3\nB. 4\nC. 5\nD. 6"
        },
        {
            "num": 4, "page": 229, "course": "线性代数", "chapter": "第4章 矩阵的秩",
            "stem": r"设 $A,B$ 为 $n$ 阶实矩阵，则下列结论不成立的是（ ）.",
            "options": "A. $r([A \quad AB]) = r(A)$\nB. $r([AB^T \quad AB^T B]) = r(AB^T)$\nC. $r\\left(\\begin{bmatrix} BA \\ B^T BA \\end{bmatrix}\\right) = r(AB^T)$\nD. $r\\left(\\begin{bmatrix} A^T A \\ B^T A \\end{bmatrix}\\right) = r(A)$"
        },
        {
            "num": 5, "page": 230, "course": "线性代数", "chapter": "第4章 矩阵的秩",
            "stem": r"已知 $A$ 为 $n$ 阶矩阵，$E$ 为 $n$ 阶单位矩阵，记矩阵 $\begin{bmatrix} O & A \\ A^T & E \\end{bmatrix}, \begin{bmatrix} O & A^T A \\ A^T & E \\end{bmatrix}, \begin{bmatrix} A^T & E \\ A^T A A^T & A^T A \\end{bmatrix}$ 的秩分别为 $r_1, r_2, r_3$，则（ ）.",
            "options": "A. $r_1 = r_2 \\ge r_3$\nB. $r_1 = r_2 \\le r_3$\nC. $r_1 = r_3 \\ge r_2$\nD. $r_1 = r_3 \\le r_2$"
        },
        {
            "num": 6, "page": 231, "course": "线性代数", "chapter": "第4章 矩阵的秩",
            "stem": r"已知 $n$ 阶矩阵 $A,B,C$ 满足 $ABC = O$，$E$ 为 $n$ 阶单位矩阵，记矩阵 $\begin{bmatrix} O & A \\ BC & E \\end{bmatrix}, \begin{bmatrix} AB & C \\ O & E \\end{bmatrix}, \begin{bmatrix} E & AB \\ AB & O \\end{bmatrix}$ 的秩分别为 $r_1, r_2, r_3$，则（ ）.",
            "options": "A. $r_1 \\le r_2 \\le r_3$\nB. $r_1 \\le r_3 \\le r_2$\nC. $r_3 \\le r_1 \\le r_2$\nD. $r_2 \\le r_1 \\le r_3$"
        },
        {
            "num": 7, "page": 232, "course": "线性代数", "chapter": "第4章 矩阵的秩",
            "stem": r"设 $A,B,C$ 均为 $n$ 阶矩阵，$r(AB) \le r(BA)$，记 $\begin{bmatrix} O & AB \\ B & BC \\end{bmatrix}, \begin{bmatrix} B & BC \\ AB & O \\end{bmatrix}, \begin{bmatrix} BA & BAC \\ O & B \\end{bmatrix}$ 的秩分别为 $r_1, r_2, r_3$，则（ ）.",
            "options": "A. $r_2 \\le r_3 \\le r_1$\nB. $r_2 \\le r_1 \\le r_3$\nC. $r_1 \\le r_2 \\le r_3$\nD. $r_3 \\le r_2 \\le r_1$"
        },
        {
            "num": 8, "page": 233, "course": "线性代数", "chapter": "第4章 矩阵的秩",
            "stem": r"设 $A$ 为 $n$ 阶矩阵，$r(A) = r$，$E_r$ 为 $r$ 阶单位矩阵，则 “$A^2 = A$” 是 “存在列满秩矩阵 $C_{n \times r}$，使得 $A = CB, BC = E_r$” 的（ ）.",
            "options": "A. 充分非必要条件\nB. 必要非充分条件\nC. 充分必要条件\nD. 既非充分又非必要条件"
        }
    ]
)

# 第5章 线性方程组
save_chapter(
    "02_强化篇/线性代数/第05章_线性方程组.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第5章 线性方程组",
    "本章节收录第 234 页至第 248 页共 8 道选择题。",
    [
        {
            "num": 1, "page": 234, "course": "线性代数", "chapter": "第5章 线性方程组",
            "stem": r"设 4 阶矩阵 $A = [a_{ij}]$ 不可逆，且元素 $a_{12}$ 的代数余子式 $A_{12} \neq 0$。若矩阵 $A$ 的列向量组为 $\alpha_1, \alpha_2, \alpha_3, \alpha_4$，$k_1, k_2, k_3$ 为任意常数，则方程组 $A^* x = 0$ 的通解为（ ）.",
            "options": "A. $k_1\alpha_1+k_2\alpha_2+k_3\alpha_3$\nB. $k_1\alpha_1+k_2\alpha_2+k_3\alpha_4$\nC. $k_1\alpha_1+k_2\alpha_3+k_3\alpha_4$\nD. $k_1\alpha_2+k_2\alpha_3+k_3\alpha_4$"
        },
        {
            "num": 3, "page": 236, "course": "线性代数", "chapter": "第5章 线性方程组",
            "stem": r"设方程组 $\begin{cases} x_1+ax_2-2x_3=0, \\ x_1+2x_2+x_3=1, \\ 2x_1+3x_2+(a+2)x_3=3 \end{cases}$ 的系数矩阵为 $A$，自由项为 $b$。若 $Ax = b$ 无解，$A^T Ax = A^T b$ 有解，则 $a = $（ ）.",
            "options": "A. -1\nB. 1\nC. -3\nD. 3"
        },
        {
            "num": 4, "page": 237, "course": "线性代数", "chapter": "第5章 线性方程组",
            "stem": r"设 $A$ 是秩为 2 的 3 阶实对称矩阵，$\alpha, \beta$ 是 3 维非零列向量，$B = \begin{bmatrix} A & \beta \\ \alpha^T & 1 \end{bmatrix}$，则 $r(B) = 2$ 是方程组 $\begin{cases} Ax = \beta, \\ \alpha^T x = 1 \end{cases}$ 有解的（ ）.",
            "options": "A. 充分非必要条件\nB. 必要非充分条件\nC. 充分必要条件\nD. 既非充分又非必要条件"
        },
        {
            "num": 7, "page": 240, "course": "线性代数", "chapter": "第5章 线性方程组",
            "stem": r"设 3 阶矩阵 $A,B$ 满足 $r(BA) < r(AB)$，对于以下结论：\n① $ABx = 0$ 与 $BAx = 0$ 有非零公共解；\n② $ABAx = 0$ 与 $BABx = 0$ 有非零公共解。\n正确的说法是（ ）.",
            "options": "A. ①正确，②正确\nB. ①正确，②错误\nC. ①错误，②正确\nD. ①错误，②错误"
        },
        {
            "num": 8, "page": 241, "course": "线性代数", "chapter": "第5章 线性方程组",
            "stem": r"设 $A$ 为 $n$ 阶实矩阵，则（ ）.",
            "options": "A. $\\begin{bmatrix} A & O \\ E & A^T A \\end{bmatrix} x = 0$ 只有零解\nB. $\\begin{bmatrix} O & A \\ A^T A & A A^T A \\end{bmatrix} x = 0$ 只有零解\nC. $\\begin{bmatrix} A & A^T A \\ O & A^T A \\end{bmatrix} x = 0$ 与 $\\begin{bmatrix} A^T A & A \\ O & A \\end{bmatrix} x = 0$ 同解\nD. $\\begin{bmatrix} A A^T A & A^T A \\ O & A \\end{bmatrix} x = 0$ 与 $\\begin{bmatrix} A^T A^2 & A \\ O & A^T A \\end{bmatrix} x = 0$ 同解"
        },
        {
            "num": 9, "page": 242, "course": "线性代数", "chapter": "第5章 线性方程组",
            "stem": r"设 $A,B$ 为 $n$ 阶矩阵，且 $A$ 满足 $A^2-A=3E$，则与 $\begin{bmatrix} A \\ B \end{bmatrix} x = 0$ 不一定同解的是（ ）.",
            "options": "A. $\\begin{bmatrix} A-B \\ A+AB \\end{bmatrix} x = 0$\nB. $\\begin{bmatrix} A+B \\ A+AB-B \\end{bmatrix} x = 0$\nC. $\\begin{bmatrix} A-B \\ 2A+B \\end{bmatrix} x = 0$\nD. $\\begin{bmatrix} A+B \\ BA+B^2 \\end{bmatrix} x = 0$"
        },
        {
            "num": 14, "page": 247, "course": "线性代数", "chapter": "第5章 线性方程组",
            "stem": r"如图所示有三张平面，其中有两张平面平行，第三张平面与它们相交，其方程 $a_{i1}x+a_{i2}y+a_{i3}z = d_i (i=1,2,3)$ 组成的方程组的系数矩阵与增广矩阵分别为 $A$ 和 $\overline{A}$，则（ ）.",
            "options": "A. $r(A) = 2, r(\\overline{A}) = 3$\nB. $r(A) = 2, r(\\overline{A}) = 2$\nC. $r(A) = 1, r(\\overline{A}) = 2$\nD. $r(A) = 1, r(\\overline{A}) = 1$"
        },
        {
            "num": 15, "page": 248, "course": "线性代数", "chapter": "第5章 线性方程组",
            "stem": r"设 $\alpha_i = [a_i, b_i, c_i]^T (i=1,2,3)$ 均为非零列向量，且直线 $\frac{x-a_1}{a_2} = \frac{y-b_1}{b_2} = \frac{z-c_1}{c_2}$ 过点 $(a_3, b_3, c_3)$，则可能是三个平面 $\pi_i: \alpha_i^T \begin{bmatrix} x \\ y \\ z \end{bmatrix} = 1 (i=1,2,3)$ 的位置关系的所有序号是（ ）.",
            "options": "A. ①③\nB. ②③\nC. ②④\nD. ①③④"
        }
    ]
)

# 第6章 向量组
save_chapter(
    "02_强化篇/线性代数/第06章_向量组.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第6章 向量组",
    "本章节收录第 249 页至第 258 页共 5 道选择题。",
    [
        {
            "num": 1, "page": 249, "course": "线性代数", "chapter": "第6章 向量组",
            "stem": r"设 $\alpha_1, \alpha_2, \cdots, \alpha_s$ 是 $n$ 维列向量，$A$ 是 $m \times n$ 矩阵，记向量组 $(\text{I})$ 为 $\alpha_1, \alpha_2, \cdots, \alpha_s$，向量组 $(\text{II})$ 为 $A\alpha_1, A\alpha_2, \cdots, A\alpha_s$，则下列命题正确的是（ ）.",
            "options": "A. 若向量组 $(\\text{I})$ 线性无关，则向量组 $(\\text{II})$ 线性无关\nB. 若向量组 $(\\text{II})$ 线性无关，则向量组 $(\\text{I})$ 线性无关\nC. 若向量组 $(\\text{II})$ 线性相关，则向量组 $(\\text{I})$ 线性相关\nD. 向量组 $(\\text{I})$ 与向量组 $(\\text{II})$ 具有不同的线性相关性"
        },
        {
            "num": 2, "page": 250, "course": "线性代数", "chapter": "第6章 向量组",
            "stem": r"设 $A = \begin{bmatrix} a & 1 & 1 \\ 1 & a & a \\ 1 & 1 & a \end{bmatrix}$ 可经初等列变换化成 $B = \begin{bmatrix} a & 1 & 1 \\ 1 & a & 1 \\ 1 & 1 & a \end{bmatrix}$，则 $a$ 的取值范围为（ ）.",
            "options": "A. $\{a \mid a \in \mathbb{R}, a \neq -2\}$\nB. $\{a \mid a \in \mathbb{R}, a \neq -2, a \neq -1\}$\nC. $\{a \mid a \in \mathbb{R}, a \neq 1, a \neq -1\}$\nD. $\{a \mid a \in \mathbb{R}, a \neq -1\}$"
        },
        {
            "num": 4, "page": 252, "course": "线性代数", "chapter": "第6章 向量组",
            "stem": r"已知 $\begin{bmatrix} 1 & 1 & 1 \\ 1 & 2 & 1 \\ 1 & 1 & 1 \end{bmatrix} = \begin{bmatrix} 1 & 1 \\ 1 & 2 \\ 1 & 1 \end{bmatrix} A$，则 $A = $（ ）.",
            "options": "A. $\\begin{bmatrix} 1 & 0 & 1 \\ 0 & 1 & 0 \\end{bmatrix}$\nB. $\\begin{bmatrix} 0 & 1 & 0 \\ 1 & 0 & 1 \\end{bmatrix}$\nC. $\\begin{bmatrix} 1 & 1 & 0 \\ 0 & 0 & 1 \\end{bmatrix}$\nD. $\\begin{bmatrix} 1 & 0 & 1 \\ 0 & 0 & 1 \\end{bmatrix}$"
        },
        {
            "num": 8, "page": 256, "course": "线性代数", "chapter": "第6章 向量组",
            "stem": r"设向量空间 $V$ 满足 $x_1+x_2+x_3=0, -\infty < x_i < +\infty, i=1,2,3$，则 $V$ 的一个基为（ ）.",
            "options": "A. $\\begin{bmatrix} -1 \\ 0 \\ 1 \\end{bmatrix}, \\begin{bmatrix} -1 \\ 1 \\ 0 \\end{bmatrix}, \\begin{bmatrix} 1 \\ 1 \\ 1 \\end{bmatrix}$\nB. $\\begin{bmatrix} 1 \\ 0 \\ -1 \\end{bmatrix}, \\begin{bmatrix} -1 \\ -1 \\ 0 \\end{bmatrix}$\nC. $\\begin{bmatrix} 1 \\ 0 \\ -1 \\end{bmatrix}, \\begin{bmatrix} -1 \\ -1 \\ 0 \\end{bmatrix}, \\begin{bmatrix} 1 \\ 1 \\ 1 \\end{bmatrix}$\nD. $\\begin{bmatrix} -1 \\ 0 \\ 1 \\end{bmatrix}, \\begin{bmatrix} -1 \\ 1 \\ 0 \\end{bmatrix}$"
        },
        {
            "num": 10, "page": 258, "course": "线性代数", "chapter": "第6章 向量组",
            "stem": r"设 $\beta_1, \beta_2, \beta_3$ 是 3 维向量空间 $\mathbb{R}^3$ 的一个基，则基 $\beta_1, 2\beta_2, 3\beta_3$ 到基 $\beta_1-\beta_2, \beta_2+\beta_3, \beta_3-\beta_1$ 的过渡矩阵为（ ）.",
            "options": "A. $\\begin{bmatrix} 0 & -2 & 1 \\ 3 & 0 & -6 \\ -8 & 4 & 0 \\end{bmatrix}$\nB. $\\begin{bmatrix} 1 & 0 & -1 \\ -\\frac{1}{2} & \\frac{1}{2} & 0 \\ 0 & \\frac{1}{3} & \\frac{1}{3} \\end{bmatrix}$\nC. $\\begin{bmatrix} \\frac{1}{2} & -\\frac{1}{3} & \\frac{1}{4} \\ 0 & \\frac{1}{2} & -\\frac{1}{3} \\ -\\frac{1}{3} & 0 & \\frac{1}{4} \\end{bmatrix}$\nD. $\\begin{bmatrix} \\frac{1}{2} & 0 & -\\frac{1}{3} \\ -\\frac{1}{3} & \\frac{1}{2} & 0 \\ \\frac{1}{4} & -\\frac{1}{3} & \\frac{1}{4} \\end{bmatrix}$"
        }
    ]
)

# 第7章 特征值与特征向量
save_chapter(
    "02_强化篇/线性代数/第07章_特征值与特征向量.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第7章 特征值与特征向量",
    "本章节收录第 260 页至第 267 页共 5 道选择题。",
    [
        {
            "num": 1, "page": 260, "course": "线性代数", "chapter": "第7章 特征值与特征向量",
            "stem": r"设 $A = \begin{bmatrix} 1 & 0 & a \\ b & 2 & 0 \\ 0 & c & 3 \end{bmatrix}$，其中 $abc = -6$，则 $A$ 的伴随矩阵 $A^*$ 有非零特征值（ ）.",
            "options": "A. -8\nB. 8\nC. -11\nD. 11"
        },
        {
            "num": 2, "page": 261, "course": "线性代数", "chapter": "第7章 特征值与特征向量",
            "stem": r"设矩阵 $A = \begin{bmatrix} 1 & -2 & 2 \\ a & 4 & b \\ -3 & -6 & 8 \end{bmatrix}$ 有三个线性无关的特征向量，$\lambda = 2$ 是 $A$ 的二重特征值，则（ ）.",
            "options": "A. $a = 1, b = -2$\nB. $a = -1, b = 2$\nC. $a = 2, b = -1$\nD. $a = -2, b = 1$"
        },
        {
            "num": 3, "page": 262, "course": "线性代数", "chapter": "第7章 特征值与特征向量",
            "stem": r"设 $A$ 是 3 阶矩阵，有特征值 $\lambda_1 = 0, \lambda_2 = 1, \lambda_3 = -1$，对应的特征向量分别是 $\xi_1, \xi_2, \xi_3$，以下 $k, k_1, k_2$ 为任意常数，则非齐次线性方程组 $Ax = \xi_2+\xi_3$ 的通解是（ ）.",
            "options": r"A. $k_1\xi_1+k_2\xi_2+\xi_3$" + "\n" + r"B. $k_1\xi_1+k_2\xi_3+\xi_2$" + "\n" + r"C. $k\xi_1-\xi_2+\xi_3$" + "\n" + r"D. $k\xi_1+\xi_2-\xi_3$"
        },
        {
            "num": 4, "page": 263, "course": "线性代数", "chapter": "第7章 特征值与特征向量",
            "stem": r"设 $A$ 是 3 阶矩阵，$Ax = 0$ 有通解 $k_1\xi_1+k_2\xi_2$ ($k_1, k_2$ 为任意常数)，$A\xi_3 = \xi_3$，则存在可逆矩阵 $P$，使得 $P^{-1}AP = \begin{bmatrix} 0 & 0 & 0 \\ 0 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix}$，其中 $P$ 是（ ）.",
            "options": r"A. $[\xi_1, \xi_2, \xi_1+\xi_3]" + "\n" + r"B. $[\xi_2, \xi_3, \xi_1]" + "\n" + r"C. $[\xi_1+\xi_2, -\xi_2, 2\xi_3]" + "\n" + r"D. $[\xi_1+\xi_2, \xi_2-\xi_3, \xi_3]$"
        },
        {
            "num": 8, "page": 267, "course": "线性代数", "chapter": "第7章 特征值与特征向量",
            "stem": r"设 $A,B$ 均为 $n$ 阶矩阵，$|B| \neq 0$，$\alpha$ 为 $n$ 维非零列向量，则 “$\alpha$ 是 $AB$ 的特征向量” 是 “$B\alpha$ 是 $BA$ 的特征向量” 的（ ）.",
            "options": "A. 充分必要条件\nB. 充分非必要条件\nC. 必要非充分条件\nD. 既非充分又非必要条件"
        }
    ]
)

# 第8章 相似理论
save_chapter(
    "02_强化篇/线性代数/第08章_相似理论.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第8章 相似理论",
    "本章节收录第 269 页至第 283 页共 7 道选择题。",
    [
        {
            "num": 1, "page": 269, "course": "线性代数", "chapter": "第8章 相似理论",
            "stem": r"设 $A,B,D$ 均为 2 阶矩阵，$|A| \neq |B|, |A| < 0, |B| < 0, C = \begin{bmatrix} A & D \\ O & B \end{bmatrix}$，则 “$\text{tr}(A) = \text{tr}(B)$” 是 “$C$ 可以相似对角化” 的（ ）.",
            "options": "A. 充分非必要条件\nB. 必要非充分条件\nC. 充分必要条件\nD. 既非充分又非必要条件"
        },
        {
            "num": 2, "page": 270, "course": "线性代数", "chapter": "第8章 相似理论",
            "stem": r"以下两个矩阵，可用同一可逆矩阵 $P$ 相似对角化的是（ ）.",
            "options": "A. $\\begin{bmatrix} 1 & 1 \\ 1 & 0 \\end{bmatrix}, \\begin{bmatrix} 0 & 1 \\ 1 & 1 \\end{bmatrix}$\nB. $\\begin{bmatrix} 1 & 1 \\ 1 & -1 \\end{bmatrix}, \\begin{bmatrix} -1 & 1 \\ 1 & 1 \\end{bmatrix}$\nC. $\\begin{bmatrix} 0 & 1 \\ 1 & 1 \\end{bmatrix}, \\begin{bmatrix} -1 & 1 \\ 1 & 0 \\end{bmatrix}$\nD. $\\begin{bmatrix} 0 & 1 \\ 1 & -1 \\end{bmatrix}, \\begin{bmatrix} -1 & 1 \\ 1 & 0 \\end{bmatrix}$"
        },
        {
            "num": 3, "page": 271, "course": "线性代数", "chapter": "第8章 相似理论",
            "stem": r"(1) 下列矩阵中与矩阵 $M = \begin{bmatrix} 1 & 2 & 3 \\ 0 & 0 & 0 \\ 0 & 0 & 0 \end{bmatrix}$ 相似的是（ ）.\n(2) 下列矩阵中，与 $\begin{bmatrix} 1 & 0 & 0 \\ 0 & 2 & 1 \\ 0 & 0 & 2 \end{bmatrix}$ 不相似的是（ ）.",
            "options": "A. (1) $A = \\begin{bmatrix} 0 & 0 & 0 \\ 1 & 2 & 3 \\ 0 & 0 & 0 \\end{bmatrix}$; (2) $\\begin{bmatrix} 2 & 0 & -1 \\ 0 & 1 & 0 \\ 0 & 0 & 2 \\end{bmatrix}$\nB. (1) $B = \\begin{bmatrix} 0 & 0 & 0 \\ 0 & 0 & 0 \\ 1 & 2 & 3 \\end{bmatrix}$; (2) $\\begin{bmatrix} 2 & 0 & 0 \\ -1 & 2 & 1 \\ 0 & 0 & 1 \\end{bmatrix}$\nC. (1) $C = \\begin{bmatrix} 1 & 0 & 0 \\ 2 & 0 & 0 \\ 3 & 0 & 0 \\end{bmatrix}$; (2) $\\begin{bmatrix} 2 & 1 & 0 \\ 0 & 1 & 1 \\ 0 & 0 & 2 \\end{bmatrix}$\nD. (1) $D = \\begin{bmatrix} 1 & 2 & 0 \\ 0 & 0 & 3 \\ 0 & 0 & 0 \\end{bmatrix}$; (2) $\\begin{bmatrix} 2 & -1 & 0 \\ 1 & 2 & 0 \\ 0 & 0 & 1 \\end{bmatrix}$"
        },
        {
            "num": 11, "page": 279, "course": "线性代数", "chapter": "第8章 相似理论",
            "stem": r"设 $A, B$ 是可逆矩阵，且 $A$ 与 $B$ 相似，则下列结论错误的是（ ）.",
            "options": "A. $A^T$ 与 $B^T$ 相似\nB. $A^2+A^{-1}$ 与 $B^2+B^{-1}$ 相似\nC. $A+A^T$ 与 $B+B^T$ 相似\nD. $A^*-A^{-1}$ 与 $B^*-B^{-1}$ 相似"
        },
        {
            "num": 13, "page": 281, "course": "线性代数", "chapter": "第8章 相似理论",
            "stem": r"设 4 阶实对称矩阵 $A$ 满足 $A^4 = O$，则 $r(A) = $（ ）.",
            "options": "A. 0\nB. 0 或 1\nC. 1 或 2\nD. 2 或 3"
        },
        {
            "num": 14, "page": 282, "course": "线性代数", "chapter": "第8章 相似理论",
            "stem": r"设 $A$ 是 3 阶实矩阵，则 “$A$ 是实对称矩阵” 是 “$A$ 有 3 个相互正交的特征向量” 的（ ）.",
            "options": "A. 充分非必要条件\nB. 必要非充分条件\nC. 充分必要条件\nD. 既非充分又非必要条件"
        },
        {
            "num": 15, "page": 283, "course": "线性代数", "chapter": "第8章 相似理论",
            "stem": r"设 2 阶实对称矩阵 $A$ 的特征值为 $\lambda_1, \lambda_2$，且 $\lambda_1 \neq \lambda_2$，$\alpha_1, \alpha_2$ 分别是 $A$ 的对应于 $\lambda_1, \lambda_2$ 的单位特征向量，则与矩阵 $A+\alpha_1\alpha_1^T$ 相似的对角矩阵为（ ）.",
            "options": "A. $\\begin{bmatrix} \\lambda_1 & 0 \\ 0 & \\lambda_2 \\end{bmatrix}$\nB. $\\begin{bmatrix} \\lambda_1+1 & 0 \\ 0 & \\lambda_2+1 \\end{bmatrix}$\nC. $\\begin{bmatrix} \\lambda_1 & 0 \\ 0 & \\lambda_2+1 \\end{bmatrix}$\nD. $\\begin{bmatrix} \\lambda_1+1 & 0 \\ 0 & \\lambda_2 \\end{bmatrix}$"
        }
    ]
)

# 第9章 二次型
save_chapter(
    "02_强化篇/线性代数/第09章_二次型.md",
    "《张宇1000题》· 强化篇 · 线性代数 · 第9章 二次型",
    "本章节收录第 290 页至第 315 页共 10 道选择题。",
    [
        {
            "num": 1, "page": 290, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"已知二次型 $f(x_1,x_2,x_3) = 4x_1^2+x_2^2+ax_3^2+2x_1x_2-4x_1x_3+2x_2x_3$ 可经可逆线性变换但不可经正交变换化为 $g(y_1,y_2,y_3) = by_1^2+6y_2^2$，则 $a+b$ 的取值范围为（ ）.",
            "options": "A. $(4, +\\infty)$\nB. $(7, +\\infty)$\nC. $[4, +\\infty)$\nD. $(4,7) \\cup (7, +\\infty)$"
        },
        {
            "num": 2, "page": 291, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"设 $A$ 为 3 阶实对称方阵，$r(E-A) = 1$，且 $A^2+2A=3E$，则二次型 $f(x_1,x_2,x_3) = x^T Ax$ 的规范形为（ ）.",
            "options": "A. $z_1^2+z_2^2+z_3^2$\nB. $z_1^2+z_2^2-z_3^2$\nC. $z_1^2-z_2^2-z_3^2$\nD. $-z_1^2-z_2^2-z_3^2$"
        },
        {
            "num": 3, "page": 292, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"$f(x_1,x_2,x_3) = x_1x_2+x_1x_3-3x_2x_3$ 的规范形为（ ）.",
            "options": "A. $z_1^2+z_2^2-z_3^2$\nB. $z_1^2-z_2^2-z_3^2$\nC. $z_1^2+z_2^2+z_3^2$\nD. $-z_1^2-z_2^2-z_3^2$"
        },
        {
            "num": 4, "page": 293, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"二次型 $f(x_1,x_2,x_3) = (x_1+3x_2+ax_3)(x_1+5x_2+bx_3)$ 的正惯性指数 $p$（ ）.",
            "options": "A. 与 $a$ 有关，与 $b$ 无关\nB. 与 $a$ 无关，与 $b$ 有关\nC. 与 $a,b$ 均有关\nD. 与 $a,b$ 均无关"
        },
        {
            "num": 19, "page": 308, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"已知 $f(x_1,x_2,x_3) = x^T Ax$ 经正交变换 $x = Qy$ 化为 $g(y_1,y_2,y_3) = y_1^2+2y_2^2+ay_3^2 (a \neq 0)$，且 $Q^{-1}A^* Q = \begin{bmatrix} 1 & 0 & 0 \\ 0 & \\frac{1}{2} & 0 \\ 0 & 0 & \\frac{1}{a} \\end{bmatrix}$，其中 $A^*$ 是 $A$ 的伴随矩阵，则对任意 $x \neq 0$，有（ ）.",
            "options": "A. $f(x_1,x_2,x_3) > 0$\nB. $f(x_1,x_2,x_3) \\ge 0$\nC. $f(x_1,x_2,x_3) < 0$\nD. $f(x_1,x_2,x_3) \\le 0$"
        },
        {
            "num": 20, "page": 309, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"二次型 $f(x_1,x_2,x_3) = \sum_{i=1}^3 x_i^2 + \sum_{1 \le i < j \le 3} 2ax_i x_j$ 正定的充要条件为（ ）.",
            "options": "A. $a > 0$\nB. $0 < a < 1$\nC. $-1 < a < 1$\nD. $-\\frac{1}{2} < a < 1$"
        },
        {
            "num": 21, "page": 310, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"设 $A$ 为 $m$ 阶正定矩阵，$B$ 为 $m \times n$ 实矩阵，$C = B^T AB$，则 $C$ 与 $n$ 阶单位矩阵 $E$ 合同的充分必要条件为（ ）.",
            "options": "A. 齐次线性方程组 $Bx = 0$ 只有零解\nB. 齐次线性方程组 $BB^T x = 0$ 有非零解\nC. 齐次线性方程组 $BB^T x = 0$ 只有零解\nD. 齐次线性方程组 $B^T Bx = 0$ 有非零解"
        },
        {
            "num": 22, "page": 311, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"设二次型 $f(x_1,x_2,x_3) = (x_1+2x_2+x_3)^2+[-x_1+(a-4)x_2+2x_3]^2+(2x_1+x_2+ax_3)^2$ 正定，则参数 $a$ 的取值范围是（ ）.",
            "options": "A. $a = 2$\nB. $a = -7$\nC. $a > 0$\nD. $a$ 为任意实数"
        },
        {
            "num": 25, "page": 314, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"设 $A$ 为 $n$ 阶矩阵，则以下不是 “$A^T A$ 正定” 的充要条件的是（ ）.",
            "options": "A. $A$ 为初等矩阵的乘积\nB. $A$ 为 $\\mathbb{R}^n$ 的某两个基之间的过渡矩阵\nC. $A$ 的行向量组线性无关\nD. $A$ 与 $n$ 阶单位矩阵 $E$ 相似"
        },
        {
            "num": 26, "page": 315, "course": "线性代数", "chapter": "第9章 二次型",
            "stem": r"设二次型 $f(x_1,x_2,x_3) = a(x_1^2+x_2^2+x_3^2)+4x_1x_2+4x_1x_3+4x_2x_3$。若方程 $f(x_1,x_2,x_3) = -1$ 表示的曲面为圆柱面，则（ ）.",
            "options": "A. $a = -4$，且 $f(x_1,x_2,x_3)$ 的规范形为 $-y_1^2-y_2^2-y_3^2$\nB. $a = -4$，且 $f(x_1,x_2,x_3)$ 在正交变换下的标准形为 $-6y_1^2-6y_2^2$\nC. $a = 2$，且 $f(x_1,x_2,x_3)$ 的规范形为 $-y_1^2-y_2^2-y_3^2$\nD. $a = 2$，且 $f(x_1,x_2,x_3)$ 在正交变换下的标准形为 $-6y_1^2-6y_2^2$"
        }
    ]
)

print("Finished 强化篇 · 线性代数")
