# Blind Test 评分：数学一（8 题）

> 评分 worker：SCORER。依据 `outputs/_protocol/EPISODE_SPEC.md`（§3/§5/§6.1/§7/§8）、
> `outputs/_protocol/OPERATOR_DEFINITIONS.md`（算子定义与 8 组边界）、`outputs/blind_test/IMAGE_STATUS.md`（必读）、
> `outputs/blind_test/predictions_math.md`（预测）、`outputs/_index/blind_solutions/solutions_math.md`（标准解）。
> 数学题包 8 题**均不引用示意图**（预测文件 §合规声明 + 标准解文件中无任何 `images/` 引用），
> 故本册 **UNVERIFIABLE = 0**（无"图不可读"这一类不可判定项）。

## 0. 本册使用的计数与判定口径（可复现）

| 约定 | 内容 |
|---|---|
| 评分单元 | 每题 5 个格子：`geometry` / `main_obstacle` / `trigger` / `第一步` / `第二步`（8×5 = 40 格）；另单列 `coverage`（标准解的承重步骤被两条 transition 覆盖的比例） |
| `geometry`/`main_obstacle` 判 HIT 的门槛 | **不是"与标准解不矛盾"，而是"标准解实际走的路能被该描述解释"**。若预测指认的承重机制在标准解路线里根本不需要，判 `PARTIAL_HIT`（M1-24-A-T19 即此例）。 |
| 口径 1（标签歧义） | 结构动作一致、仅标签名不同 → `HIT` + 备注 `label_ambiguity`。本册按 `OPERATOR_DEFINITIONS.md` §0 判定顺序为每个标准解步骤指派"标准标签"，只有**指派的标签与预测标签不同**时才计 `label_ambiguity`。 |
| MISS 分型 | `structure_wrong`（标准解走的是另一条结构）vs `route_choice`（预测的路线本身是同一道题的另一条合法解法，只是标准解文件里收录的是另一条）。两者都计 MISS，但解释力完全不同。 |
| 口径 2（污染分组） | 按预测者自报 `prior_exposure_self_report` 分组，并另按 `basis: pattern_recall` / `trope_component: high` 分组；两者都报。 |
| 口径 3（自评校准） | 优先检验预测者自列的 4 条 UNKNOWN 候选 + 每题 uncertainty 里自认"最没把握"的一项。 |
| OCR 处理 | 标准解公式有 OCR 损坏时，能无歧义恢复的按 `[OCR→]` 标出恢复值并继续评分；**无法无歧义恢复的才判 UNVERIFIABLE**（本册没有触发该条）。 |

---

## M1-21-A-T17 ｜ 微积分（极限）｜ 暴露度 weak-to-moderate（低）｜ pattern_recall 0/2

### 标准解原文摘录

> **【答案】** 1/2
>
> **方法一**
> $$x→0lim(ex−11+∫0xet2dt−sinx1)=x→0lim(ex−1)sinx(1+∫0xet2dt)sinx−ex+1=x→0limx2(1+∫0xet2dt)sinx−ex+1=\cdots=x→0limex2−x→0lim2xex−1=1−21=21.$$
>
> **方法三**
> 由泰勒公式得 $et2=1+t2+o(t2)$ [OCR→ $e^{t^2}=1+t^2+o(t^2)$], 从而
> $$∫0xet2dt=x+3x3+o(x3),$$
> 于是有 $\cdots=x→0lim(ex−11+x−sinx1)=\cdots=1+x→0lim2−sinx−ex=21.$

### 逐项评级

| 项 | 预测 | 标准解实际 | 评级 |
|---|---|---|---|
| geometry | 两项各自 ~1/x 的发散之差；两个分母都是一阶零点，主导项必须精确对消；等价替换会丢掉唯一需要的那一阶 | 方法一把两项并成一个商后，分子分母同阶相消；方法三把 $e^{t^2}$ 展到 $o(t^2)$ 再积分，正是"对消深度"的来源 | **HIT** |
| main_obstacle | "信息被发散性掩盖 + 展开深度未知"，不是"要会算极限" | 标准解的全部难点确实在"相消到哪一阶"，而非公式选择 | **HIT** |
| trigger | 4 条：①两项之差不可单项等价替换 ②被积函数非初等只能局部展开 ③两个分母不同须统一表示 ④`e^x−1`/`sin x` 不是 `x` | 方法一/三都先统一分母再同阶展开；没有任何一处对单项做等价替换 | **HIT** |
| 第一步 | `STATE_REREPRESENTATION`：两项并成一个商，使对消成为单一对象内部结构 | 方法一第一步：$(1+\int)\sin x-e^x+1 \over (e^x-1)\sin x$ | **HIT** |
| 第二步 | `CRITICAL_SCALE_PROBE`：展开到恰好暴露首个非零阶，确认分母同阶 | 方法三：$e^{t^2}=1+t^2+o(t^2)\Rightarrow\int_0^x=x+\frac{x^3}{3}+o(x^3)$，正是"探到首个非零阶" | **HIT** |

