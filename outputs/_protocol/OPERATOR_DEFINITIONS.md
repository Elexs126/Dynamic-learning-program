# 母算子定义与边界 v1.0

> **本文件解决什么问题**：`EPISODE_SPEC.md` §7/§8 最初只给了**裸标签、没有定义**。
> 盲测预测者实测指出："我预测出'部分分式分解'后，**无法判断**它属于
> `STATE_REREPRESENTATION` / `DEPENDENCY_REORGANIZATION` / `INFORMATION_AXIS_DECOMPOSITION` 中的哪一个。"
>
> 后果有两个，都已实测到：
> 1. **同一道题被不同 worker 指派了不同标签**——`M1-16-A-T19` 被 M1/M2/M6 各立一条，
>    三个 worker 给出三套主算子。这不是"结构理解不同"，很大程度是**没有共同定义**。
> 2. **盲测的 HIT/MISS 有一部分在测量命名约定，而不是结构预测准确度。**
>
> 本文件的定义**从实际用法反推**（依据 `_index/operator_usage_evidence.md` 里
> 各算子的 `why` 与 trigger 原文），不是先验规定的。凡实测样本不足的，明确标注。

---

## 0. 怎么用：选标签的判定顺序

不要先想"这题用了什么方法"，而要按下面顺序问：

```
1. 这一步**改变了问题的对象/表示**吗？          → STATE_REREPRESENTATION
2. 还是只**把注意力限制到一个子集/切片**上？      → RESTRICT_SLICE
3. 还是**引入了一个原本不存在的新对象**？         → AUXILIARY_OBJECT
4. 还是**把某个量拆成互不耦合的块**？            → INVARIANT_BLOCK_DECOMPOSITION
5. 还是**把不可见的自由度商掉**？                → QUOTIENT_KERNEL
6. 还是**把多个约束/信息合并成一条**？            → EXACT_ELIMINATION
7. 以上都不是，只是**估计/试算/探边界**？          → PROBE 家族
```

**判据的核心是"这一步之后，问题的对象变了没有"**，而不是"这一步用了什么工具"。
用洛必达可以是 `STATE_REREPRESENTATION`（若把未定式重写成了可比较的形式），
也可以什么都不算（若只是机械求导）。

---

## 1. 最容易混淆的 8 组边界（实测高频误用）

### 1.1 `STATE_REREPRESENTATION` vs `RESTRICT_SLICE`

| | 判据 |
|---|---|
| `STATE_REREPRESENTATION` | **对象本身换了表示**。例：`C1-010` 多叉树 → 二叉链表（左孩子-右兄弟）；`C1-023` 线性数组 → 环（用取模）；`C1-002` "头指针为 NULL" → "头结点 next 为 NULL"。**换表示后，整个问题都在新表示下讨论。** |
| `RESTRICT_SLICE` | **对象不变，只把注意力限制到一个子集**。例：`C1-012` 把调整范围限制到"最小不平衡子树"；`M1-009` 按 x 的符号分片处理不等号方向；`M1-002` 按端点是否含奇点筛选选项。**切片之外的部分被暂时搁置，但没有被重新表示。** |

**分界问句**：切片之外的东西**还在不在问题里**？在 → `RESTRICT_SLICE`；不在（已被新表示吸收）→ `STATE_REREPRESENTATION`。

### 1.2 `AUXILIARY_OBJECT` vs `SPACE_AUGMENTATION`

| | 判据 |
|---|---|
| `AUXILIARY_OBJECT` | **引入一个具体的新对象来承载信息**。例：`C1-002` 头结点（使"第一个数据结点的前驱"恒存在）；`C1-004` 第二个工作指针（构造出"间距"）；`C1-009` ltag/rtag 标志；`C1-021` 大根堆作候选容器。 |
| `SPACE_AUGMENTATION` | **把常数变量化 / 往约束空间里补进一条新方程**，对象是"自由度"而非"实体"。例：`M1-001` 把 `x` 写成 `1/x` 再生成第二条方程。 |

