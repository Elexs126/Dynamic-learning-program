# -*- coding: utf-8 -*-
"""
Generator for Zhang Yu 1000: 03_综合篇 (测试卷一 ~ 测试卷四 选择题)
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

# 测试卷一
save_chapter(
    "03_综合篇/测试卷一.md",
    "《张宇1000题》· 综合篇 · 测试卷一（选择题）",
    "本套试卷包含 10 道综合精选选择题（P425 ~ P434），涵盖高等数学、线性代数与概率统计。",
    [
        {
            "num": 1, "page": 425, "course": "高等数学", "chapter": "无穷小量与极限",
            "stem": r"当 $x \to 0^+$ 时，下列无穷小量中，最高阶的是（ ）.",
            "options": "A. $\\int_0^{x^2} (e^{t^2}+1) dt$\nB. $\\int_0^x \\ln(1+\\sqrt{t^3}) dt$\nC. $\\int_0^{\\sin x} \\cos^2 t dt$\nD. $\\int_0^{1-\\cos x} \\sqrt{\\arcsin^3 t} dt$"
        },
        {
            "num": 2, "page": 426, "course": "高等数学", "chapter": "微分方程",
            "stem": r"若微分方程 $y'' + ay' + by = 0$ 的解在 $(-\\infty, +\\infty)$ 上必为周期函数，则（ ）.",
            "options": "A. $a = 0, b > 0$\nB. $a = 0, b < 0$\nC. $a \\neq 0, b < 0$\nD. $a \\neq 0, b > 0$"
        },
        {
            "num": 3, "page": 427, "course": "高等数学", "chapter": "二重积分",
            "stem": r"$\int_{\\frac{1}{4}}^{\\frac{1}{2}} dy \\int_y^{\\sqrt{y}} e^{\\sqrt{x}} dx + \\int_{\\frac{1}{2}}^1 dy \\int_y^{\\sqrt{y}} e^{\\sqrt{x}} dx = $（ ）.",
            "options": "A. $\\frac{3e}{4}-\\frac{\\sqrt{e}}{2}$\nB. $\\frac{3e}{8}-\\frac{\\sqrt{e}}{2}$\nC. $\\frac{3e}{4}+\\frac{\\sqrt{e}}{2}$\nD. $\\frac{3e}{8}+\\frac{\\sqrt{e}}{2}$"
        },
        {
            "num": 4, "page": 428, "course": "高等数学", "chapter": "一元函数微分学",
            "stem": r"设 $f(x) = \\arcsin x - \\frac{x}{1+ax^2}$，$f'''(0) = 2$，则 $a = $（ ）.",
            "options": "A. $\\frac{1}{6}$\nB. $\\frac{1}{4}$\nC. $\\frac{1}{3}$\nD. $\\frac{1}{2}$"
        },
        {
            "num": 5, "page": 429, "course": "线性代数", "chapter": "向量组",
            "stem": r"设向量 $\beta$ 可由向量组 $\alpha_1, \\alpha_2, \\alpha_3, \\alpha_4$ 线性表示，但不可由向量组 $(\\text{I}): \\alpha_1, \\alpha_2, \\alpha_3$ 线性表示，记向量组 $(\\text{II}): \\alpha_1, \\alpha_2, \\alpha_3, \\beta$，则（ ）.",
            "options": "A. $\\alpha_4$ 不可由向量组 $(\\text{I})$ 线性表示，也不可由向量组 $(\\text{II})$ 线性表示\nB. $\\alpha_4$ 不可由向量组 $(\\text{I})$ 线性表示，但可由向量组 $(\\text{II})$ 线性表示\nC. $\\alpha_4$ 可由向量组 $(\\text{I})$ 线性表示，也可由向量组 $(\\text{II})$ 线性表示\nD. $\\alpha_4$ 可由向量组 $(\\text{I})$ 线性表示，但不可由向量组 $(\\text{II})$ 线性表示"
        },
        {
            "num": 6, "page": 430, "course": "线性代数", "chapter": "线性方程组",
            "stem": r"设 $A$ 为 $n$ 阶矩阵，$A^*$ 是 $A$ 的伴随矩阵，齐次线性方程组 $Ax = 0$ 有两个线性无关的解，则（ ）.",
            "options": "A. $A^* x = 0$ 的解均是 $Ax = 0$ 的解\nB. $Ax = 0$ 的解均是 $A^* x = 0$ 的解\nC. $Ax = 0$ 与 $A^* x = 0$ 没有非零公共解\nD. $Ax = 0$ 与 $A^* x = 0$ 仅有两个非零公共解"
        },
        {
            "num": 7, "page": 431, "course": "线性代数", "chapter": "特征值与特征向量",
            "stem": r"设矩阵 $A = [a_{ij}]_{n \\times n}$ 的元素全大于零，且每行元素之和等于 1，以下结论：\n① $\\lambda = 1$ 是 $A$ 的特征值；\n② $(A-E)x = 0$ 有非零解；\n③ $A$ 的每一个特征值 $\\lambda$ 都满足 $|\\lambda| \\le 1$。\n正确结论的个数为（ ）.",
            "options": "A. 0\nB. 1\nC. 2\nD. 3"
        },
        {
            "num": 8, "page": 432, "course": "概率论与数理统计", "chapter": "数字特征",
            "stem": r"设总体 $X$ 的概率分布为 $P(X=-1)=\\frac{1}{4}, P(X=0)=\\frac{1}{2}, P(X=1)=\\frac{1}{4}$。从总体 $X$ 中抽取 $n$ 个简单随机样本，$N_1$ 表示 $n$ 个样本中取到 -1 的个数，$N_2$ 表示 $n$ 个样本中取到 0 的个数，$N_3$ 表示 $n$ 个样本中取到 1 的个数，则 $N_1$ 与 $N_2$ 的相关系数为（ ）.",
            "options": "A. -1\nB. 1\nC. $-\\frac{\\sqrt{3}}{3}$\nD. $\\frac{\\sqrt{3}}{3}$"
        },
        {
            "num": 9, "page": 433, "course": "概率论与数理统计", "chapter": "假设检验",
            "stem": r"设 $X_1, X_2, \\cdots, X_{25}$ 是来自总体 $N(\\mu, \\sigma^2) (\\sigma > 0)$ 的简单随机样本，$\\Phi(x)$ 表示标准正态分布函数，考虑假设检验问题：$H_0: \\mu \\le 10, H_1: \\mu > 10$。若该检验问题的拒绝域为 $W = \\{\\overline{X} > 20\\}$，其中 $\\overline{X} = \\frac{1}{25}\\sum_{i=1}^{25} X_i$。当 $\\mu = 20.5$ 时，该检验犯第二类错误的概率为 $1-\\Phi(\\frac{1}{2})$，则 $\\sigma = $（ ）.",
            "options": "A. 5\nB. 6\nC. 7\nD. 8"
        },
        {
            "num": 10, "page": 434, "course": "概率论与数理统计", "chapter": "参数估计",
            "stem": r"设总体 $X \\sim U(0, \\alpha), Y \\sim U(\\alpha, 2\\alpha), \\alpha > 0$ 为未知参数。$X,Y$ 相互独立。记 $Z_{(a,b)} = aX + bY$，则当 $Z_{(k_1,k_2)}$ 是 $\\alpha$ 的最有效的无偏估计量时，有（ ）.",
            "options": "A. $k_1 = \\frac{1}{3}, k_2 = \\frac{2}{3}$\nB. $k_1 = \\frac{2}{3}, k_2 = \\frac{1}{3}$\nC. $k_1 = \\frac{1}{5}, k_2 = \\frac{3}{5}$\nD. $k_1 = \\frac{1}{2}, k_2 = \\frac{1}{2}$"
        }
    ]
)

# 测试卷二
save_chapter(
    "03_综合篇/测试卷二.md",
    "《张宇1000题》· 综合篇 · 测试卷二（选择题）",
    "本套试卷包含 10 道综合精选选择题（P447 ~ P456），涵盖高等数学、线性代数与概率统计。",
    [
        {
            "num": 1, "page": 447, "course": "高等数学", "chapter": "函数极限与连续",
            "stem": r"函数 $f(x) = \\frac{(e^{\\frac{1}{x-1}}-1)|x|}{(x+1)\\ln|x-1|}$ 的第一类间断点的个数为（ ）.",
            "options": "A. 0\nB. 1\nC. 2\nD. 3"
        },
        {
            "num": 2, "page": 448, "course": "高等数学", "chapter": "多元函数微分学",
            "stem": r"设 $z = z(x,y)$ 是由方程 $\\int_{2x-3y}^z f(2x-3y+z-t) dt = \\sin(2x-3y+z)$ 所确定的函数，其中 $f$ 为大于 1 的连续函数，则（ ）.",
            "options": "A. $3\\frac{\\partial z}{\\partial x} + 2\\frac{\\partial z}{\\partial y} = 0$\nB. $3\\frac{\\partial z}{\\partial x} - 2\\frac{\\partial z}{\\partial y} = 0$\nC. $2\\frac{\\partial z}{\\partial x} + 3\\frac{\\partial z}{\\partial y} = 0$\nD. $2\\frac{\\partial z}{\\partial x} - 3\\frac{\\partial z}{\\partial y} = 0$"
        },
        {
            "num": 3, "page": 449, "course": "高等数学", "chapter": "反常积分",
            "stem": r"设 $a$ 与 $b$ 都是常数，若反常积分 $\\int_0^{+\\infty} \\frac{x^a(1-e^{-x})}{(1+x)^b} dx$ 收敛，则 $a$ 与 $b$ 的取值范围为（ ）.",
            "options": "A. $a < -2, b > a+1$\nB. $a < -2, b < a+1$\nC. $a > -2, b < a+1$\nD. $a > -2, b > a+1$"
        },
        {
            "num": 4, "page": 450, "course": "高等数学", "chapter": "空间解析几何",
            "stem": r"设椭球面 $\\Sigma: x^2+y^2+z^2-yz = 1$，则其在 $xOy$ 面上的投影区域为（ ）.",
            "options": "A. $x^2+\\frac{5}{4}y^2 \\le 1$\nB. $\\frac{3}{4}x^2+y^2 \\le 1$\nC. $x^2+\\frac{3}{4}y^2 \\le 1$\nD. $\\frac{5}{4}x^2+y^2 \\le 1$"
        },
        {
            "num": 5, "page": 451, "course": "线性代数", "chapter": "二次型",
            "stem": r"已知 $\\alpha_1 = [1,2]^T, \\alpha_2 = [a,1]^T, x = [x_1,x_2]^T$，若二次型 $f(x_1,x_2) = \\sum_{i=1}^2 (\\alpha_i, x)^2$ 正定，其中 $(\\alpha_i, x)$ 表示向量 $\\alpha_i, x$ 的内积 $(i=1,2)$，则 $a$ 的取值范围是（ ）.",
            "options": "A. $(-\\infty, \\frac{1}{2}) \\cup (\\frac{1}{2}, +\\infty)$\nB. $(-\\infty, -\\frac{1}{2}) \\cup (-\\frac{1}{2}, +\\infty)$\nC. $(-\\frac{1}{2}, \\frac{1}{2})$\nD. $\\{\\frac{1}{2}\\}$"
        },
        {
            "num": 6, "page": 452, "course": "线性代数", "chapter": "矩阵初等变换",
            "stem": r"下列矩阵中，可以经过若干次初等行变换得到矩阵 $\\begin{bmatrix} 1 & 1 & 0 & 1 \\ 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 0 \\end{bmatrix}$ 的是（ ）.",
            "options": "A. $\\begin{bmatrix} 1 & 1 & 0 & 1 \\ 1 & 2 & 1 & 3 \\ 2 & 3 & 1 & 4 \\end{bmatrix}$\nB. $\\begin{bmatrix} 1 & 1 & 0 & 1 \\ 1 & 1 & 2 & 5 \\ 1 & 1 & 1 & 3 \\end{bmatrix}$\nC. $\\begin{bmatrix} 1 & 0 & 0 & 1 \\ 0 & 1 & 0 & 3 \\ 0 & 1 & 0 & 0 \\end{bmatrix}$\nD. $\\begin{bmatrix} 1 & 1 & 0 & 1 \\ 1 & 2 & 0 & 1 \\ 2 & 3 & 0 & 2 \\end{bmatrix}$"
        },
        {
            "num": 7, "page": 453, "course": "线性代数", "chapter": "向量组与方程组",
            "stem": r"设 $\\alpha_1 = [a_1, a_2, a_3]^T, \\alpha_2 = [b_1, b_2, b_3]^T, \\alpha_3 = [c_1, c_2, c_3]^T$（其中 $a_i^2+b_i^2 \\neq 0, i=1,2,3$），则三条直线 $a_i x+b_i y+c_i = 0 (i=1,2,3)$ 交于一点的充分必要条件是（ ）.",
            "options": "A. $\\alpha_1, \\alpha_2, \\alpha_3$ 线性相关\nB. $\\alpha_1, \\alpha_2, \\alpha_3$ 线性相关，但 $\\alpha_1, \\alpha_2$ 线性无关\nC. 向量组 $\\alpha_1, \\alpha_2, \\alpha_3$ 的秩等于向量组 $\\alpha_1, \\alpha_2$ 的秩\nD. $\\alpha_1, \\alpha_2, \\alpha_3$ 线性无关"
        },
        {
            "num": 8, "page": 454, "course": "概率论与数理统计", "chapter": "一维随机变量",
            "stem": r"设随机变量 $X$ 服从参数为 $\\lambda(\\lambda > 0)$ 的指数分布，若 $P\\{X > D(X)\\} = [P\\{X > E(X)\\}]^3$，则 $\\lambda = $（ ）.",
            "options": "A. 3\nB. $\\frac{3}{2}$\nC. $\\frac{2}{3}$\nD. $\\frac{1}{3}$"
        },
        {
            "num": 9, "page": 455, "course": "概率论与数理统计", "chapter": "随机变量独立性与相关性",
            "stem": r"设随机变量 $X$ 与 $Y$ 相互独立，$D(X) \\cdot D(Y) \\neq 0$，以下结论：\n① $3X+1$ 与 $4Y-2$ 相关；\n② $X+Y$ 与 $X-Y$ 不相关；\n③ $X+Y$ 与 $2Y+1$ 相互独立；\n④ $e^X$ 与 $2Y+1$ 相互独立。\n正确结论的个数为（ ）.",
            "options": "A. 1\nB. 2\nC. 3\nD. 4"
        },
        {
            "num": 10, "page": 456, "course": "概率论与数理统计", "chapter": "假设检验",
            "stem": r"设总体 $X$ 服从 $\\begin{pmatrix} 1 & 0 \\ p & 1-p \\end{pmatrix}, p \\in (0,1)$ 为未知参数。给出假设检验 $H_0: p = k, H_1: p = 1-k$ ($k$ 为常数)，对样本 $X_1, X_2$，拒绝域为 $W = \\{X_1+X_2 < 1\\}$，则犯第二类错误的概率为（ ）.",
            "options": "A. $k^2$\nB. $(1-k)^2$\nC. $1-k^2$\nD. $1-(1-k)^2$"
        }
    ]
)

# 测试卷三
save_chapter(
    "03_综合篇/测试卷三.md",
    "《张宇1000题》· 综合篇 · 测试卷三（选择题）",
    "本套试卷包含 10 道综合精选选择题（P469 ~ P478），涵盖高等数学、线性代数与概率统计。",
    [
        {
            "num": 1, "page": 469, "course": "高等数学", "chapter": "定积分与函数性质",
            "stem": r"设 $f(x) = \\int_0^x (x-2t) e^{-t^2} dt (x \\ge 0), g(x) = \\int_0^x (x-2t) \\sin t^2 dt$，则（ ）.",
            "options": "A. $f(x)$ 单调增加, $g(x)$ 是奇函数\nB. $f(x)$ 单调增加, $g(x)$ 是偶函数\nC. $f(x)$ 单调减少, $g(x)$ 是奇函数\nD. $f(x)$ 单调减少, $g(x)$ 是偶函数"
        },
        {
            "num": 2, "page": 470, "course": "高等数学", "chapter": "一元积分学与不等式",
            "stem": r"设函数 $f(x)$ 在 $[0,1]$ 上二阶可导，则（ ）.",
            "options": "A. 当 $f''(x) < 0$ 时, $f(\\frac{1}{2}) < \\int_0^1 f(x) dx$\nB. 当 $f'(x) > 0$ 时, $f(\\frac{1}{2}) < \\int_0^1 f(x) dx$\nC. 当 $f''(x) < 0$ 时, $f(\\frac{1}{3}) < \\int_0^1 f(x^2) dx$\nD. 当 $f''(x) > 0$ 时, $f(\\frac{1}{3}) < \\int_0^1 f(x^2) dx$"
        },
        {
            "num": 3, "page": 471, "course": "高等数学", "chapter": "多元函数微分学",
            "stem": r"已知函数 $f(x,y)$ 满足 $f(0,0) = 0$，设 $n = (f_x'(0,0), f_y'(0,0), -1), \\alpha = (x,y,f(x,y))$，则 $n \\cdot \\alpha = 0$ 是 $f(x,y)$ 在点 $(0,0)$ 处可微的（ ）.",
            "options": "A. 充分非必要条件\nB. 必要非充分条件\nC. 充分必要条件\nD. 既非充分又非必要条件"
        },
        {
            "num": 4, "page": 472, "course": "高等数学", "chapter": "导数应用与中值",
            "stem": r"设 $f'(x) > 0, f''(x) < 0, x > 0$，对任意的正整数 $n$，记 $I_1 = \\frac{1}{2}[f(n+1)-f(n)], I_2 = f(n)-f(\\frac{2n-1}{2}), I_3 = f(\\frac{2n+1}{2})-f(n)$，则（ ）.",
            "options": "A. $I_1 > I_2 > I_3$\nB. $I_1 > I_3 > I_2$\nC. $I_2 > I_1 > I_3$\nD. $I_2 > I_3 > I_1$"
        },
        {
            "num": 5, "page": 473, "course": "线性代数", "chapter": "矩阵的秩",
            "stem": r"设 $n$ 阶矩阵 $A,B,C$ 满足 $r(ABC)+2n = r(A)+r(B)+r(C)$，则（ ）.",
            "options": "A. $r(A)+r(B)+r(C) = r(AB)$\nB. $r(AB)+n = r(A)+r(B)$\nC. $r(ABC) > r(A)+r(BC)-n$\nD. $r(AB) = r(BC) = n$"
        },
        {
            "num": 6, "page": 474, "course": "线性代数", "chapter": "特征值与二次型",
            "stem": r"设矩阵 $\\begin{bmatrix} 1 & 2 & 0 \\ 2 & a & 1 \\ 0 & 1 & b \\end{bmatrix}$ 有 2 个正特征值和 1 个负特征值，则（ ）.",
            "options": "A. $a > 4, b > 1$\nB. $a < 4, b > 1$\nC. $(a-4)b > 1$\nD. $(a-4)b < 1$"
        },
        {
            "num": 7, "page": 475, "course": "线性代数", "chapter": "向量组与空间几何",
            "stem": r"设 $\\alpha_1, \\alpha_2, \\alpha_3, \\alpha_4$ 是 $n$ 维非零列向量，$x_1\\alpha_1+x_2\\alpha_2 = \\alpha_3$ 有唯一解，且 $\\alpha_1, \\alpha_2, \\alpha_4$ 线性相关。在空间直角坐标系 $O-xyz$ 中，关于 $x,y,z$ 的方程组 $x\\alpha_1+y\\alpha_2+z\\alpha_3 = \\alpha_4$ 的几何图形是（ ）.",
            "options": "A. 过原点的一条直线\nB. 过原点的一个平面\nC. 不过原点的一条直线\nD. 不过原点的一个平面"
        },
        {
            "num": 8, "page": 476, "course": "概率论与数理统计", "chapter": "随机变量的独立性与相关性",
            "stem": r"设随机变量 $X$ 的概率密度为 $f(x) = \\frac{1}{2} e^{-|x|}, x \\in (-\\infty, +\\infty)$，则（ ）.",
            "options": "A. $X$ 与 $|X|$ 不相关, $X$ 与 $|X|$ 不相互独立\nB. $X$ 与 $|X|$ 不相关, $X$ 与 $|X|$ 相互独立\nC. $X$ 与 $|X|$ 相关, $X$ 与 $|X|$ 不相互独立\nD. $X$ 与 $|X|$ 相关, $X$ 与 $|X|$ 相互独立"
        },
        {
            "num": 9, "page": 477, "course": "概率论与数理统计", "chapter": "数字特征",
            "stem": r"将 2 个球随机放入 3 个盒子，每个盒子可放任意个球。设 $X_1, X_2$ 分别表示第一个和第二个盒子中放入的球的个数，$Y_1 = X_1+X_2, Y_2 = X_1-X_2$，则 $E(Y_1)$ 与 $E(Y_2)$ 分别为（ ）.",
            "options": "A. $\\frac{2}{3}, 0$\nB. $\\frac{4}{3}, 0$\nC. $\\frac{2}{3}, \\frac{1}{3}$\nD. $\\frac{4}{3}, \\frac{1}{3}$"
        },
        {
            "num": 10, "page": 478, "course": "概率论与数理统计", "chapter": "大数定律",
            "stem": r"设总体 $X$ 的概率密度为 $f(x) = \\begin{cases} 6x(1-x), & 0 < x < 1 \\ 0, & \\text{其他} \\end{cases}$，$X_1, X_2, \\cdots, X_n, \\cdots$ 为来自总体 $X$ 的简单随机样本，且对任意的 $\\varepsilon > 0$，有 $\\lim_{n \\to \\infty} P\\left\\{ \\left|\\sum_{l=1}^n \\frac{X_{2l}}{nX_{2l-1}} - a\\right| < \\varepsilon \\right\\} = 1$，则 $a = $（ ）.",
            "options": "A. $\\frac{1}{2}$\nB. 1\nC. $\\frac{3}{2}$\nD. $\\frac{5}{2}$"
        }
    ]
)

# 测试卷四
save_chapter(
    "03_综合篇/测试卷四.md",
    "《张宇1000题》· 综合篇 · 测试卷四（选择题）",
    "本套试卷包含 10 道综合精选选择题（P491 ~ P500），涵盖高等数学、线性代数与概率统计。",
    [
        {
            "num": 1, "page": 491, "course": "高等数学", "chapter": "极限与连续",
            "stem": r"若函数 $f(x) = \\begin{cases} \\frac{1-\\cos\\sqrt{x}}{a\\ln(1+x)}, & x > 0 \\ b, & x \\le 0 \\end{cases}$ 在 $x=0$ 处连续，则（ ）.",
            "options": "A. $ab = \\frac{1}{2}$\nB. $ab = -\\frac{1}{2}$\nC. $ab = 0$\nD. $ab = 2$"
        },
        {
            "num": 2, "page": 492, "course": "高等数学", "chapter": "多元函数微分学",
            "stem": r"设 $f(x,y) = \\begin{cases} \\sin x \\cos y, & x \\neq 0 \\ 1-\\cos y, & x = 0 \\end{cases}$，则（ ）.",
            "options": "A. $f_x'(0,0) = 0$\nB. $\\lim_{x \\to 0} \\lim_{y \\to 0} f(x,y) = 0$\nC. $f_{yx}''(0,0) = 1$\nD. $f_y'(0,0) = 1$"
        },
        {
            "num": 3, "page": 493, "course": "高等数学", "chapter": "微分方程",
            "stem": r"已知 $y_1 = xe^x+e^{2x}$ 和 $y_2 = xe^x+e^{-x}$ 是二阶常系数非齐次线性微分方程的两个解，则此方程为（ ）.",
            "options": "A. $y'' - y' + 2y = e^x+2xe^x$\nB. $y'' - y' - 2y = e^x-2xe^x$\nC. $y'' - y' + 2y = e^{2x}-e^{-x}$\nD. $y'' - y' - 2y = xe^x+e^{2x}$"
        },
        {
            "num": 4, "page": 494, "course": "高等数学", "chapter": "无穷级数",
            "stem": r"设 $R$ 为幂级数 $\\sum_{n=1}^\\infty a_n x^n$ 的收敛半径，$r$ 是实数，则（ ）.",
            "options": "A. 当 $\\sum_{n=1}^\\infty a_{2n+1} r^{2n+1}$ 发散时, $|r| \\ge R$\nB. 当 $\\sum_{n=1}^\\infty a_{2n} r^{2n}$ 收敛时, $|r| \\le R$\nC. 当 $|r| \\ge R$ 时, $\\sum_{n=1}^\\infty a_{2n+1} r^{2n+1}$ 发散\nD. 当 $|r| \\le R$ 时, $\\sum_{n=1}^\\infty a_{2n} r^{2n}$ 收敛"
        },
        {
            "num": 5, "page": 495, "course": "线性代数", "chapter": "矩阵与特征向量",
            "stem": r"设 $\\alpha, \\beta$ 是 2 阶实矩阵 $A$ 的两个实特征向量，$\\|\\alpha+\\beta\\| = \\|\\alpha-\\beta\\|$，则矩阵 $A$ 必为（ ）.",
            "options": "A. 正定矩阵\nB. 单位矩阵\nC. 正交矩阵\nD. 对称矩阵"
        },
        {
            "num": 6, "page": 496, "course": "线性代数", "chapter": "二次型",
            "stem": r"二次型 $f(x_1,x_2,x_3) = x_1^2+2x_1x_2+2x_1x_3$ 的符号差（正惯性指数 - 负惯性指数）为（ ）.",
            "options": "A. 2\nB. 1\nC. 0\nD. -1"
        },
        {
            "num": 7, "page": 497, "course": "线性代数", "chapter": "线性方程组",
            "stem": r"若矩阵 $A = [a_{ij}]_{n \\times n}$，对 $i=1,2,\\cdots,n$，均有 $|a_{ii}| > \\sum_{j \\neq i} |a_{ij}|$，其中 $|a_{ij}|$ 表示元素 $a_{ij}$ 的绝对值，$\\beta$ 为任一 $n$ 维列向量，则（ ）.",
            "options": "A. $Ax = 0$ 有非零解\nB. $Ax = \\beta$ 有唯一解\nC. $Ax = \\beta$ 不一定有解\nD. $Ax = 0$ 不一定有非零解"
        },
        {
            "num": 8, "page": 498, "course": "概率论与数理统计", "chapter": "随机变量分布函数",
            "stem": r"设随机变量 $X \\sim \\begin{pmatrix} 1 & 0 \\ p & 1-p \\end{pmatrix}, Y \\sim B(2,p), 0 < p < 1$，$F_X(x), F_Y(y)$ 分别为 $X,Y$ 的分布函数，则（ ）.",
            "options": "A. $P\\{X \\ge Y\\} = 1$\nB. $P\\{X \\le Y\\} = 1$\nC. $F_X(z) \\le F_Y(z)$\nD. $F_X(z) \\ge F_Y(z)$"
        },
        {
            "num": 9, "page": 499, "course": "概率论与数理统计", "chapter": "多维随机变量条件分布",
            "stem": r"设 $(X,Y)$ 的概率密度为 $f(x,y) = \\begin{cases} \\frac{1}{8}(y^2-x^2)e^{-y}, & |x| < y \\ 0, & \\text{其他} \\end{cases}$，则 $P\\{0 < X < 2 \\mid Y = 1\\} = $（ ）.",
            "options": "A. $\\frac{1}{4}$\nB. $\\frac{1}{3}$\nC. $\\frac{1}{2}$\nD. $\\frac{2}{3}$"
        },
        {
            "num": 10, "page": 500, "course": "概率论与数理统计", "chapter": "二维正态分布",
            "stem": r"设 $(X,Y)$ 服从二维正态分布 $N(0,0; 1,4; \\frac{1}{2})$，则下列随机变量中与 $X$ 相互独立且同分布的是（ ）.",
            "options": "A. $\\frac{\\sqrt{3}}{3}(X+Y)$\nB. $\\frac{\\sqrt{5}}{5}(X+Y)$\nC. $\\frac{\\sqrt{3}}{3}(X-Y)$\nD. $\\frac{\\sqrt{5}}{5}(X-Y)$"
        }
    ]
)

print("Finished 03_综合篇")
