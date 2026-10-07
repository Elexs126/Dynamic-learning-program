# `key_transitions[].operation` 是否描述了结构动作

由 `check_operation_labels.py` 生成。母算子词表解析自 SPEC §7，anti-operator 解析自 §8。

- 母算子词表：34 个 ｜ anti-operator 词表：16 个
- **命中问题条目：86**

## 为什么这道闸门重要

下游按 `operation` 检索"这题做了什么结构动作"。
若 `operation` 填的是"转变前的假设/提问"，或填了描述**失败**的 anti-operator，
检索结果就会指向**什么都没做的事**，或指向**反方向**。

## ⚠️ 这是分诊，不是判决

`operation` 用自然语言描述动作而没写标签，**本身可能是写法差异，不一定是错误**。
必须回读原文判断"它到底有没有描述一个动作"。

## 各 worker 命中率

| worker | transition 数 | 无算子标签 | anti 在动作位 | 已废弃标签 | 问题占比 |
|---|---:|---:|---:|---:|---:|
| C1 | 25 | 0 | 0 | 0 | 0% |
| C2 | 54 | 23 | 0 | 0 | 43% |
| C3 | 24 | 0 | 0 | 0 | 0% |
| C4 | 24 | 0 | 0 | 0 | 0% |
| M1 | 22 | 0 | 0 | 0 | 0% |
| M2 | 36 | 14 | 0 | 0 | 39% |
| M3 | 47 | 0 | 0 | 0 | 0% |
| M4 | 46 | 1 | 0 | 0 | 2% |
| M5 | 40 | 9 | 0 | 0 | 22% |
| M6 | 42 | 5 | 0 | 0 | 12% |
| M7 | 60 | 34 | 0 | 0 | 57% |
| M8 | 27 | 0 | 0 | 0 | 0% |

## 明细（86 条）