**分界问句**：新东西是**一个可以指名的实体**，还是**一个新维度/新方程**？实体 → `AUXILIARY_OBJECT`；维度 → `SPACE_AUGMENTATION`。

### 1.3 `EXACT_ELIMINATION` vs `CONSTRAINT_COLLISION`

| | 判据 |
|---|---|
| `EXACT_ELIMINATION` | 多条约束**相容**，联立后能**精确消掉某个未知量**。 |
| `CONSTRAINT_COLLISION` | 两条约束**打架**（同时满足会导出矛盾），冲突本身就是信息。 |

**分界问句**：联立之后**是消掉了东西，还是撞出了矛盾**？

### 1.4 `PROBE` / `CRITICAL_SCALE_PROBE` / `COUNTEREXAMPLE_PROBE`

| 算子 | 探的是什么 |
|---|---|
| `PROBE` | 泛化的试探：代入特值、试算小规模、观察规律。**不预设要探什么。** |
| `CRITICAL_SCALE_PROBE` | **探尺度/临界参数**：数齐次次数、找主导项、定位分界参数。 |
| `COUNTEREXAMPLE_PROBE` | **探反例**：主动构造两条路径/两个取值来**否证**某个命题。 |

**分界问句**：试探的**目的**是找规律（`PROBE`）、定尺度（`CRITICAL_SCALE_PROBE`）、还是造反驳（`COUNTEREXAMPLE_PROBE`）？

### 1.5 `GLUE_LOCAL_TO_GLOBAL` vs `DEPENDENCY_ORDERING`

| | 判据 |
|---|---|
| `GLUE_LOCAL_TO_GLOBAL` | 把**局部结论拼成全局结论**。例：`C1-014` 局部插入/合并 → 全局性质。 |
| `DEPENDENCY_ORDERING` | 安排**处理顺序**使依赖成立。例：拓扑序、先算哪个后算哪个。 |

**分界问句**：你在**拼结论**，还是在**排顺序**？

### 1.6 `INVARIANT_BLOCK_DECOMPOSITION` vs `INFORMATION_AXIS_DECOMPOSITION`

| | 判据 |
|---|---|
| `INVARIANT_BLOCK_DECOMPOSITION` | 按**不变量**把对象切成互不耦合的块（如按特征子空间、按独立分量）。 |
| `INFORMATION_AXIS_DECOMPOSITION` | 按**信息维度**拆开（如把"位置"与"速度"分开看）。 |

两者实测样本都偏少（各 3–7 条），**边界证据不足**，判定时请谨慎并在 notes 说明理由。

### 1.7 `QUOTIENT_KERNEL` vs `NORMALIZE`

| | 判据 |
|---|---|
| `QUOTIENT_KERNEL` | 存在**对目标完全不可见的方向**，把它商掉。 |
| `NORMALIZE` | 存在**尺度冗余**，把它固定下来（如归一化、取单位向量）。 |

**分界问句**：被去掉的是**方向**（商）还是**大小**（归一）？

### 1.8 `RIGIDIFY` vs `RESTRICT_SLICE`

| | 判据 |
|---|---|
| `RIGIDIFY` | **给柔性对象加约束使它变刚**（如把不等式收紧成等式、把近似变成精确）。 |
| `RESTRICT_SLICE` | **只看一部分**，不改变对象性质。 |

---

## 2. 全部母算子定义（依据实测用法）

> `n=` 为实测出现次数（基于 179 条 Episode 的 `existing_operator_matches`）。
> **n 很小的算子，其定义属于推测，使用时请标注不确定性。**