**备注**：第一步的 `STATE_REREPRESENTATION` 与 `OPERATOR_DEFINITIONS.md` §0 判定顺序第 1 条（对象/表示是否改变）一致，标签无歧义。coverage 2/2。

---

## M1-24-A-T19 ｜ 微积分（微分中值定理）｜ 暴露度 moderate（高）｜ pattern_recall 0/2

### 标准解原文摘录

> (1) 证明：令 $g(x)=f(0)(1−x)+f(1)x$。令 $F(x)=f(x)−g(x)−2x(1−x)$ **[OCR→ $F(x)=f(x)-g(x)-\frac{x(1-x)}{2}$]**，其中 $x∈(0,1)$。由于 $F(0)=0$，$F(1)=0$，且 $F′′(x)=f′′(x)+1≥0$（因为 $∣f′′(x)∣≤1$），因此 $F(x)$ 为凹函数，从而 $F(x)≥0$ **[OCR→ 与 $F''≥0$、$F(0)=F(1)=0$ 矛盾，应为 $F(x)≤0$]**。于是有 $f(x)−f(0)(1−x)−f(1)x≤2x(1−x)$ **[OCR→ $\le\frac{x(1-x)}{2}$]**。
> 再令 $F(x)=f(x)−g(x)+2x(1−x)$ **[OCR→ $+\frac{x(1-x)}{2}$]** … $F′′(x)=f′′(x)−1≤0$ … 因此 $F(x)$ 为凸函数，从而 $F(x)≥0$。于是有 $f(x)−f(0)(1−x)−f(1)x≥−2x(1−x)$。
> (2) 由 (1) 中 $f(x)−f(0)(1−x)−f(1)x≤2x(1−x)$，两边在 $[0,1]$ 上积分得 …

**OCR 还原说明**：`(x(1−x)/2)'' = −1` 是唯一能与 `F''=f''+1` 相容的取法，且题面右端正是 `x(1−x)/2`；(2) 的答案文本 `∫01f(x)dx−2f(0)+f(1)≤121` 同理还原为 `∫f dx − (f(0)+f(1))/2 ≤ 1/12`。还原后路线自洽可判，故**不判 UNVERIFIABLE**。

### 逐项评级

| 项 | 预测 | 标准解实际 | 评级 |
|---|---|---|---|
| geometry | 目标= f 与弦的偏差；`information_risk`：丢掉 `f'(0)=f'(1)` 则两端局部表示不再共享同一线性系数，界无法收口 | 标准解确实先"减弦"（令 $g(x)=f(0)(1-x)+f(1)x$），但**全程未使用 $f'(0)=f'(1)$**，也不需要"两端表示共享系数"这一机制 | **PARTIAL_HIT** |
| main_obstacle | "两端各自给出含同一未知系数的局部表示，必须把两个表示组合起来把它消掉" | 标准解的承重机制是"构造 $F=f-g\mp\frac{x(1-x)}{2}$ + $F''$ 定号 + 端点为零 ⇒ 双侧不等式"，与"消去共享未知量"无关 | **PARTIAL_HIT** |
| trigger | 5 条，其中第 3 条：看到 $f'(0)=f'(1)$ → 警觉它是"可消去性的燃料" | 标准解**从未引用该条件**（$F=f-g-\frac{x(1-x)}2$，$F(0)=F(1)=0$，$F''=f''+1\ge0$ 即得结论，对任意满足 $|f''|\le1$ 的 $f$ 都成立） | **PARTIAL_HIT**（1/5 条触发信号未被标准解证实；不判 `FALSE_TRIGGER`，理由见备注） |
| 第一步 | `AUXILIARY_OBJECT`：减掉弦，定义偏差函数作为新研究对象 | "令 $g(x)=f(0)(1−x)+f(1)x$。令 $F(x)=f(x)−g(x)-\frac{x(1-x)}2$" | **HIT** |
| 第二步 | `EXACT_ELIMINATION`（前置 `SPACE_AUGMENTATION`）：两端各写局部表示，用与右端结构匹配的权重线性组合，使未知一阶系数精确相消 | 标准解走的是"辅助函数 + 凹凸性定号"，**没有两端局部表示、没有加权组合、没有消去** | **MISS**（`route_choice`） |

### 依据与备注