| problem_id | worker | T# | 类型 | operation 开头 |
|---|---|---:|---|---|
| C2-003 | C2 | 2 | `NO_OPERATOR_LABEL` | 引入 w 后自然会认为写者已被严格优先 |
| C2-010 | C2 | 1 | `NO_OPERATOR_LABEL` | C3 是'修改'，与 C2 的'读'在题面并列出现，容易被归为同类 |
| C2-011 | C2 | 1 | `NO_OPERATOR_LABEL` | 题面把铁锹放在括号式的补充说明里，不像同步约束 |
| C2-012 | C2 | 1 | `NO_OPERATOR_LABEL` | 二者通常同向，容易被合并 |
| C2-013 | C2 | 1 | `NO_OPERATOR_LABEL` | 层数增加意味着地址变换链变长，开销上升 |
| C2-014 | C2 | 1 | `NO_OPERATOR_LABEL` | 页号是唯一给出的索引量 |
| C2-015 | C2 | 1 | `NO_OPERATOR_LABEL` | 紧凑能把空闲块合并成大块，是对症手段 |
| C2-016 | C2 | 1 | `NO_OPERATOR_LABEL` | 置换的目标是降低缺页率，访问情况是唯一相关因素 |
| C2-016 | C2 | 2 | `NO_OPERATOR_LABEL` | 多轮扫描必然增加开销 |
| C2-017 | C2 | 1 | `NO_OPERATOR_LABEL` | 页框分配是运行时决策，没有先验依据 |
| C2-018 | C2 | 1 | `NO_OPERATOR_LABEL` | 共享必然需要映射信息，开销似乎只与大小有关 |
| C2-019 | C2 | 1 | `NO_OPERATOR_LABEL` | 为每个文件配一个索引块，文件越大索引块越多 |
| C2-019 | C2 | 2 | `NO_OPERATOR_LABEL` | 混合索引似乎是折中妥协 |
| C2-020 | C2 | 1 | `NO_OPERATOR_LABEL` | 多个用户共享同一文件，副本唯一最省空间 |
| C2-022 | C2 | 1 | `NO_OPERATOR_LABEL` | 中断已解放了等待时间，剩余开销似乎可接受 |
| C2-022 | C2 | 2 | `NO_OPERATOR_LABEL` | DMA 已把 CPU 从搬运中剥离，剩余参数设置开销很小 |
| C2-023 | C2 | 1 | `NO_OPERATOR_LABEL` | 双缓冲已实现设备与 CPU 并行，应已足够 |
| C2-024 | C2 | 1 | `NO_OPERATOR_LABEL` | 就近贪心的局部最优无法保证全局公平 |
| C2-024 | C2 | 2 | `NO_OPERATOR_LABEL` | SCAN 的两端折返使靠近折返点的请求被优先服务 |
| C2-024 | C2 | 3 | `NO_OPERATOR_LABEL` | 算法层面已足够公平，问题应出在请求本身 |
| C2-025 | C2 | 1 | `NO_OPERATOR_LABEL` | 折中方案似乎能两者兼得 |
| C2-026 | C2 | 0 | `NO_OPERATOR_LABEL` | 软件检查实现简单且灵活 |
| C2-026 | C2 | 1 | `NO_OPERATOR_LABEL` | 直接跳转不可行，自行置位模式位被禁止 |
| M2-003 | M2 | 1 | `NO_OPERATOR_LABEL` | 局部化（极限保号性的“脱帽法”）：由 f'_+(a)>0 得存在 δ1 使 (a,a+δ1) 内 f(x)>f(a)；由 f'_-(b)<0 得存在 δ2 使  |
| M2-007 | M2 | 1 | `NO_OPERATOR_LABEL` | 证书类型切换：放弃罗尔（只给 =0），改用拉格朗日中值定理于 F 在 [0,a] 上 |
| M2-010 | M2 | 1 | `NO_OPERATOR_LABEL` | 介值定理（连续函数取平均值）：由 f''' 在 [η1,η2] 上连续，取最大值 M 与最小值 m，得 m≤(f'''(η1)+f'''(η2))/2=3≤M |
| M2-012 | M2 | 0 | `NO_OPERATOR_LABEL` | 常数变量化：把其中一个常数（b）替换为变量 x，把不等式升级成关于 x 的函数不等式 |
| M2-012 | M2 | 1 | `NO_OPERATOR_LABEL` | 求导 + 配方：φ'(x) 的分子为 2√(ax)-x-a = -(√x-√a)²<0（分母 2x√(ax)>0） |
| M2-012 | M2 | 2 | `NO_OPERATOR_LABEL` | 换回中值定理：对 ln x 在 [a,b] 用拉格朗日中值定理得 (ln b-ln a)/(b-a)=1/ξ，ξ∈(a,b)；再用 1/ξ>1/b 与 a²+b |
| M2-013 | M2 | 1 | `NO_OPERATOR_LABEL` | 代入 (1) 的结论 f(ξ)=1-ξ，得 f'(η)=(1-ξ)/ξ 与 f'(τ)=ξ/(1-ξ) |
| M2-015 | M2 | 1 | `NO_OPERATOR_LABEL` | 判据反用 + 因式分解对齐重数：对每个 f_i 把绝对值内的多项式分解，找出全部实根；再检查每个根是否也是外面 (x²-1) 的根 |
| M2-017 | M2 | 1 | `NO_OPERATOR_LABEL` | 对称扩展 + 积分因子：由奇函数 ⇒ f' 为偶函数 ⇒ f'(-ξ)=f'(ξ)=1（复用 (I)）；令 G(x)=e^x[f'(x)-1]，则 G(ξ)=G |
| M2-018 | M2 | 1 | `NO_OPERATOR_LABEL` | 夹逼 + 链式传递：在 (a,b) 取 x1<x2<x3<x4<x5，由条件得四个差商严格递增；对第一个不等式令 x2→x1+ 得 f'_+(x1)≤(f(x3 |
| M2-019 | M2 | 1 | `NO_OPERATOR_LABEL` | 整体化（积分）：对 (1) 在 [0,1] 上积分，利用 ∫₀¹x(1-x)/2 dx=1/12 |
| M2-020 | M2 | 1 | `NO_OPERATOR_LABEL` | 与几何级数比较（比较判别法）：Σ(1/2)^{n-1}/x_2-x_1/ 收敛 ⇒ Σ(x_{n+1}-x_n) 绝对收敛 |
| M2-021 | M2 | 1 | `NO_OPERATOR_LABEL` | UNKNOWN —— 讲义直接给出封闭公式 k1+2k2+3k3-2，未给出从单点规则到全局计数的推导；本 worker 无法从材料中恢复 |
| M2-022 | M2 | 1 | `NO_OPERATOR_LABEL` | UNKNOWN —— 材料只给出“新概念：{f_n(x)} 函数列———族函数”这一句，未说明这一提升要解决什么问题，也未继续研究 {x_n} |
| M4-003 | M4 | 1 | `NO_OPERATOR_LABEL` | 等价无穷小 + 符号分析：ln(1+u)~u 把第一个极限化为 lim /x sin1//x，再分离左右极限看符号 |
| M5-005 | M5 | 1 | `NO_OPERATOR_LABEL` | 可分离变量 + 初值定常数：dp/[p(1+p^2)] = dx，积分并用 p(0)=y'(0)=1 定 C1 |
| M5-010 | M5 | 2 | `NO_OPERATOR_LABEL` | 三角换元 x = sin t 积分，并用初始条件 Q=(1,0) 定常数 |
| M5-011 | M5 | 1 | `NO_OPERATOR_LABEL` | 调用极值第二充分条件收口 |
| M5-012 | M5 | 1 | `NO_OPERATOR_LABEL` | 放缩估计 + 分离 C 的作用：由 /f/ ≤ M 得 /∫_0^x f e^{at}dt/ ≤ (M/a)(e^{ax} - 1)，故 /y/ ≤ M/a + |
| M5-013 | M5 | 1 | `NO_OPERATOR_LABEL` | 回代 t = ln x（逆换元） |
| M5-014 | M5 | 1 | `NO_OPERATOR_LABEL` | 合并两支（把对数统一写成 ln/x/，并统一常数记号） |
| M5-015 | M5 | 1 | `NO_OPERATOR_LABEL` | 选取合适的线性组合（用两解的公共部分构造一个已知解）代入原方程 |
| M5-018 | M5 | 0 | `NO_OPERATOR_LABEL` | 检查解流形的可达范围（由 1+y^2 > 1 与 x^2/(1+x^2) < 1 反推 C 的约束）：由 (1+y^2) = C·x^2/(1+x^2) 且左端 |
| M5-020 | M5 | 1 | `NO_OPERATOR_LABEL` | 位移公式 + 求逆规则：用 1/F(D)[e^{αx}v(x)] = e^{αx}[1/F(D+α)]v(x) 把指数因子提到外面，再对化简后的算子多项式在自由 |
| M6-002 | M6 | 1 | `NO_OPERATOR_LABEL` | 解一阶线性 ODE（积分因子法），再用展开中心处的值 S(0)=0 定常数 |
| M6-004 | M6 | 1 | `NO_OPERATOR_LABEL` | 先导后积：把求导动作逆转，用 f(x)=f(0)+∫₀ˣ f'(t)dt 还原（积分下限取展开中心 0） |
| M6-006 | M6 | 1 | `NO_OPERATOR_LABEL` | 换问题而非换工具：从'用判别法判级数'改为'用必要条件判通项'——利用 (1+1/n)^n 单调增且收敛到 e，得 u_{n+1}/u_n = e/(1+1/n |
| M6-011 | M6 | 1 | `NO_OPERATOR_LABEL` | 取逆否命题：把'/r/<R ⇒ 收敛'取逆否，得'发散 ⇒ /r/≥R' |
| M6-019 | M6 | 2 | `NO_OPERATOR_LABEL` | 性质1 的推论：收敛 ± 发散 = 发散 |
| M7-002 | M7 | 1 | `NO_OPERATOR_LABEL` | 由右端是 $E$ 判定 $A-B$ 可逆（$/A-B/\neq0$），左右同时乘 $(A-B)^{-1}$ |
| M7-004 | M7 | 1 | `NO_OPERATOR_LABEL` | 用方阵的等价刻画 $Ax=0$ 有非零解 $\Leftrightarrow r(A)<n \Leftrightarrow /A/=0$ |
| M7-005 | M7 | 0 | `NO_OPERATOR_LABEL` | 把判据从『特征值』换成『特征子空间维数 vs 代数重数』，对每个重根计算 $n-r(\lambda E-A)$ |
| M7-005 | M7 | 1 | `NO_OPERATOR_LABEL` | 用秩而不是求解去数维数：$\dim\ker(\lambda E-A)=n-r(\lambda E-A)$ |
| M7-008 | M7 | 1 | `NO_OPERATOR_LABEL` | 直接用克拉默法则的逆否命题跳到 $/A/=0$，不再经过秩的语言 |
| M7-009 | M7 | 1 | `NO_OPERATOR_LABEL` | 用 $/XY/=/X//Y/$ 与 $/A^{-1}/=1//A/$ 计算 |
| M7-010 | M7 | 1 | `NO_OPERATOR_LABEL` | 把 $A$ 与 $B$ 拼成增广矩阵 $[A\mid B]$，一次性高斯消元（三个方程组的消元过程完全相同） |
| M7-010 | M7 | 2 | `NO_OPERATOR_LABEL` | 读出自由变量并写成参数形式 |
| M7-011 | M7 | 1 | `NO_OPERATOR_LABEL` | 由右端为 $E$ 判定 $A-B$ 与 $A+B$ 均可逆，左乘 $(A-B)^{-1}$、右乘 $(A+B)^{-1}$ |
| M7-012 | M7 | 1 | `NO_OPERATOR_LABEL` | 用『存在非零二阶子式』给下界、用『$/A/=0$』给上界，把秩等式翻译成行列式方程 |
| M7-013 | M7 | 0 | `NO_OPERATOR_LABEL` | 先算修正项的幂：令 $B=\alpha\beta^{\mathrm{T}}$，则 $B^2=\alpha(\beta^{\mathrm{T}}\alpha)\b |
| M7-013 | M7 | 1 | `NO_OPERATOR_LABEL` | 把二项式展开 $(E+B)^{-1}=E-B+B^2-\cdots$ 在 $B^2=O$ 处截断，得 $(E+B)^{-1}=E-B$ |
| M7-014 | M7 | 1 | `NO_OPERATOR_LABEL` | 从相关性的定义出发：存在不全为零的 $k_1,\cdots,k_s$ 使 $\sum k_i\alpha_i=0$；由 $\alpha_s$ 不可表出推出 $k |
| M7-015 | M7 | 1 | `NO_OPERATOR_LABEL` | 解这个三元齐次方程组，得 $x_1=-7t,x_2=3t,x_3=t$ |
| M7-016 | M7 | 1 | `NO_OPERATOR_LABEL` | 取任意 $x$ 使 $ABx=0$，令 $y=Bx$；则 $Ay=0$，由 $A$ 单射得 $y=0$，即 $Bx=0$ |
| M7-017 | M7 | 0 | `NO_OPERATOR_LABEL` | 利用相似的函子性：$A\sim B\Rightarrow A^{2}+A-2E\sim B^{2}+B-2E$，把整个多项式搬到已知矩阵 $B$ 上 |
| M7-017 | M7 | 2 | `NO_OPERATOR_LABEL` | 检验 $B+2E=\begin{bmatrix}4&1&3\\1&3&0\\3&0&3\end{bmatrix}$ 可逆，于是 $r[(B+2E)(B-E)]= |
| M7-018 | M7 | 0 | `NO_OPERATOR_LABEL` | 把多项式方程作用在特征向量上得 $(\lambda^2-2\lambda)\alpha=0$，定出候选集；再用『$\alpha_1$ 是基础解系』给出 $r(A |
| M7-018 | M7 | 1 | `NO_OPERATOR_LABEL` | 用实对称矩阵不同特征值的特征向量互相正交这一性质，求 $\alpha_1$ 的正交补（即 $x_2+x_3=0$ 的解空间），取一组基 $\alpha_2=(1 |
| M7-018 | M7 | 2 | `NO_OPERATOR_LABEL` | 用谱的平移：$A+kE$ 的特征值为 $k,k+2,k+2$；规范形 $y_1^2+y_2^2-y_3^2$ 要求正惯性指数 $2$、负惯性指数 $1$ |
| M7-019 | M7 | 1 | `NO_OPERATOR_LABEL` | 由 $A$ 正定得存在可逆 $C$ 使 $C^{\mathrm{T}}AC=E$；对等式两边取逆，整理成 $P^{\mathrm{T}}A^{-1}P=E$（$ |
| M7-019 | M7 | 2 | `NO_OPERATOR_LABEL` | 设 $A^{-1}$ 的特征值为 $\lambda_1,\cdots,\lambda_n$，则 $A$ 的特征值为 $1/\lambda_i$；由 $A$ 正定 |
| M7-020 | M7 | 1 | `NO_OPERATOR_LABEL` | 对增广矩阵作初等行变换，化为行阶梯形，读出使 $r(A)=r(\overline{A})$ 的条件 |
| M7-020 | M7 | 2 | `NO_OPERATOR_LABEL` | 读出齐次部分的基础解系 $\xi_1=(1,-1,1,0)^{\mathrm{T}},\ \xi_2=(1,0,0,1)^{\mathrm{T}}$ 与一个特解 |
| M7-021 | M7 | 1 | `NO_OPERATOR_LABEL` | 对 $A$ 用幂等性 $A^{2}=A$（等价于 $A$ 的极小多项式无重根，必可对角化）；对 $B$ 用 $r(0E-B)=r(B)=1$，得零特征值的几何重 |
| M7-022 | M7 | 0 | `NO_OPERATOR_LABEL` | 两侧夹逼：由 $\alpha_3=\alpha_1+2\alpha_2$ 得列向量线性相关，$r(A)<3$；由 3 个互异特征值得 $A$ 可对角化、零特征值 |
| M7-022 | M7 | 1 | `NO_OPERATOR_LABEL` | 直接读出特解：题面已把 $\beta$ 写成 $\alpha_1+\alpha_2+\alpha_3$，即 $A(1,1,1)^{\mathrm{T}}=\be |
| M7-022 | M7 | 2 | `NO_OPERATOR_LABEL` | 同样直接读出：第 (Ⅰ) 问用过的 $\alpha_1+2\alpha_2-\alpha_3=0$ 就是 $A(1,2,-1)^{\mathrm{T}}=0$， |
| M7-023 | M7 | 1 | `NO_OPERATOR_LABEL` | 对 $C$ 作初等行变换，算 $/C/=a-2$ |
| M7-023 | M7 | 2 | `NO_OPERATOR_LABEL` | 注意到当 $C$ 可逆时，$y=Cx$ 本身就是一个合法的（非正交）坐标变换，且 $f=\/y\/^2=y_1^2+y_2^2+y_3^2$，规范形直接读出；$ |
| M7-024 | M7 | 1 | `NO_OPERATOR_LABEL` | 用 $A^{*}A=/A/E=3E$ 左乘 $\mathbf{1}$ 的两侧：$A^{*}(A\mathbf{1})=A^{*}(2\mathbf{1})=2A |
| M7-025 | M7 | 1 | `NO_OPERATOR_LABEL` | 在方程两端左乘 $E-A^{-1}$ |
| M7-026 | M7 | 1 | `NO_OPERATOR_LABEL` | 把它按分量分解：$\beta\alpha^{\mathrm{T}}-\alpha\beta^{\mathrm{T}}=\begin{bmatrix}y_1\\y |
| M7-026 | M7 | 2 | `NO_OPERATOR_LABEL` | 计算 $\alpha^{\mathrm{T}}\begin{bmatrix}0&a\\-a&0\end{bmatrix}\beta=-a(x_1y_2-x_2y |

## 建议处置

1. `ANTI_OPERATOR_IN_ACTION` / `DEPRECATED_LABEL_IN_ACTION`：**机械可改**——
   从 `operation` 里删掉该标签（保留动作描述），或换成对应的母算子。
2. `NO_OPERATOR_LABEL`：需回读——若 `operation` 确实是"假设/提问/观察"，
   应把真动作从 `after_state` 移回 `operation`，原假设移入 `why_triggered`。
3. **不应删除这些条目**：缺陷在字段落位，不在内容本身。