| 算子 | 定义 | 实测 n |
|---|---|---:|
| `STATE_REREPRESENTATION` | 把问题对象**换成另一种表示**，使原本困难的操作变便宜或使隐藏结构显形。**判据：换表示后整个问题都在新表示下讨论。** | 79 |
| `RESTRICT_SLICE` | 把注意力**限制到一个子集/切片**上处理，其余暂时搁置。对象性质不变。 | 51 |
| `AUXILIARY_OBJECT` | **引入一个具体的新对象**承载信息或消除边界情形。 | 30 |
| `CRITICAL_SCALE_PROBE` | **探尺度**：数次数、找主导项、定位临界参数或平衡层。 | 25 |
| `GLUE_LOCAL_TO_GLOBAL` | 把**局部结论拼接成全局结论**。 | 20 |
| `BRIDGE_OBSERVABLE` | **把不可直接观测的量/性质，桥接到可直接观测或可直接计算的量上**，使抽象目标变成可检验的对象。例：把"是否决定工期"桥接到可计算的时间余量 `d(i)=l(i)-e(i)=0`；把"拓扑序唯一性"桥接到"每轮入度为 0 的顶点个数"。**注意：定义的核心是"可观测"，不是泛泛的"两个对象之间换算"。** | 20 |
| `EXACT_ELIMINATION` | 相容约束联立后**精确消掉**某个未知量。 | 17 |
| `DEPENDENCY_ORDERING` | 安排**处理顺序**使依赖关系成立。 | 17 |
| `COUNTEREXAMPLE_PROBE` | 主动**构造反例**来否证命题（常取两条路径/两个取值）。 | 15 |
| `SPACE_AUGMENTATION` | 把常数变量化，或**往约束空间补进新方程/新维度**。 | 14 |
| `INVARIANT_BLOCK_DECOMPOSITION` | 按**不变量**把对象切成互不耦合的块。 | 11 |
| `QUOTIENT_KERNEL` | 存在**对目标不可见的方向**，把它商掉。 | 11 |
| `CERTIFICATE_PRODUCTION` | 产出一个**可验证的凭据**（构造出对象、给出显式界、写出显式解）。 | 11 |
| `NORMALIZE` | 消除**尺度冗余**（归一化、取单位化）。 | 10 |
| `UNIFORMIZATION` | ⚠️ **实测是"兜底标签"，覆盖至少三种互不相同的机制，建议拆分或补定义。** 见下方 §2.1。 | 11 |
| `SELF_IMPROVING_CLOSURE` | 构造一个**自我改进/自我闭合**的过程（迭代收敛、逐步收紧）。 | 10 |
| `PROBE` | 泛化的试探（代入特值、试算小规模）。**不预设探什么。** | 10 |
| `CONSTRAINT_COLLISION` | 两条约束**打架**，冲突本身即信息。 | 9 |
| `DEFECT_CENTERING` | 把**缺陷/奇点**作为展开或分析的**中心**。 | 8 |
| `DEFECT_FACTORIZATION` | 把缺陷**按重数/类型分解**。 | 7 |
| `INFORMATION_PRESERVATION` | 有意识地**推迟有损操作**以保住信息。 | 7 |
| `DEPENDENCY_REORGANIZATION` | **重排依赖结构**本身（不只是处理顺序）。 | 6 |
| `RIGIDIFY` | **给柔性对象加约束使它变刚**。 | 6 |
| `LOW_BANDWIDTH_INTERFACE` | 用**低带宽接口**屏蔽内部复杂度。 | 5 |
| `INFORMATION_AXIS_DECOMPOSITION` | 按**信息维度**拆开分析。**边界证据不足。** | 4 |
| `INTERFACE_RENORMALIZATION` | 对**接口/边界条件**做重整化。**边界证据不足。** | 4 |
| `REPAIR_SCALE_MATCHING` | 通过**匹配尺度**来修补失效的近似或估计。**证据不足。** | 4 |
| `SHARED_WORLD_EMBEDDING` | 把多个主体**嵌入同一个世界/样本空间**以统一处理。**证据不足。** | 3 |
| `THICKNESS_EXTRACTION` | 提取**厚度/余量**类量（如把"至少差多少"显式化）。**证据不足。** | 2 |
| `FRONTIER_NAVIGATION` | 沿**边界/前沿**搜索。**证据不足。** | 2 |
| `ENVIRONMENT_REWEIGHTING` | 对**环境/权重**重新加权。**证据不足。** | 1 |
| `STRUCTURAL_PROGRESS` | 只表示"有结构进展"，**语义过泛，建议废弃或拆分**。**证据不足。** | 1 |