1. **第二步为什么判 MISS 而不是 HIT**：按 `OPERATOR_DEFINITIONS.md` §1.3，`EXACT_ELIMINATION` 要求"相容约束联立后精确消掉某个未知量"。标准解没有任何联立与消去，而是把待证不等式整体改写成一个函数的定号问题。两者是同一道题的两条不同收口路线。
2. **为什么标 `route_choice` 而不是 `structure_wrong`**：预测的"两端 Taylor 加权组合"是这道 2024 真题的**经典解法**（$(1-x)\times$左端展开 $+x\times$右端展开 ⇒ 线性项 $x(1-x)[f'(0)-f'(1)]=0$ ⇒ 余项被 $\frac{x(1-x)}2$ 控制），数学上完全正确，且恰好用到 $f'(0)=f'(1)$。标准解文件收录的是另一条合法路线。**因此这一条 MISS 有相当成分在测"答案书收了哪条解析"，而不是"预测的结构是否错"** —— 这是本册最重要的方法论发现之一。
3. **为什么不判 `FALSE_TRIGGER`**：`FALSE_TRIGGER` 的定义是"照着这个信号走会做错"。照 trigger 3 走会得到另一条**正确**的证明（见上），只是与标准解文件不同路，故判 PARTIAL 而非 FALSE_TRIGGER。
4. **口径 3（自评校准）**：预测者把"本题第二步"列为 4 条 UNKNOWN 候选的第 1 条，并写"标准解完全可能不走两端 Taylor 加权组合…若如此，我的 T2 会 MISS，而 T1（减弦）大概率仍然 HIT"。**实测完全命中该自评**：T1 HIT、T2 MISS。
5. **词表缺口**：标准解的"构造 $F$ + 由 $F''$ 定号 + $F(0)=F(1)=0$ ⇒ 双侧不等式"在 30 个母算子中**无格可填**（最接近的 `CERTIFICATE_PRODUCTION`/`RIGIDIFY` 都不贴）。按 `OPERATOR_DEFINITIONS.md` §4.4，应走 `CANDIDATE_NEW_OPERATOR`，而不是硬塞。
6. coverage 2/2（步骤都覆盖到了），但第二步是路线分歧。

---

## M1-25-A-T17 ｜ 微积分（定积分计算）｜ 暴露度 weak（低）｜ pattern_recall 0/2（`trope_component: high` 1/2）

### 标准解原文摘录

> **【答案】** $103ln2+101π$ **[OCR→ $\frac{3}{10}\ln 2+\frac{1}{10}\pi$]**
>
> $$∫01(x+1)(x2−2x+2)1dx=∫01(x+1A+x2−2x+2Bx+C)dx=∫01(x+151+x2−2x+2−51x+53)dx=51ln∣1+x∣01−101ln∣x2−2x+2∣01+52arctan(x−1)01$$

### 逐项评级

| 项 | 预测 | 标准解实际 | 评级 |
|---|---|---|---|
| geometry | 被积函数是"两类不同类型因子的乘积"，与可积表示不匹配 | 标准解第一步就是把乘积拆成和 | **HIT** |
| main_obstacle | 结构类型不匹配 + 耦合；须先解耦再把不可约二次因子归约成"平方+常数" | 分解 + 由 $\arctan(x-1)$ 可见的配方归约 | **HIT** |
| trigger | 4 条（乘积形式须解耦 / 判别式为负须配方 / 区间无奇点故难点在表示 / 系数搭配） | 与标准解路线一致 | **HIT** |
| 第一步 | `STATE_REREPRESENTATION`：把乘积型有理函数改写为若干更简单分式之和 | $\int\left(\frac{A}{x+1}+\frac{Bx+C}{x^2-2x+2}\right)dx=\int\left(\frac{1/5}{x+1}+\frac{-\frac15 x+\frac35}{x^2-2x+2}\right)dx$ | **HIT** |
| 第二步 | `NORMALIZE`：对无实根二次因子配方（平移+尺度归约）到"平方+1"，暴露对数导数型与反正切型 | 结果里的 $\ln|x^2-2x+2|$ 与 $\arctan(x-1)$ 只能由 $x^2-2x+2=(x-1)^2+1$ 的平移归约得到 | **HIT**（标准解一行压缩，第二步为隐含动作） |

**备注**：
- 预测者自己把第一步标为"**备选标签** `DEPENDENCY_REORGANIZATION`，无法在无定义情况下判断"。按 `OPERATOR_DEFINITIONS.md` §0 判定顺序第 1 条，部分分式分解改变了对象（乘积→和），**标准标签就是 `STATE_REREPRESENTATION`**，与预测一致，故**不计 `label_ambiguity`**。这是"定义补齐后歧义自行消解"的实例。
- `trope_component: high`（预测者自认"有理函数→部分分式是教科书头号套路"）。按预测者给出的严格口径，本步应计入 `pattern_recall` → 本册在口径 2 的第二个分组里按 **1/2** 计。
- 口径 3：预测者把"第一步是否真的出现在标准解里（标准解也可能先换元再分解）"列为 UNKNOWN 候选第 4 条。**实测标准解第一步就是分解** → 该自评**过于保守**。
- coverage 2/2。

