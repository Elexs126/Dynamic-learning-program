# -*- coding: utf-8 -*-
"""
Script to generate all Multiple Choice Questions from the 512-page PDF
with proper LaTeX formulas, dual tags (Course, Chapter), and image references.
"""

import os

base_dir = r"c:\Users\HP\Documents\antigravity\delightful-salk\张宇1000题"

# Define all data structures
# -------------------------------------------------------------
# 1. 基础篇 · 线性代数
# -------------------------------------------------------------
jc_xd = {
    "第01章_行列式.md": {
        "title": "《张宇1000题》· 基础篇 · 线性代数 · 第1章 行列式",
        "course": "线性代数",
        "chapter": "第1章 行列式",
        "questions": [
            {
                "num": 1,
                "page": 1,
                "stem": r"设 $a,b,c$ 是方程 $x^3-2x+4=0$ 的三个不同的根，则行列式 $\begin{vmatrix} a & b & c \\ b & c & a \\ c & a & b \end{vmatrix}$ 的值等于（ ）. ",
                "options": "A. 1\nB. 0\nC. -1\nD. -2"
            },
            {
                "num": 2,
                "page": 2,
                "stem": r"行列式 $\begin{vmatrix} x & 1 & 0 & 1 \\ 0 & 1 & x & 1 \\ 1 & x & 1 & 0 \\ 1 & 0 & 1 & x \end{vmatrix}$ 展开式中的常数项为（ ）. ",
                "options": "A. 4\nB. 2\nC. 1\nD. 0"
            },
            {
                "num": 3,
                "page": 3,
                "stem": r"设 $D = \begin{vmatrix} 5x & 1 & 2 & 3 \\ x & x & 1 & 2 \\ 1 & 2 & x & 3 \\ x & 1 & 2 & 2x \end{vmatrix}$，则 $D$ 的展开式中 $x^3$ 的系数与 $x^4$ 的系数分别为（ ）. ",
                "options": "A. -5, 10\nB. -5, -10\nC. 5, -10\nD. 5, 10"
            },
            {
                "num": 4,
                "page": 4,
                "stem": r"不恒为零的函数 $f(x) = \begin{vmatrix} a_1+x & b_1+x & c_1+x \\ a_2+x & b_2+x & c_2+x \\ a_3+x & b_3+x & c_3+x \end{vmatrix}$（ ）. ",
                "options": "A. 没有零点\nB. 至多有 1 个零点\nC. 恰有 2 个零点\nD. 恰有 3 个零点"
            },
            {
                "num": 5,
                "page": 5,
                "stem": r"若 $f(x) = \begin{vmatrix} 3x+1 & x+11 & x-2 \\ x+1 & x+4 & -1 \\ x & 7 & x-1 \end{vmatrix}$，则曲线 $f(x)$ 的拐点为（ ）. ",
                "options": "A. $(1,7)$\nB. $(-1,-1)$\nC. $(0,0)$\nD. $(-2,-2)$"
            },
            {
                "num": 6,
                "page": 6,
                "stem": r"设 $n$ 阶行列式 $D_n = \begin{vmatrix} 2 & 1 & 0 & \cdots & 0 \\ 1 & 2 & 1 & \cdots & 0 \\ 0 & 1 & 2 & \cdots & 0 \\ \vdots & \vdots & \vdots & & \vdots \\ 0 & 0 & 0 & \cdots & 2 \end{vmatrix}$，则（ ）. ",
                "options": "A. $D_1, D_2, \cdots, D_n$ 为等比数列\nB. $D_1, D_2, \cdots, D_n$ 为等差数列\nC. $D_n$ 为范德蒙德行列式\nD. $D_n = n$"
            }
        ]
    },
    "第02章_矩阵.md": {
        "title": "《张宇1000题》· 基础篇 · 线性代数 · 第2章 矩阵",
        "course": "线性代数",
        "chapter": "第2章 矩阵",
        "questions": [
            {
                "num": 1,
                "page": 12,
                "stem": r"以下矩阵乘积的结果为 $\begin{bmatrix} 1 & -1 & 2 \\ 2 & 1 & 3 \\ 3 & 1 & 4 \end{bmatrix}$ 的是（ ）. ",
                "options": "A. $\\begin{bmatrix} 1 & 0 & 0 \\ 2 & 1 & 0 \\ 3 & \\frac{4}{3} & 2 \\end{bmatrix} \\begin{bmatrix} 1 & -1 & 2 \\ 0 & 3 & -1 \\ 0 & 0 & -\\frac{2}{3} \\end{bmatrix}$\nB. $\\begin{bmatrix} 1 & 0 & 0 \\ 2 & -1 & 0 \\ 3 & \\frac{4}{3} & 1 \\end{bmatrix} \\begin{bmatrix} 1 & -1 & 2 \\ 0 & -3 & -1 \\ 0 & 0 & -\\frac{2}{3} \\end{bmatrix}$\nC. $\\begin{bmatrix} 1 & 0 & 0 \\ 2 & 1 & 0 \\ 3 & \\frac{4}{3} & 1 \\end{bmatrix} \\begin{bmatrix} 1 & 0 & 0 \\ 0 & 3 & 0 \\ 0 & 0 & -\\frac{2}{3} \\end{bmatrix} \\begin{bmatrix} 1 & -1 & 2 \\ 0 & 1 & -\\frac{1}{3} \\ 0 & 0 & 1 \\end{bmatrix}$\nD. $\\begin{bmatrix} 1 & 0 & 0 \\ 2 & -1 & 0 \\ 3 & \\frac{4}{3} & 1 \\end{bmatrix} \\begin{bmatrix} 1 & 0 & 0 \\ 0 & -3 & 0 \\ 0 & 0 & -\\frac{2}{3} \\end{bmatrix} \\begin{bmatrix} 1 & -1 & 2 \\ 0 & 1 & -\\frac{1}{3} \\ 0 & 0 & 1 \\end{bmatrix}$"
            },
            {
                "num": 7,
                "page": 18,
                "stem": r"$A,B$ 是 $n$ 阶矩阵，$A^*,B^*$ 分别是 $A,B$ 对应的伴随矩阵，则分块矩阵 $C = \begin{bmatrix} O & A \\ B & O \end{bmatrix}$ 的伴随矩阵 $C^* = $（ ）. ",
                "options": "A. $\\begin{bmatrix} O & |A|A^* \\ |B|B^* & O \\end{bmatrix}$\nB. $\\begin{bmatrix} O & (-1)^n|A|B^* \\ (-1)^n|B|A^* & O \\end{bmatrix}$\nC. $\\begin{bmatrix} O & |B|A^* \\ |A|B^* & O \\end{bmatrix}$\nD. $\\begin{bmatrix} O & (-1)^n|B|B^* \\ (-1)^n|A|A^* & O \\end{bmatrix}$"
            },
            {
                "num": 9,
                "page": 20,
                "stem": r"设 $A,B$ 为 3 阶矩阵，且 $AB = \begin{bmatrix} 0 & 1 & 0 \\ 1 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix}$，则必有（ ）. ",
                "options": "A. 互换矩阵 $A^{-1}$ 的第 1,2 行得矩阵 $B$\nB. 互换矩阵 $A^{-1}$ 的第 1,2 列得矩阵 $B^{-1}$\nC. 互换矩阵 $A$ 的第 1,2 行得矩阵 $B^{-1}$\nD. 互换矩阵 $A$ 的第 1,2 列得矩阵 $B^{-1}$"
            },
            {
                "num": 10,
                "page": 21,
                "stem": r"设 $A$ 为 3 阶矩阵，将 $A$ 的第 1 行加到第 2 行得到 $B$，再将 $B$ 的第 2 列的 -1 倍加到第 1 列得到 $C$，记 $P = \begin{bmatrix} 1 & 1 & 0 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{bmatrix}$，则 $C = $（ ）. ",
                "options": "A. $P^{-1}AP$\nB. $PAP^{-1}$\nC. $P^T AP$\nD. $P^T A (P^T)^{-1}$"
            },
            {
                "num": 11,
                "page": 22,
                "stem": r"设 3 阶矩阵 $A$ 与 $B$ 等价，则下列结论正确的是（ ）. ",
                "options": "A. 存在可逆矩阵 $P$，使得 $PA = B$\nB. 存在可逆矩阵 $Q$，使得 $AQ = B$\nC. 若 $r(A) = 2$，$A$ 可经初等行变换化为矩阵 $B$\nD. 若 $r(A) = 3$，$A$ 可经初等列变换化为矩阵 $B$"
            },
            {
                "num": 12,
                "page": 23,
                "stem": r"设 $A = \begin{bmatrix} a_{11} & a_{12} & a_{13} \\ a_{21} & a_{22} & a_{23} \\ a_{31} & a_{32} & a_{33} \end{bmatrix}$，$B = \begin{bmatrix} a_{21} & a_{22} & a_{23} \\ a_{11} & a_{12} & a_{13} \\ a_{31}+a_{11} & a_{32}+a_{12} & a_{33}+a_{13} \end{bmatrix}$，$P_1 = \begin{bmatrix} 0 & 1 & 0 \\ 1 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix}$，$P_2 = \begin{bmatrix} 1 & 0 & 1 \\ 0 & 1 & 0 \\ 0 & 0 & 1 \end{bmatrix}$，则（ ）. ",
                "options": "A. $AP_1^9 P_2^T = B$\nB. $AP_2^T P_1^9 = B$\nC. $P_1^9 P_2^T A = B$\nD. $P_2^T P_1^9 A = B$"
            },
            {
                "num": 13,
                "page": 24,
                "stem": r"将 3 阶方阵 $A$ 的第 1 行的 2 倍加到第 2 行得到矩阵 $B$，将 3 阶方阵 $C$ 的第 3 列的 -3 倍加到第 1 列得到矩阵 $D$。若 $BD = \begin{bmatrix} 1 & 0 & 0 \\ 0 & 2 & 0 \\ 0 & 0 & 3 \end{bmatrix}$，则 $AC = $（ ）. ",
                "options": "A. $\\begin{bmatrix} 1 & 0 & 0 \\ 2 & 2 & 0 \\ -9 & 0 & 3 \\end{bmatrix}$\nB. $\\begin{bmatrix} 1 & 0 & 0 \\ -2 & 2 & 0 \\ 9 & 0 & 3 \\end{bmatrix}$\nC. $\\begin{bmatrix} -3 & 0 & 0 \\ -6 & 2 & 0 \\ 0 & 0 & 3 \\end{bmatrix}$\nD. $\\begin{bmatrix} 1 & 0 & 0 \\ -2 & 2 & 0 \\ -1 & 0 & 3 \\end{bmatrix}$"
            },
            {
                "num": 14,
                "page": 25,
                "stem": r"设 $A,B$ 是 3 阶矩阵，$A$ 是非零矩阵，且满足 $AB = O$，$B = \begin{bmatrix} 1 & -1 & 1 \\ 2a & 1-a & 2a \\ a & -a & a^2-2 \end{bmatrix}$，则（ ）. ",
                "options": "A. $a = -1$ 时，必有 $r(A) = 1$\nB. $a = 2$ 时，必有 $r(A) = 2$\nC. $a = -1$ 时，必有 $r(A) = 2$\nD. $a = 2$ 时，必有 $r(A) = 1$"
            },
            {
                "num": 15,
                "page": 26,
                "stem": r"设 $A,B,C$ 均是 3 阶方阵，满足 $AB = C$，其中 $B = \begin{bmatrix} 1 & 2 & 2 \\ 2 & 1 & 1 \\ -2 & -1 & a \end{bmatrix}$，$C = \begin{bmatrix} 0 & 0 & 0 \\ 2 & 1 & 1 \\ 0 & 0 & 0 \end{bmatrix}$，则必有（ ）. ",
                "options": "A. $a = -1$ 时，$r(A) = 1$\nB. $a = -1$ 时，$r(A) = 2$\nC. $a \neq -1$ 时，$r(A) = 1$\nD. $a \neq -1$ 时，$r(A) = 2$"
            }
        ]
    },
    "第03章_向量组.md": {
        "title": "《张宇1000题》· 基础篇 · 线性代数 · 第3章 向量组",
        "course": "线性代数",
        "chapter": "第3章 向量组",
        "questions": [
            {
                "num": 1,
                "page": 31,
                "stem": r"$n$ 维向量组 $\alpha_1, \alpha_2, \cdots, \alpha_r (3 \le r \le n)$ 线性相关的充分必要条件是（ ）. ",
                "options": "A. 对于任意一组不全为零的数 $k_1, k_2, \cdots, k_r$，都有 $k_1\alpha_1+k_2\alpha_2+\cdots+k_r\alpha_r = 0$\nB. $\\alpha_1, \\alpha_2, \\cdots, \\alpha_r$ 中任意两个向量都线性相关\nC. $\\alpha_1, \\alpha_2, \\cdots, \\alpha_r$ 中任何一个向量都能由其余向量线性表示\nD. $\\alpha_1, \\alpha_2, \\cdots, \\alpha_r$ 中至少有一个向量能由其余向量线性表示"
            },
            {
                "num": 2,
                "page": 32,
                "stem": r"设 $n$ 阶方阵 $A = [\alpha_1, \alpha_2, \cdots, \alpha_n]$，$B = [\beta_1, \beta_2, \cdots, \beta_n]$，$AB = [\gamma_1, \gamma_2, \cdots, \gamma_n]$，记向量组 $\text{I}: \alpha_1, \alpha_2, \cdots, \alpha_n$，向量组 $\text{II}: \beta_1, \beta_2, \cdots, \beta_n$，向量组 $\text{III}: \gamma_1, \gamma_2, \cdots, \gamma_n$。如果向量组 $\text{III}$ 线性相关，则（ ）. ",
                "options": "A. 向量组 $\\text{I}$ 线性相关\nB. 向量组 $\\text{II}$ 线性相关\nC. 向量组 $\\text{I}$ 与 $\\text{II}$ 都线性相关\nD. 向量组 $\\text{I}$ 与 $\\text{II}$ 至少有一个线性相关"
            },
            {
                "num": 3,
                "page": 33,
                "stem": r"设 $\alpha_1, \alpha_2, \cdots, \alpha_n$ 是 $n$ 个 $n$ 维的线性无关向量，$\alpha_{n+1} = k_1\alpha_1+k_2\alpha_2+\cdots+k_n\alpha_n$，其中 $k_1, k_2, \cdots, k_n$ 全不为 0，则下列结论：\n① $\alpha_2, \alpha_3, \cdots, \alpha_{n+1}$ 线性相关；\n② $\alpha_1, \alpha_3, \cdots, \alpha_{n+1}$ 线性相关；\n③ $\alpha_1, \alpha_2, \alpha_4, \cdots, \alpha_{n+1}$ 线性相关。\n正确的个数为（ ）. ",
                "options": "A. 0\nB. 1\nC. 2\nD. 3"
            },
            {
                "num": 4,
                "page": 34,
                "stem": r"设 $A = \begin{bmatrix} a_{11} & a_{12} & a_{13} & a_{14} \\ a_{21} & a_{22} & a_{23} & a_{24} \\ a_{31} & a_{32} & a_{33} & a_{34} \end{bmatrix}$，对 $A$ 分别以列和行分块，记为 $A = [\alpha_1, \alpha_2, \alpha_3, \alpha_4] = \begin{bmatrix} \beta_1 \\ \beta_2 \\ \beta_3 \end{bmatrix}$，其中 $\begin{vmatrix} a_{12} & a_{14} \\ a_{32} & a_{34} \end{vmatrix} \neq 0$，$\begin{vmatrix} a_{11} & a_{12} & a_{13} \\ a_{21} & a_{22} & a_{23} \\ a_{31} & a_{32} & a_{33} \end{vmatrix} = 0$，则以下结论中：\n① $r(A) = 2$；\n② $\alpha_2, \alpha_4$ 线性无关；\n③ $\beta_1, \beta_2, \beta_3$ 线性相关；\n④ $\alpha_1, \alpha_2, \alpha_3$ 线性相关。\n所有正确结论的序号是（ ）. ",
                "options": "A. ①③\nB. ②③\nC. ①④\nD. ②④"
            },
            {
                "num": 5,
                "page": 35,
                "stem": r"设向量组 $\alpha_1, \alpha_2, \alpha_3$ 线性无关，若向量 $\beta_1$ 可由 $\alpha_1, \alpha_2, \alpha_3$ 线性表示，向量 $\beta_2$ 不能由 $\alpha_1, \alpha_2, \alpha_3$ 线性表示，则必有（ ）. ",
                "options": "A. 向量组 $\\alpha_1, \\alpha_2, \\beta_1$ 线性相关\nB. 向量组 $\\alpha_1, \\alpha_2, \\beta_1$ 线性无关\nC. 向量组 $\\alpha_1, \\alpha_2, \\beta_2$ 线性相关\nD. 向量组 $\\alpha_1, \\alpha_2, \\beta_2$ 线性无关"
            },
            {
                "num": 6,
                "page": 36,
                "stem": r"设 $x_1 = [1,2,2,-4]^T, x_2 = [1,k,-1,-4]^T, x_3 = [-1,-3,1,k+6]^T$，则（ ）. ",
                "options": "A. 对任意常数 $k, x_1, x_2, x_3$ 线性无关\nB. 当 $k = 3$ 时, $x_1, x_2, x_3$ 线性相关\nC. 当 $k = -2$ 时, $x_1, x_2, x_3$ 线性相关\nD. $k \neq 3$ 且 $k \neq -2$ 是 $x_1, x_2, x_3$ 线性无关的充要条件"
            },
            {
                "num": 7,
                "page": 37,
                "stem": r"设 $\alpha_1 = [1,1,0,-2]^T, \alpha_2 = [1,k,-2,0]^T, \alpha_3 = [-1,-3,2,k+4]^T$，则（ ）. ",
                "options": "A. 对任意常数 $k, \alpha_1, \alpha_2, \alpha_3$ 线性无关\nB. 当 $k = 3$ 时, $\\alpha_1, \\alpha_2, \\alpha_3$ 线性相关\nC. 当 $k = -4$ 时, $\\alpha_1, \\alpha_2, \\alpha_3$ 线性相关\nD. $k \neq 3$ 且 $k \neq -4$ 是 $\\alpha_1, \\alpha_2, \\alpha_3$ 线性无关的充要条件"
            },
            {
                "num": 8,
                "page": 38,
                "stem": r"已知向量组 $\alpha, \beta, \gamma$ 线性无关，则 $k \neq 1$ 是向量组 $\alpha+k\beta, \beta+k\gamma, \alpha-\gamma$ 线性无关的（ ）. ",
                "options": "A. 充分必要条件\nB. 充分非必要条件\nC. 必要非充分条件\nD. 既非充分又非必要条件"
            },
            {
                "num": 9,
                "page": 39,
                "stem": r"若向量组 $\alpha_1 = [1,0,2,a]^T, \alpha_2 = [2,1,a,4]^T, \alpha_3 = [0,a,5,-6]^T$ 线性相关，则 $a = $（ ）. ",
                "options": "A. -1\nB. 3\nC. -3\nD. 5"
            },
            {
                "num": 10,
                "page": 40,
                "stem": r"$n$ 维向量组 $\alpha_1, \alpha_2, \cdots, \alpha_s$ 线性无关，$\beta = k_1\alpha_1+k_2\alpha_2+\cdots+k_s\alpha_s$，其中 $k_1, k_2, \cdots, k_s$ 全不为零，则（ ）. ",
                "options": "A. 向量组 $\\alpha_1, \\alpha_2, \\cdots, \\alpha_{s-1}, \\beta$ 线性相关\nB. 向量组 $\\alpha_1, \\alpha_2, \\cdots, \\alpha_s, \\beta$ 线性无关\nC. 向量组 $\\alpha_2, \\alpha_3, \\cdots, \\alpha_s, \\beta$ 线性相关\nD. 向量组 $\\alpha_1, \\cdots, \\alpha_{i-1}, \\beta, \\alpha_{i+1}, \\cdots, \\alpha_s$ 线性无关（当 $k_i \\neq 0$ 时）"
            },
            {
                "num": 11,
                "page": 41,
                "stem": r"设向量 $\alpha_1 = [1,1,2]^T, \alpha_2 = [2,a,4]^T, \alpha_3 = [a,3,6]^T, \alpha_4 = [0,2,2a]^T$，若向量组 $\alpha_1, \alpha_2, \alpha_3, \alpha_4$ 与 $\alpha_1, \alpha_2, \alpha_3$ 不等价，则 $a = $（ ）. ",
                "options": "A. 2\nB. 3\nC. 4\nD. 6"
            },
            {
                "num": 12,
                "page": 42,
                "stem": r"已知向量组 $\alpha_1 = [1,2,-3]^T, \alpha_2 = [3,0,-3]^T, \alpha_3 = [9,6,-15]^T$ 与向量组 $\beta_1 = [0,1,-1]^T, \beta_2 = [3,a,1]^T, \beta_3 = [1,1,b]^T$ 等价，则 $a,b$ 的值分别为（ ）. ",
                "options": "A. -4, 2\nB. 4, -2\nC. -4, -2\nD. 4, 2"
            },
            {
                "num": 13,
                "page": 43,
                "stem": r"设 $\alpha_1 = \begin{bmatrix} 1 \\ 1 \\ 0 \end{bmatrix}, \alpha_2 = \begin{bmatrix} 1 \\ 0 \\ 1 \end{bmatrix}, \alpha_3 = \begin{bmatrix} -1 \\ 0 \\ 0 \end{bmatrix}$，记 $\beta_1 = \alpha_1, \beta_2 = \alpha_2-k_1\beta_1, \beta_3 = \alpha_3-k_2\beta_1-k_3\beta_2$。若 $\beta_1, \beta_2, \beta_3$ 为正交向量组，则 $k_1, k_2, k_3$ 依次为（ ）. ",
                "options": "A. $-\\frac{1}{2}, \\frac{1}{2}, -\\frac{1}{3}$\nB. $-\\frac{1}{2}, \\frac{1}{2}, \\frac{1}{3}$\nC. $\\frac{1}{2}, \\frac{1}{2}, \\frac{1}{3}$\nD. $\\frac{1}{2}, -\\frac{1}{2}, -\\frac{1}{3}$"
            }
        ]
    },
    "第04章_线性方程组.md": {
        "title": "《张宇1000题》· 基础篇 · 线性代数 · 第4章 线性方程组",
        "course": "线性代数",
        "chapter": "第4章 线性方程组",
        "questions": [
            {
                "num": 2,
                "page": 47,
                "stem": r"设 3 维列向量组 $\alpha_1, \alpha_2, \alpha_3$ 线性无关，$k,l$ 均为非零常数，$\beta_1 = k\alpha_1+l\alpha_2, \beta_2 = k\alpha_2+l\alpha_3, \beta_3 = k\alpha_3+l\alpha_1$，记 $B = [\beta_1, \beta_2, \beta_3]$，则齐次线性方程组 $Bx = 0$ 有非零解的充分必要条件为（ ）. ",
                "options": "A. $k - l = 0$\nB. $k + l = 0$\nC. $k - l \\neq 0$\nD. $k + l \\neq 0$"
            },
            {
                "num": 3,
                "page": 48,
                "stem": r"设 $A$ 是 $m \times n$ 矩阵，$B$ 是 $n \times m$ 矩阵，则（ ）. ",
                "options": "A. 当 $m > n$ 时，必有 $|AB| = 0$\nB. 当 $m > n$ 时，$AB$ 必可逆\nC. 当 $n > m$ 时，$ABx = 0$ 有唯一零解\nD. 当 $n > m$ 时，必有 $r(AB) < m$"
            },
            {
                "num": 4,
                "page": 49,
                "stem": r"设 $A$ 为 $n(n > 2)$ 阶方阵，$r(A^*) = 1$，$\alpha_1, \alpha_2$ 是非齐次线性方程组 $Ax = b$ 的两个不同解，$k$ 为任意常数，则方程组 $Ax = b$ 的通解为（ ）. ",
                "options": "A. $(k-1)\alpha_1+k\alpha_2$\nB. $(k-1)\alpha_1-k\alpha_2$\nC. $(k+1)\alpha_1+k\alpha_2$\nD. $(k+1)\alpha_1-k\alpha_2$"
            },
            {
                "num": 8,
                "page": 53,
                "stem": r"设 $A = [\alpha_1, \alpha_2, \cdots, \alpha_n]$ 经过若干次初等行变换得 $B = [\beta_1, \beta_2, \cdots, \beta_n]$，则 $A$ 与 $B$（ ）. ",
                "options": "A. 对应的任何部分行向量组具有相同的线性相关性\nB. 对应的任何部分列向量组具有相同的线性相关性\nC. 对应的任何 $k$ 阶子式同时为零或同时不为零\nD. 对应的非齐次线性方程组 $Ax = b$ 和 $Bx = b$ 是同解方程组"
            },
            {
                "num": 9,
                "page": 54,
                "stem": r"设 $A$ 是 3 阶非零矩阵，满足 $A^2 = O$，若非齐次线性方程组 $Ax = b$ 有解，则其线性无关的解向量的个数为（ ）. ",
                "options": "A. 1\nB. 2\nC. 3\nD. 4"
            },
            {
                "num": 10,
                "page": 55,
                "stem": r"已知线性方程组 $Ax = k\beta_1+\beta_2$ 有解，其中 $A = \begin{bmatrix} 1 & 1 & -1 \\ -1 & -2 & 1 \\ 1 & -1 & -1 \end{bmatrix}, \beta_1 = \begin{bmatrix} 2 \\ 1 \\ 3 \end{bmatrix}, \beta_2 = \begin{bmatrix} 1 \\ 3 \\ -1 \end{bmatrix}$，则 $k$ 等于（ ）. ",
                "options": "A. 1\nB. -1\nC. 2\nD. -2"
            },
            {
                "num": 12,
                "page": 57,
                "stem": r"设 3 维列向量组 $\alpha_1, \alpha_2, \alpha_3$ 与 $\beta_1, \beta_2, \beta_3$ 等价，记 $A = [\alpha_1, \alpha_2, \alpha_3], B = [\beta_1, \beta_2, \beta_3]$，则下列结论：\n① $Ax = 0$ 与 $Bx = 0$ 同解；\n② $A^T x = 0$ 与 $B^T x = 0$ 同解；\n③ $\begin{bmatrix} A \\ B \end{bmatrix} x = 0$ 与 $Ax = 0$ 同解；\n④ $\begin{bmatrix} A^T \\ B^T \end{bmatrix} x = 0$ 与 $A^T x = 0$ 同解。\n所有正确结论的序号是（ ）. ",
                "options": "A. ①②\nB. ①③\nC. ②④\nD. ①②③④"
            },
            {
                "num": 13,
                "page": 58,
                "stem": r"设 $A$ 为 $m \times n$ 矩阵，$e = [1,1,\cdots,1]^T$。若方程组 $Ay = e$ 有解，则对于 $(\text{I}) A^T x = 0$ 与 $(\text{II}) \begin{cases} A^T x = 0, \\ e^T x = 0 \end{cases}$，说法正确的是（ ）. ",
                "options": "A. $(\\text{I})$ 的解都是 $(\\text{II})$ 的解，但 $(\\text{II})$ 的解未必是 $(\\text{I})$ 的解\nB. $(\\text{II})$ 的解都是 $(\\text{I})$ 的解，但 $(\\text{I})$ 的解未必是 $(\\text{II})$ 的解\nC. $(\\text{I})$ 的解不是 $(\\text{II})$ 的解，且 $(\\text{II})$ 的解也不是 $(\\text{I})$ 的解\nD. $(\\text{I})$ 的解都是 $(\\text{II})$ 的解，且 $(\\text{II})$ 的解也都是 $(\\text{I})$ 的解"
            },
            {
                "num": 16,
                "page": 61,
                "stem": r"在空间直角坐标系 $O-xyz$ 中，三张平面 $\pi_1: ax+y-z=1, \pi_2: x+y+bz=a, \pi_3: x+ay-z=1$ 的位置关系如图所示，则（ ）. ",
                "options": "A. $a = -2, b = 2$\nB. $a \neq -2, b = 2$\nC. $a = 1, b = -1$\nD. $a = 1, b \neq -1$"
            },
            {
                "num": 17,
                "page": 62,
                "stem": r"设 $B$ 是 3 阶矩阵，齐次线性方程组 $Bx = 0$ 的解空间的维数为 2，$A = \begin{bmatrix} 1 & 2 & -2 \\ 4 & a & 3 \\ 3 & -1 & 1 \end{bmatrix}$，若 $AB = O$，则齐次线性方程组 $Ax = 0$ 的解空间的维数为（ ）. ",
                "options": "A. 0\nB. 1\nC. 2\nD. 3"
            }
        ]
    },
    "第05章_特征值与特征向量.md": {
        "title": "《张宇1000题》· 基础篇 · 线性代数 · 第5章 特征值与特征向量",
        "course": "线性代数",
        "chapter": "第5章 特征值与特征向量",
        "questions": [
            {
                "num": 1,
                "page": 63,
                "stem": r"已知 $A$ 为 3 阶方阵，$1,1,2$ 是 $A$ 的 3 个特征值，$\alpha_1, \alpha_2, \alpha_3$ 为这 3 个特征值对应的特征向量，则（ ）. ",
                "options": "A. $\\alpha_1, \\alpha_2, \\alpha_3$ 必为矩阵 $2E-A$ 的特征向量\nB. $\\alpha_1-\\alpha_2$ 必为矩阵 $2E-A$ 的特征向量\nC. $\\alpha_1+\\alpha_3$ 必为矩阵 $2E-A$ 的特征向量\nD. $\\alpha_1, \\alpha_2$ 不是矩阵 $2E-A$ 的特征向量，$\\alpha_3$ 必为矩阵 $2E-A$ 的特征向量"
            },
            {
                "num": 2,
                "page": 64,
                "stem": r"设 $A = \begin{bmatrix} 3 & -4 & 0 \\ 4 & -5 & 0 \\ a & 2 & -1 \end{bmatrix}$，若 $A$ 的三重特征值 $\lambda$ 对应两个线性无关的特征向量，则 $a = $（ ）. ",
                "options": "A. 1\nB. 2\nC. -1\nD. 0"
            },
            {
                "num": 3,
                "page": 65,
                "stem": r"已知 $P^{-1}AP = \begin{bmatrix} 1 & 0 & 0 \\ 0 & 3 & 0 \\ 0 & 0 & 3 \end{bmatrix}$，$\alpha_1$ 是矩阵 $A$ 属于特征值 $\lambda = 1$ 的特征向量，$\alpha_2, \alpha_3$ 是矩阵 $A$ 属于特征值 $\lambda = 3$ 的线性无关的特征向量，则矩阵 $P$ 不可以是（ ）. ",
                "options": "A. $[\alpha_1, -2\alpha_2, \alpha_3]$\nB. $[\alpha_1, \alpha_2+\alpha_3, \alpha_2-2\alpha_3]$\nC. $[\alpha_1, \alpha_3, \alpha_2]$\nD. $[\alpha_1+\alpha_2, \alpha_1-\alpha_2, \alpha_3]$"
            },
            {
                "num": 4,
                "page": 66,
                "stem": r"$\lambda = -1$ 是 $A$ 的特征值的充分必要条件为（ ）. ",
                "options": "A. $A^2 = E$\nB. $r(A+E) < n$\nC. $A$ 中每行元素之和为 -1\nD. $A = -E$"
            },
            {
                "num": 5,
                "page": 67,
                "stem": r"设 $A,P$ 都是 $n$ 阶可逆矩阵，$\lambda, \xi$ 分别是 $A$ 的特征值和对应的特征向量，则 $P^{-1}A^*P$ 的特征值和对应的特征向量分别是（ ）. ",
                "options": "A. $\\frac{|A|}{\\lambda}, P^{-1}\\xi$\nB. $\\frac{|A|}{\\lambda}, \\xi$\nC. $\\frac{1}{\\lambda}, P\\xi$\nD. $\\frac{1}{\\lambda}, P^{-1}\\xi$"
            },
            {
                "num": 6,
                "page": 68,
                "stem": r"设 $A$ 是 3 阶矩阵，将 $A$ 的第 2 列加到第 3 列得矩阵 $B$，再将 $B$ 的第 3 行的 -1 倍加到第 2 行得 $\begin{bmatrix} 1 & 1 & 0 \\ 0 & 2 & 0 \\ 0 & 2 & a \end{bmatrix}$，其中 $a$ 为常数，则 $A$ 的特征值为（ ）. ",
                "options": "A. $1, 2, a$\nB. $1, 2, -2$\nC. $1, -1, 2$\nD. $1, a, -a$"
            },
            {
                "num": 7,
                "page": 69,
                "stem": r"下列矩阵中，不能相似对角化的是（ ）. ",
                "options": "A. $\\begin{bmatrix} 1 & 2 & -1 \\ 2 & 0 & 1 \\ -1 & 1 & 0 \\end{bmatrix}$\nB. $\\begin{bmatrix} 3 & 2 & 1 \\ 0 & 2 & 1 \\ 0 & 0 & 0 \\end{bmatrix}$\nC. $\\begin{bmatrix} 2 & 0 & 0 \\ 0 & 2 & 0 \\ 1 & 0 & 1 \\end{bmatrix}$\nD. $\\begin{bmatrix} 0 & 0 & 0 \\ 1 & 2 & 0 \\ 0 & 1 & 2 \\end{bmatrix}$"
            },
            {
                "num": 10,
                "page": 72,
                "stem": r"设 1 与 -1 是矩阵 $A = \begin{bmatrix} 3 & 1 & -2 \\ -a & -1 & a \\ 4 & 1 & -3 \end{bmatrix}$ 的特征值，若矩阵 $A$ 可相似对角化，则 $a = $（ ）. ",
                "options": "A. -1\nB. 0\nC. 1\nD. 2"
            },
            {
                "num": 17,
                "page": 79,
                "stem": r"已知 $A$ 是 3 阶矩阵，$r(A) = 1$，则 $\lambda = 0$ 是 $A$ 的特征值，其重数（ ）. ",
                "options": "A. 必为 2\nB. 可能为 2 或 3\nC. 可能为 1 或 2\nD. 可能为 1,2 或 3"
            },
            {
                "num": 19,
                "page": 81,
                "stem": r"设 $A,B$ 是 $n$ 阶可逆矩阵，且 $A \sim B$，则以下结论中：\n① $A^{-1} \sim B^{-1}$；\n② $A^T \sim B^T$；\n③ $A^* \sim B^*$；\n④ $AB \sim BA$。\n正确结论的个数是（ ）. ",
                "options": "A. 1\nB. 2\nC. 3\nD. 4"
            }
        ]
    },
    "第06章_二次型.md": {
        "title": "《张宇1000题》· 基础篇 · 线性代数 · 第6章 二次型",
        "course": "线性代数",
        "chapter": "第6章 二次型",
        "questions": [
            {
                "num": 1,
                "page": 86,
                "stem": r"$f(x_1,x_2,x_3) = -2x_1x_2-2x_1x_3+6x_2x_3$ 的正惯性指数为（ ）. ",
                "options": "A. 3\nB. 2\nC. 1\nD. 0"
            },
            {
                "num": 2,
                "page": 87,
                "stem": r"设二次型 $f(x_1,x_2,x_3) = ax_1x_2+x_1x_3-x_2x_3$ 的正惯性指数为 2，负惯性指数为 1，则以下结论可能成立的是（ ）. ",
                "options": "A. $a = -1$\nB. $a = 1$\nC. $a \ge 0$\nD. $a < 0$"
            },
            {
                "num": 4,
                "page": 89,
                "stem": r"设二次型 $f(x_1,x_2,x_3) = a(x_1^2+x_2^2+x_3^2)+4(x_1x_2+x_1x_3+x_2x_3)$ 经正交变换可化为标准形 $f = 5y_1^2-y_2^2-y_3^2$，则 $a = $（ ）. ",
                "options": "A. 0\nB. 1\nC. 2\nD. 3"
            },
            {
                "num": 5,
                "page": 90,
                "stem": r"设二次型 $f(x_1,x_2,x_3)$ 在正交变换 $x = Py$ 下的标准形为 $y_1^2+y_2^2-2y_3^2$，其中 $P = [e_1, e_2, e_3]$。若 $Q = [-e_3, e_2, e_1]$，则 $f(x_1,x_2,x_3)$ 在正交变换 $x = Qy$ 下的标准形为（ ）. ",
                "options": "A. $2y_1^2-y_2^2+y_3^2$\nB. $2y_1^2+y_2^2-y_3^2$\nC. $-2y_1^2+y_2^2+y_3^2$\nD. $-2y_1^2-y_2^2+y_3^2$"
            },
            {
                "num": 8,
                "page": 93,
                "stem": r"设 $A = \begin{bmatrix} 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \\ 0 & 1 & 0 & 0 \\ 1 & 0 & 0 & 0 \end{bmatrix}, B = \begin{bmatrix} -1 & 0 & 0 & 0 \\ 0 & -1 & 0 & 0 \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}$，则 $A$ 和 $B$（ ）. ",
                "options": "A. 不相似且不合同\nB. 相似但不合同\nC. 不相似但合同\nD. 相似且合同"
            },
            {
                "num": 9,
                "page": 94,
                "stem": r"设 $A$ 为 $n(n > 1)$ 阶方阵，$i,j = 1,2,\cdots,n; i \neq j$，互换 $A$ 的第 $i$ 行与第 $j$ 行得到矩阵 $B$，再互换 $B$ 的第 $i$ 列与第 $j$ 列得到矩阵 $C$，则 $A$ 与 $C$（ ）. ",
                "options": "A. 等价，相似且合同\nB. 等价，合同但不相似\nC. 合同，相似但不等价\nD. 等价，相似但不合同"
            },
            {
                "num": 10,
                "page": 95,
                "stem": r"下列矩阵中的正定矩阵是（ ）. ",
                "options": "A. $A = \\begin{bmatrix} 2 & -1 & 1 \\ -1 & 1 & 2 \\ 1 & 2 & 0 \\end{bmatrix}$\nB. $B = \\begin{bmatrix} 2 & -1 & 1 \\ -1 & 2 & 2 \\ 1 & 2 & 5 \\end{bmatrix}$\nC. $C = \\begin{bmatrix} 1 & 1 & 2 \\ 1 & 3 & 1 \\ 2 & 1 & -1 \\end{bmatrix}$\nD. $D = \\begin{bmatrix} 1 & 2 & -1 \\ 2 & 5 & -3 \\ -1 & -3 & 2 \\end{bmatrix}$"
            },
            {
                "num": 11,
                "page": 96,
                "stem": r"设 $A$ 为 $n$ 阶方阵，有下列结论：\n① 若 $A$ 的全部顺序主子式为正，则 $A$ 正定；\n② 若 $A$ 相似于对角矩阵 $\Lambda$，则 $A$ 与 $\Lambda$ 合同；\n③ 若 $A$ 与正定矩阵合同，则 $A$ 为正定矩阵。\n则正确结论的个数为（ ）. ",
                "options": "A. 0\nB. 1\nC. 2\nD. 3"
            },
            {
                "num": 14,
                "page": 99,
                "stem": r"设 $A = \begin{bmatrix} -3 & 0 & 0 \\ 0 & -1 & 2 \\ 0 & 2 & 2 \end{bmatrix}, B = \begin{bmatrix} 0 & 3 & 0 \\ 3 & 0 & 0 \\ 0 & 0 & k \end{bmatrix}$，若 $A$ 与 $B$ 合同但不相似，则常数 $k$ 的取值范围为（ ）. ",
                "options": "A. $k > 0$ 且 $k \neq 2$\nB. $k > 0$ 且 $k \neq 3$\nC. $k < 0$ 且 $k \neq -2$\nD. $k < 0$ 且 $k \neq -3$"
            },
            {
                "num": 15,
                "page": 100,
                "stem": r"设二次型 $f(x_1,x_2,x_3) = 4x_1^2+x_2^2+ax_3^2+2x_1x_2-4x_1x_3+2x_2x_3$ 与 $g(y_1,y_2,y_3) = 2y_1^2+by_2^2$ 合同，则（ ）. ",
                "options": "A. $a = 3, b > 0$\nB. $a = 3, b < 0$\nC. $a = 4, b > 0$\nD. $a = 4, b < 0$"
            },
            {
                "num": 16,
                "page": 101,
                "stem": r"设 3 阶实对称矩阵 $A$ 的各行元素之和均为 2，其主对角线元素之和为 5，$r(A) = 2$，则二次型 $f(x_1,x_2,x_3) = x^T Ax$ 满足条件 $x_1^2+x_2^2+x_3^2=1$ 的最大值为（ ）. ",
                "options": "A. $\\frac{1}{5}$\nB. $\\frac{1}{2}$\nC. 2\nD. 3"
            },
            {
                "num": 18,
                "page": 103,
                "stem": r"设 $\alpha, \beta$ 为 $n$ 维列向量，$P = [\alpha, \beta], Q = [\alpha+\beta, 2\alpha]$。若矩阵 $A$ 使得 $P^T AP = \begin{bmatrix} 1 & 0 \\ 0 & 0 \end{bmatrix}$，则 $Q^T AQ = $（ ）. ",
                "options": "A. $\\begin{bmatrix} 1 & 4 \\ 4 & 2 \\end{bmatrix}$\nB. $\\begin{bmatrix} 4 & 2 \\ 2 & 1 \\end{bmatrix}$\nC. $\\begin{bmatrix} 1 & 2 \\ 2 & 4 \\end{bmatrix}$\nD. $\\begin{bmatrix} 2 & 1 \\ 1 & 4 \\end{bmatrix}$"
            },
            {
                "num": 21,
                "page": 106,
                "stem": r"设二次型 $f(x_1,x_2,x_3) = x_1^2+x_2^2+2x_3^2-2x_1x_2$ 的矩阵为 $A$，则与 $A^2$ 既相似又合同的矩阵是（ ）. ",
                "options": "A. $\\begin{bmatrix} 2 & 0 & 0 \\ 0 & 2 & 0 \\ 0 & 0 & 0 \\end{bmatrix}$\nB. $\\begin{bmatrix} 4 & 0 & 0 \\ 0 & 4 & 0 \\ 0 & 0 & 0 \\end{bmatrix}$\nC. $\\begin{bmatrix} 4 & 0 & 0 \\ 0 & 0 & 0 \\ 0 & 0 & 0 \\end{bmatrix}$\nD. $\\begin{bmatrix} 3 & 0 & 0 \\ 0 & 3 & 0 \\ 0 & 0 & 2 \\end{bmatrix}$"
            },
            {
                "num": 22,
                "page": 107,
                "stem": r"下列二次型中，属于正定二次型的是（ ）. ",
                "options": "A. $f_1(x_1,x_2,x_3,x_4) = (x_1-x_2)^2+(x_2-x_3)^2+(x_3-x_4)^2+(x_4-x_1)^2$\nB. $f_2(x_1,x_2,x_3,x_4) = (x_1+x_2)^2+(x_2+x_3)^2+(x_3+x_4)^2+(x_4+x_1)^2$\nC. $f_3(x_1,x_2,x_3,x_4) = (x_1-x_2)^2+(x_2+x_3)^2+(x_3-x_4)^2+(x_4+x_1)^2$\nD. $f_4(x_1,x_2,x_3,x_4) = (x_1-x_2)^2+(x_2+x_3)^2+(x_3+x_4)^2+(x_4+x_1)^2$"
            },
            {
                "num": 26,
                "page": 111,
                "stem": r"$f(x_1,x_2,x_3) = -2x_1x_2-2x_1x_3+6x_2x_3 = 0$ 是（ ）. ",
                "options": "A. 柱面\nB. 单叶双曲面\nC. 双叶双曲面\nD. 锥面"
            }
        ]
    }
}

print("Loaded JC XD successfully")