---

## 2.1 实测发现的两个"定义与用法不符"的算子

### `BRIDGE_OBSERVABLE` —— 我原先的定义太泛

**原定义**（错）："建立两个对象之间的换算桥梁，使关于 A 的已知信息可用于 B。"
这个说法丢了**标签名里的关键词：OBSERVABLE（可观测）**。

**实测 20 条的真正共同点**：把**不可直接观测**的量/性质，桥接到**可直接观测或可直接计算**的量上。
- `C1-019` — 把"是否决定工期"桥接到可计算的 `d(i)=l(i)-e(i)=0`
- `C1-020` — 把"拓扑序唯一性"桥接到"每轮入度为 0 的顶点个数"
- `C1-024` — 把"拓扑序"桥接到"DFS 结束时间"
- `M3-016` — 把不可观测的 `f` 内部取值桥接为可观测的函数值
- `M5-007` — 把几何可观测量翻译为分析表达式

**已修正定义**：见 §2 表格。**判据**：被桥接的一端必须是"原本不可直接观测/不可直接计算"的。

### `UNIFORMIZATION` —— 兜底标签，覆盖至少三种机制

实测 11 条里至少混了三种互不相同的动作：

| 机制 | 实例 |
|---|---|
| **A. 统一参数/尺度** | `M1-005` 用统一的尺度链一次性排序；`M3-012` 用统一参数 `t` 描述曲线；`M5-013` 换元后取得统一常系数形式 |
| **B. 对称性归并/平均化** | `M4-013` 用区域对称群把不对称被积函数"平均化"；`M4-016`/`M4-017` 轮换对称性把不对称量归并为对称量的倍数 |
| **C. 信息压缩到一点** | `M2-004` 把分散在三个点上的信息统一压缩成一点处的函数值 |

**而且有两条的 worker 自己就标注了这个标签不合适**：
- `M3-012` — "有统一化色彩，**但本题的关键是'识别为换元'而非'统一参数'**"
- `M3-014` — "有统一化色彩，**但核心是回到更一般原理**"

**这说明 `UNIFORMIZATION` 被当成了"说不清就放这儿"的筐。**

**处置建议**（交 Critic / 聚合阶段裁决）：
- 机制 B（对称性归并）应归 `STATE_REREPRESENTATION` 或单独立 `SYMMETRY_AVERAGING`；
- 机制 C（信息压缩到一点）应归 `DEPENDENCY_REORGANIZATION`；
- 机制 A 才真正是 `UNIFORMIZATION`；
- 若拆分后 A 的样本不足（<5），则该标签应**降级为描述性标签**。

**在使用该标签时**：请先判断自己属于 A/B/C 哪一类；若是 B 或 C，请改用对应的标签，
并在 `notes` 里说明"此处 `UNIFORMIZATION` 不适用，理由…"。这类冲突正是
`unexplained_cases.md` 要收录的东西。

---

## 3. Anti-operator 定义

> ⚠️ **实测：`BAD_REPRESENTATION_LOCK_IN` 也是兜底标签。**
> 它占全部 `naive_routes` 的 **23.4%（100/427）**，是头号 anti-operator。
> 但它的 100 次实际用法里，**绝大多数与"表示"无关，而是约束违反**：
>
> | 实例 | 实际是什么问题 |
> |---|---|
> | 从头遍历找前驱 | 违反 **O(1)** 复杂度要求 |
> | 先逆置链表再数第 k 个 | 违反 **"不改变链表"** 约束 |
> | 复制到数组 | 违反 **O(1) 空间** |
> | 加 prev/next 指针域 | **空间开销**问题 |
> | 为首部插入单独写 if 分支 | **没有抽象**，不是表示锁死 |
> | 只做过程性模拟 | **没找到离线判据** |
> | 用顺序循环队列 | **选错结构以迎合约束** |
> | 把哨兵计入表长 | **结构理解错误** |
>
> **八条实例、八种不同失败机制、同一个标签。**
>
> 这也修正了一个此前的观察：anti-operator 的 top3 只有 45.7%（vs 母算子 90.4%），
> 看起来"区分度更高"——**但那个分散是假象**，它只是因为标签更多（20 个）而分布更平。
> 头号标签照样吃掉 23.4%，且**字面定义与绝大多数用法脱节**。
>
> **使用建议**：标 `BAD_REPRESENTATION_LOCK_IN` 前先自问
> **"这条路线的问题真的是'锁死在错误表示里'吗？"**
> 若其实是违反约束（复杂度/空间/不改变结构），请改用更贴切的标签，
> 或标 `CANDIDATE_*` 并在 `notes` 说明。
> 证据：`_index/anti_operator_usage.md`（工具 `anti_operator_usage.py` 可复跑）。