---

## M1-23-A-T18 ｜ 微积分（多元极值）｜ 暴露度 moderate-to-strong（高）｜ pattern_recall 0/2

### 标准解原文摘录

> $${fx′=−2(2y+3xy−5x3)=0 \atop fy′=2y−x2−x3=0}$$，得驻点为 $(0,0),(1,1),(32,2710)$ **[OCR→ $(2/3,10/27)$]**
> 代入点 $(0,0)$ 可得 $A=0,B=0,C=2$，则 $AC−B2=0$ 判别法失效，故当 $x→0$ 时，取 $y=x2+kx3$ 可得 $f(x,y)=kx5$ 故附近值既有大于 $0$ 也有小于 $0$。因此 $(0,0)$ 不是极值点

### 逐项评级

| 项 | 预测 | 标准解实际 | 评级 |
|---|---|---|---|
| geometry | 两条零集曲线在原点相切（$x^2$ vs $x^3$）⇒ 必然退化驻点；符号由层决定 | 标准解正因 $AC-B^2=0$ 才另做符号论证 | **HIT** |
| main_obstacle | "极值判定被一个退化点卡住，二阶判据在那里给出零信息" | "判别法失效" 正是标准解的分水岭 | **HIT** |
| trigger | 5 条（相切⇒退化 / 符号分层 / 关于 y 二次可降维 / 退化点须独立论证 / 不同阶消失） | 全部与标准解吻合 | **HIT** |
| 第一步 | `RESTRICT_SLICE`：用 $f$ 关于 y 二次，把 $\partial f/\partial y=0$ 解成 $y(x)$，二维驻点搜索降到一维曲线 | $f_y'=2y-x^2-x^3=0$ 是 y 的一次方程，驻点 $(2/3,10/27)$ 满足 $y=(x^2+x^3)/2$ —— 标准解必然执行了该消元（只是未叙述顺序） | **HIT** + `label_ambiguity` |
| 第二步 | `CRITICAL_SCALE_PROBE`：放弃二阶信息，比较 $y$ 相对 $x^2$、$x^3$ 的位置（读三层符号区域） | 标准解用**单参数路径族** $y=x^2+kx^3$ 代入得 $f=kx^5$，显式给出两侧符号 | **PARTIAL_HIT** |

**备注**：
- `label_ambiguity`（+1）：标准解的实际动作是"相容约束联立、精确消掉 $y$" → 按 §1.3 标准标签应为 `EXACT_ELIMINATION`；预测用 `RESTRICT_SLICE`。**结构一致、标签不同**，按口径 1 判 HIT 并计入 `label_ambiguity`。
- 第二步判 PARTIAL 的理由：预测抓住了"二阶判据失效 ⇒ 必须改用符号/尺度分析"这一**障碍与方向**（与标准解一致），但**没有预测承重的收口工具**——构造 $y=x^2+kx^3$ 这条单参数路径族作为两侧符号的显式见证。按 §1.4，标准动作更贴 `COUNTEREXAMPLE_PROBE`（构造两条取值否证"是极值"），预测的 `CRITICAL_SCALE_PROBE` 是同一结构的静态描述。预测者自己在 uncertainty 里预判"可能被判 PARTIAL"——**自评准确**。
- 口径 2：`prior_exposure = moderate-to-strong`，预测者声明"刻意未写入任何答案级记忆（驻点坐标、极值数值）"，核对属实：预测文件里确实没有任何坐标或数值。
- coverage 2/2。

---

## M1-22-A-T17 ｜ 微积分（一阶线性 ODE + 渐近线）｜ 暴露度 weak-to-moderate（低）｜ pattern_recall 0/2（`trope_component: high` 1/2）

### 标准解原文摘录

> 解 根据求解公式，$y=e−∫2x1dx[∫(2+x)e∫2x1dxdx+C0]=e−x[∫(2+x)exdx+C0]$ **(1)**  **[OCR→ $e^{-\sqrt x}\left[\int(2+\sqrt x)e^{\sqrt x}dx+C_0\right]$]**
> $∫(2+x)exdx=u=x2∫(2+u)ueudu=\cdots=2u2eu+C1=2xex+C1$ **[OCR→ $=2u^2e^u+C_1=2x\,e^{\sqrt x}+C_1$]**
> $y=e−x(2xex+C)=2x+Ce−x$ **[OCR→ $y=2x+Ce^{-\sqrt x}$]**，代入 $y(1)=3$ … 解得 $C=e$。因此，$y(x)=2x+e1−x$。
> 由于函数 $y(x)=2x+e1−x$ 在 $[0,+∞)$ 上没有无定义的点，故曲线 … 没有铅直渐近线。
> $limx→+∞xy(x)=limx→+∞x2x+e1−x=2$, $limx→+∞[y(x)−2x]=limx→+∞e1−x=0$。因此 $y=2x$ 为曲线 … 的斜渐近线，也是唯一的渐近线。

**OCR 说明**：多处 `x` 实为 `√x`（由 $\int(2+u)u\,2u\,du=2u^2e^u$、$u^2=x$ 唯一确定），`e−x` 实为 $e^{-\sqrt x}$。恢复后整条解自洽（$y=2x+e^{1-\sqrt x}$，$y(1)=2+1=3$ ✓，$y=2x$ 为斜渐近线 ✓），故可判。

### 逐项评级

| 项 | 预测 | 标准解实际 | 评级 |
|---|---|---|---|
| geometry | 目标对象隐式定义；系数在 $x\to0^+$ 奇异；截距来自次阶项；同一份初值信息在两端可见性不同 | 标准解先求显式解，再在两端分别讨论 | **HIT** |
| main_obstacle | "要一个隐式定义对象的极限性质 + 目标要求次阶精度" | "本题主要考查微分方程求解与渐近线的计算" + 必须保留 $e^{1-\sqrt x}$ 项才能得 $\lim(y-2x)=0$ | **HIT** |
| trigger | 5 条（目标是渐近线 / 系数恰是 $\sqrt x$ 的导数 / 定义域 $(0,\infty)$ 两端分别讨论 / 次阶定截距 / 初值常数的两端可见性） | 与标准解逐条吻合 | **HIT** |
| 第一步 | `STATE_REREPRESENTATION`：识别系数 $1/(2\sqrt x)=(\sqrt x)'$，把左端改写为整体导数，一次性精确积分 | 标准解用求解公式（等价于乘 $e^{\sqrt x}$ 后 $(ye^{\sqrt x})'=(2+\sqrt x)e^{\sqrt x}$） | **HIT** |
| 第二步 | `REPAIR_SCALE_MATCHING`：保留到足以定出截距的次阶；同时在 $x\to0^+$ 端判定有无竖直渐近线 | 标准解：先判无铅直、无水平渐近线，再由 $\lim y/x=2$ 与 $\lim(y-2x)=0$ 定出 $y=2x$ —— 截距确实来自被保留下来的 $e^{1-\sqrt x}$ 次阶项 | **HIT** |

**备注**：
- 口径 3：预测者把"标准解是否讨论 $x\to0^+$ 端"列为 UNKNOWN 候选第 2 条，并担心"我 T2 里两端分别判定会多出一块标准解没有的动作，可能被判 PARTIAL 或 FALSE_TRIGGER"。**实测标准解明确讨论了两端**（"没有铅直渐近线"、"没有水平渐近线"）→ 该自评**过于保守**（与 M1-24-A-T19 的精准自评形成对照）。
- `REPAIR_SCALE_MATCHING` 是 `OPERATOR_DEFINITIONS.md` 标注"证据不足（n=4）"的算子。本步我不认为存在一个**明显更贴**的替代标签（`CRITICAL_SCALE_PROBE` 只覆盖"定尺度"的一半），故不计 `label_ambiguity`。
- `trope_component: high`（预测者自认"求渐近线→展开到次阶取截距"是套路）→ 口径 2 严格分组计 1/2。
- coverage 2/2。

---

## M1-21-A-T18 ｜ 微积分（级数收敛域与和函数）｜ 暴露度 weak-to-moderate（低）｜ pattern_recall 0/2

### 标准解原文摘录

> $∑n=1∞un(x)=∑n=1∞e−nx+∑n=1∞n(n+1)xn+1$。
> 当 $limn→∞e−nxe−(n+1)x=e−x<1$，即 $x>0$ 时，$∑n=1∞e−nx$ 收敛。
> 再由 $limn→∞n(n+1)1(n+1)(n+2)1=1$ 得，$∑n=1∞n(n+1)xn+1$ 的收敛半径为 $R=1$。当 $x=±1$ 时，$n=1∑∞n(n+1)(±1)n+1=n=1∑∞n(n+1)1=1$，故 … 的收敛域为 $[−1,1]$。因此级数 … 的收敛域为 $(0,1]$。
> $S2(x)=n=1∑∞n(n+1)xn+1=n=1∑∞nxn+1−n=1∑∞n+1xn+1=\cdots=(1−x)ln(1−x)+x(0<x<1)$。
> 当 $x=1$ 时，由 $S1(1)=e−11$，$S2(1)=1$ 得 $S(1)=e−11+1=e−1e$。

### 逐项评级