| 标签 | 定义 |
|---|---|
| `PREMATURE_INFORMATION_LOSS` | 过早执行了不可逆的信息损失操作（该保留绝对值时去掉了、该保留符号时取了模）。 |
| `PREMATURE_ABSOLUTE_VALUE` | 为了便于估计而**过早取绝对值**，破坏正负相消。 |
| `PREMATURE_APPROXIMATION` | 在还没确定主导项时就做近似。 |
| `BAD_REPRESENTATION_LOCK_IN` | 锁死在一个不适用的表示里继续硬算。 |
| `OVER_DECOUPLING` | 把**本耦合**的对象强行分开处理。 |
| `MISSING_SHARED_WITNESS` | 多个子问题各自成立，但**证人不一致**，无法重新组合。 |
| `LOCAL_REPAIR_GLOBAL_ERROR` | 局部修补导致全局错误。 |
| `DEPTH_TUNNEL_VISION` | 在一条路上越挖越深，不回头看别的分支。 |
| `BRANCH_EXPLOSION` | 分支爆炸，没有剪枝。 |
| `TARGET_DRIFT` | 目标在过程中漂移，最后解的不是原题。 |
| `PROXY_OBJECTIVE_DRIFT` | 用代理目标替换了真目标。 |
| `SEARCH_EXHAUSTED_AS_REFUTED` | 搜索穷尽被当成了"已证伪"。 |
| `PROMISING_AS_PROVED` | 把"看起来有希望"当成了"已经证明"。 |
| `DEPENDENCY_CYCLE` | 依赖成环。 |
| `RECOMPUTE_WHOLE_FOR_LOCAL_CHANGE` | 局部改动却重算全体。 |
| `NEWTON_LEIBNIZ_BLIND_APPLICATION` | 凑出原函数后不检查其在区间上是否处处有定义/可导就代入上下限。（M3 提出） |
| `UNJUSTIFIED_SYMMETRY_TRANSFER` | 把有限对称区间的奇偶性结论无条件搬到反常积分。（M3 提出） |
| `MISSING_ABSOLUTE_VALUE` | **该取绝对值时反而去掉**——与 `PREMATURE_ABSOLUTE_VALUE` 成对的反方向失败。（M3 提出，已采纳） |

---

## 4. 本文件自身的局限

1. **定义是从用法反推的，不是先验正确的。** 若某个定义与你的判断冲突，
   **以题目结构为准**，并在 `notes` 里写明"该定义在此处不适用，理由是…"。
   这些冲突正是 `unexplained_cases.md` 要收录的东西。
2. **n < 5 的算子定义属于推测**（表中已标"证据不足"）。使用它们时请标注不确定性。
3. **`STRUCTURAL_PROGRESS` 语义过泛**（实测仅 1 次），建议在 Critic 阶段判定是否废弃。
4. 本文件**不改变** SPEC §7 的标签清单，只补充语义。
   若发现某个结构动作**在所有标签里都无格可填**，那应走 `CANDIDATE_NEW_OPERATOR`
   路径，而不是硬塞进最接近的标签——盲测预测者实测报告了**至少 3 处**这种情况。