| 项 | 预测 | 标准解实际 | 评级 |
|---|---|---|---|
| geometry | 通项是两种不同 n-依赖机制之和；两机制收敛边界不同；闭式有效域小于收敛域 | 标准解拆两块、各自判界，且 $S_2$ 的闭式明标 $(0<x<1)$、$x=1$ 单独给值 | **HIT** |
| main_obstacle | "一个通项装两种收敛机制，边界竞争 + 闭式有效域小于收敛域" | 与标准解结构完全一致 | **HIT** |
| trigger | 5 条（两机制须分别判 / $e^{-nx}$ 的边界是 $x=0$ / 权重 $1/(n(n+1))$ 裂项得对数型且 $x=1$ 单判 / 和函数可能分段 / $x<0$ 侧被直接截断） | 逐条吻合（含"$x=1$ 单独给值"） | **HIT** |
| 第一步 | `INVARIANT_BLOCK_DECOMPOSITION`：按 n-依赖机制拆成两个互不混合的块 | 标准解第一行就是 $\sum e^{-nx}+\sum\frac{x^{n+1}}{n(n+1)}$ | **HIT** |
| 第二步 | `CRITICAL_SCALE_PROBE`：分别探两块在各自临界点（$x=0$、$x=\pm1$）的行为 | 标准解显式判 $x=1$ 与 $x=-1$，并定出 $x>0$ | **HIT** |

**备注（本册最有价值的**覆盖**失败之一）**：
- `coverage = 1/2`。标准解**一半的承重内容是和函数**：把 $\frac{1}{n(n+1)}$ 裂成 $\frac1n-\frac1{n+1}$（望远镜型）并用已知级数求和得 $(1-x)\ln(1-x)+x$。预测的两条 transition 完全没覆盖这一段，预测者自己也如实声明："本题真正的第三块结构动作（把权重裂成望远镜形式、并用已知级数求和函数）我没有写进两条 transition 里…这意味着我对本题的预测**缺了'和函数'这一承重步骤**"。
- 这属于**词表缺口**而非预测错误：预测者另点名了 3 处"现有标签无格可填"的动作（对称适配坐标、沿水平集积分降维、把两个分式并成一个商），加上这里的"权重裂项求和"，共 4 处。按 `OPERATOR_DEFINITIONS.md` §4.4，这些应走 `CANDIDATE_NEW_OPERATOR`。
- 故本题在"步骤级"记 HIT，但在"整题预测完整度"上应视为 **PARTIAL**（SUMMARY 的总表以 `coverage` 列显式记录，不计入 5 格统计）。

---

## M1-24-A-T21 ｜ 线性代数（递推 / $A^n$）｜ 暴露度 moderate（高）｜ pattern_recall **1/2**

### 标准解原文摘录

> 由 $∣λE−A∣=0$ … 得 $λ1=0$，$λ2=1$，$λ3=−2$。
> 当 $λ1=0$ 时，$Ax=0$，得基础解系为 $η1=(1,−1,1)T$。当 $λ2=1$ 时…$η2=(2,−2,3)T$。当 $λ3=−2$ 时…$η3=(−1,2,0)T$。
> 故存在可逆矩阵 $P=(η1,η2,η3)$，使 $P−1AP=01−2$ **[OCR→ $\mathrm{diag}(0,1,-2)$]**，即 $A=PΛP−1$。则 $An=PΛnP−1$ … 由 $αn=Aαn−1$，得 $αn=Anα0$ … $xn=8+(−2)n, yn=−8+(−2)n+1, zn=12.$

### 逐项评级

| 项 | 预测 | 标准解实际 | 评级 |
|---|---|---|---|
| geometry | 目标是"线性映射的第 n 次幂"；A 奇异（第三行是前两行的线性组合）⇒ 存在被抹掉的核方向 | 标准解确实得到 $λ_1=0$，即 A 奇异、存在核方向 | **HIT** |
| main_obstacle | "求 $A^n$ + 谱结构未知 + 存在信息不可逆丢失的方向" | 与标准解一致 | **HIT** |
| trigger | 5 条（目标是 $A^n$ / 第三行是前两行线性组合⇒奇异 / x、y 只通过 z 耦合 / 通项只依赖存活方向投影 / 3×3 整数矩阵需判可对角化） | 标准解三条特征向量互异 ⇒ 可对角化，与"须先判可对角化"的警觉一致 | **HIT** |
| 第一步 | `INVARIANT_BLOCK_DECOMPOSITION`：求谱并把空间分解成不变子空间，使 A 变成标量/分块对角 | $|λE-A|=0 \Rightarrow \lambda=0,1,-2$；$P^{-1}AP=\mathrm{diag}(0,1,-2)$；$A^n=P\Lambda^nP^{-1}$ | **HIT** |
| 第二步 | `QUOTIENT_KERNEL`：把核方向从状态中商掉，只对存活方向展开初值 | 标准解把 $λ=0$ 一并放进 $P$ 与 $\Lambda^n$，核方向由 $0^n=0$ **自动**消失；没有独立的"商核 / 只展开存活方向"步骤 | **PARTIAL_HIT** |

**备注**：
- 第一步的标签**无歧义**：`OPERATOR_DEFINITIONS.md` §1.6 对 `INVARIANT_BLOCK_DECOMPOSITION` 的举例原文就是"按特征子空间"，故预测者担心的"`INVARIANT_BLOCK_DECOMPOSITION` vs `STATE_REREPRESENTATION`（换基）"在定义补齐后并不构成歧义，不计 `label_ambiguity`。
- 第二步的结构洞察**是对的**（核方向对 $n\ge1$ 确实无贡献：$c_1=-10\neq0$ 却不出现在 $α_n$ 里），但它不是标准解的一个独立动作，而是被对角化吸收。判 PARTIAL。
- 口径 3：预测者 uncertainty 第 1 条原文预判"标准解可能把'核方向消失'和'坐标变换'合并在一步里完成（那样 T2 会被判 PARTIAL 而不是 HIT）" → **自评准确**。
- 口径 2：第一步是**全库唯一一条自标 `basis: pattern_recall`** 的数学 transition（预测者主动声明"求 $A^n$ → 对角化"属套路记忆，宁可多标不隐瞒），且 `trope_component: high`。本题 `prior_exposure = moderate`。
- coverage 2/2。

---

## M1-23-A-T22 ｜ 概率论（二维分布）｜ 暴露度 **strong（高）** ｜ pattern_recall 0/2

### 标准解原文摘录

> （1）$Cov(X,Y)=E(XY)−E(X)E(Y)$；$E(XY)=∫−∞+∞∫−∞+∞xyf(x,y)dxdy=∬x2+y2≤1xyπ2(x2+y2)dxdy=0$；$E(X)=\cdots=0$；所以 $Cov(X,Y)=0$.
> （2）当 $−1<x<1$ 时 $fX(x)=∫−∞+∞f(x,y)dy=∫−1−x21−x2π2(x2+y2)dy=2∫01−x2π2(x2+y2)dy=π4[x21−x2+31(1−x2)23]$ … $f(x,y)\neq fX(x)fY(y)$，$X$ 与 $Y$ 不相互独立；
> （3）$FZ(z)=P{Z≤z}=P{X2+Y2≤z}$ … $0≤z<1$ 时，$FZ(z)=∫02πdθ∫0zπ2r3dr=z2$ …

### 逐项评级

| 项 | 预测 | 标准解实际 | 评级 |
|---|---|---|---|
| geometry | 密度只依赖 $x^2+y^2$、支撑是圆盘；存在对目标不可见的角向方向；支撑不是乘积集 | 标准解 (1) 用对称性、(3) 用极坐标，均由该结构驱动 | **HIT** |
| main_obstacle | "目标量在对称方向上不可见/被抵消，但支撑不是乘积集 ⇒ '看起来对称所以独立'是最强错误吸引子" | (2) 正是"密度只依赖 r 却不独立"的判定 | **HIT** |
| trigger | 6 条，第 2 条："看到支撑是**圆盘**而不是矩形 → 独立性几乎必然不成立，不要因为密度只依赖 r 就误判独立" | 标准解 (2) 算出边缘密度后与联合比较 ⇒ 不独立 | **HIT** |
| 第一步 | `STATE_REREPRESENTATION`：换到与对称性匹配的径向/角向坐标，圆盘变矩形、密度只依赖径向、显式带入 Jacobian | 标准解**只在 (3) 用了极坐标**；(1) 用奇对称性直接判零，(2) 用**直角坐标**做二维积分得边缘密度。全题第一步不是换坐标 | **PARTIAL_HIT** |
| 第二步 | `QUOTIENT_KERNEL`：把目标看不见的角向方向商掉——(3) 沿 $Z$ 的水平集积分掉角向，(1) 用同一对称性使交叉矩精确为零 | (3) $F_Z(z)=\int_0^{2\pi}d\theta\int_0^{\sqrt z}\frac2\pi r^3dr$（角向积分 + Jacobian $r$）；(1) 交叉矩由对称性精确为 0 | **HIT** |

**备注**：
- 第一步判 PARTIAL 的理由：预测把"换到径向/角向坐标"当作**贯穿全题的第一步**，而标准解只在小问 (3) 做该动作，且 (1) 完全不需要坐标变换（对称性即可）。方向对、落点与覆盖范围不对。
- 预测者自己点名这是**词表缺口**："这个动作的本质是'换到**对称适配**坐标'，现有标签里没有对应格位，只能塞进 `STATE_REREPRESENTATION`"。本册确认：按 `OPERATOR_DEFINITIONS.md`，该动作确实只能塞进 `STATE_REREPRESENTATION`（§0 第 1 条），属"词表无格可填"而非命名歧义。
- `coverage = 2/3`：标准解第 (2) 问（比较联合与边缘、否定性判定）是承重步骤，两条 transition 均未覆盖（预测者已如实声明"我把它放进了 trigger 而没有放进两条 transition"）。
- 口径 2：`prior_exposure = strong`，预测者声明"我**很可能见过它的标准解**…如果评分口径严格，请把本题整体按 `pattern_recall` 处理——我自己已经认为它的预测价值是可疑的"。核对：预测文件确实未写任何结果数值（协方差值、边缘密度、$Z$ 的密度），符合其声明。

---

## 汇总表（数学）

| 题号 | domain | geometry | main_obstacle | trigger | 第一步 | 第二步 | coverage | prior_exposure | pattern_recall |
|---|---|---|---|---|---|---|---|---|---|
| M1-21-A-T17 | 高数/极限 | HIT | HIT | HIT | HIT | HIT | 2/2 | weak-to-moderate（低） | 0/2 |
| M1-24-A-T19 | 高数/中值定理 | PARTIAL_HIT | PARTIAL_HIT | PARTIAL_HIT | HIT | **MISS**(route_choice) | 2/2 | moderate（高） | 0/2 |
| M1-25-A-T17 | 高数/积分 | HIT | HIT | HIT | HIT | HIT | 2/2 | weak（低） | 0/2（trope_high 1） |
| M1-23-A-T18 | 高数/多元极值 | HIT | HIT | HIT | HIT + `label_ambiguity` | PARTIAL_HIT | 2/2 | moderate-to-strong（高） | 0/2 |
| M1-22-A-T17 | 高数/ODE | HIT | HIT | HIT | HIT | HIT | 2/2 | weak-to-moderate（低） | 0/2（trope_high 1） |
| M1-21-A-T18 | 高数/级数 | HIT | HIT | HIT | HIT | HIT | **1/2** | weak-to-moderate（低） | 0/2 |
| M1-24-A-T21 | 线代 | HIT | HIT | HIT | HIT | PARTIAL_HIT | 2/2 | moderate（高） | **1/2** |
| M1-23-A-T22 | 概率 | HIT | HIT | HIT | PARTIAL_HIT | HIT | 2/3 | **strong（高）** | 0/2 |

## 统计（数学，40 格 / 16 条 transition）

- 40 格：**HIT 33 ｜ PARTIAL_HIT 6 ｜ MISS 1 ｜ FALSE_TRIGGER 0 ｜ UNVERIFIABLE 0**
- 16 条 transition：**HIT 12（75.0%）｜ PARTIAL_HIT 3 ｜ MISS 1（route_choice）｜ FALSE_TRIGGER 0**
- 分列：`geometry` 7 HIT + 1 PARTIAL；`main_obstacle` 7 HIT + 1 PARTIAL；`trigger` 7 HIT + 1 PARTIAL（**FALSE_TRIGGER 0**）
- `label_ambiguity`：**1**（M1-23-A-T18 第一步，`RESTRICT_SLICE` vs 标准 `EXACT_ELIMINATION`）
- `UNVERIFIABLE`：**0**（8 题均不依赖示意图；两处 OCR 损坏均无歧义恢复，见 M1-24-A-T19 / M1-22-A-T17）
- 按领域：高数 6 题（12 transition：HIT 10 / PARTIAL 1 / MISS 1）；线代 1 题（HIT 1 / PARTIAL 1）；概率 1 题（HIT 1 / PARTIAL 1）
- 按暴露度（transition 级）：
  - 高暴露（`moderate` 及以上：T19/T18-2023/T21/T22）＝ 8 条 → **HIT 4 / PARTIAL 3 / MISS 1（50.0%）**
  - 低暴露（`weak` / `weak-to-moderate`：T17-2021/T17-2025/T17-2022/T18-2021）＝ 8 条 → **HIT 8 / PARTIAL 0 / MISS 0（100%）**
- 算子命中（数学 16 条预测标签）：
  | 预测标签 | 次数 | HIT | PARTIAL | MISS |
  |---|---:|---:|---:|---:|
  | `STATE_REREPRESENTATION` | 4 | 3 | 1 | 0 |
  | `CRITICAL_SCALE_PROBE` | 3 | 2 | 1 | 0 |
  | `INVARIANT_BLOCK_DECOMPOSITION` | 2 | 2 | 0 | 0 |
  | `QUOTIENT_KERNEL` | 2 | 1 | 1 | 0 |
  | `AUXILIARY_OBJECT` | 1 | 1 | 0 | 0 |
  | `EXACT_ELIMINATION` | 1 | 0 | 0 | **1** |
  | `NORMALIZE` | 1 | 1 | 0 | 0 |
  | `RESTRICT_SLICE` | 1 | 1(+LA) | 0 | 0 |
  | `REPAIR_SCALE_MATCHING` | 1 | 1 | 0 | 0 |
  | 其余 21 个母算子 | 0 | — | — | — |
