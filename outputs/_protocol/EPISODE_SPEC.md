# Problem Episode 抽取规范 v1.0

> 本文件是所有 worker 的唯一共同契约。动手前必须完整读完。
> 目标产物：`outputs/raw_episodes/<worker>.jsonl`（一题一行）+ `outputs/raw_episodes/<worker>.notes.md`

---

## 0. 唯一总原则

> **不要问"这题考什么知识点"，要问"这题为什么难，它是怎样被变成容易问题的"。**

本任务**不是**知识点整理，**不是**教材摘要，**不是**题型归纳。
本任务要把资料预处理成**问题解决轨迹样本库**，供后续主 Agent 检索：

```
问题形状 → 障碍诊断 → 触发信号 → 关键变形 → 新问题状态 → 后续动作
```

最终要能回答：**面对一个问题，人为什么会想到这样处理？**

---

## 1. 环境与路径

| 项 | 值 |
|---|---|
| 源仓库根（**只读**） | `E:\杂七杂八的垃圾堆\_dlp_src` |
| 输出目录 | `E:\杂七杂八的垃圾堆\LearningOS\outputs\` |
| 你的 Episode 文件 | `outputs\raw_episodes\<worker>.jsonl` |
| 你的笔记文件 | `outputs\raw_episodes\<worker>.notes.md` |

**禁止修改源仓库任何文件。** 只读。

`repo_path` 一律写**仓库相对路径**，用正斜杠，例如：
`讲义/高等数学/01_强化篇/第01讲_函数极限与连续.md`
不要写 `E:\...` 绝对路径。

---

## 2. 五条禁止事项（违反即报废）

### 禁止 1：知识点摘要
不要输出"第一章 极限 / 1. 极限定义 / 2. 洛必达法则"这类目录式结果。零价值。

### 禁止 2：题型分类作为组织方式
"题型一：求极限"不能当核心抽象。题型只能当检索辅助标签（放在 `notes` 里）。

### 禁止 3：看到答案后只做事后包装
不能写"本题用了 Taylor，因此属于换表征"。
必须尽量恢复：
- 题目**最初**暴露了什么结构？
- 为什么直接操作困难？
- 什么**信号**让 Taylor 成为自然动作？
- Taylor 以后**究竟改变了什么**？

### 禁止 4：为套算子而强行解释
无法自然解释的，标 `UNKNOWN` / `UNEXPLAINED`。**不要硬贴标签。这些样本反而最重要。**

### 禁止 5：把每一步都当"思想"
普通代数化简、机械求导、公式代入等**执行步骤**不升格为算子。
只提取**改变问题结构的步骤**。

---

## 3. 基本单位

一个 Episode = 一道**人类可识别的完整问题**。

- 一道大题含多个独立小问，且小问之间没有结构依赖 → 拆成多个 Episode。
- 小问依赖前问结论（"用(1)的结论证明(2)"）→ 保留为一个 Episode，在 `solution_skeleton` 里体现依赖。
- 若几道题共享同一问题结构，**先各自保留单题轨迹，再聚类**（聚类是后续独立 worker 的活，你不要替它做）。

---

## 4. 产量要求

- 目标：**15–22 条/worker**，全库 ≥200 条。
- **宁少勿滥。** 材料薄就少写，并在 notes.md 说明原因。
- 宁可 15 条真轨迹，不要 40 条"用了换元法"的垃圾标签。
- 优先选择：**有分析过程、有方法总结、有明确转折、有典型错误路线**的题。
- 纯记忆题（如"栈的特点是什么"）、纯计算题（如"求 3×4 矩阵的行列式"）→ 直接跳过，不要凑数。

---

## 5. 证据等级（每条抽象都要标）

| 等级 | 含义 |
|---|---|
| `E0` | worker 自己联想，材料无支持 |
| `E1` | 从单个答案事后推断 |
| `E2` | 单题分析文字**明确表现**这一思路（讲义 `分析`/`方法总结` 原话） |
| `E3` | 多道题反复出现同一 trigger → transition |
| `E4` | 不同章节/题型出现相同问题结构 |
| `E5` | 跨领域重复出现（高数+线代+概率，或数学+408） |

**E3 以上才值得进入稳定 ontology。** 你只负责 `E0`–`E2`（单 worker 视角）；
`E3`–`E5` 由后续聚合 worker 判定。**不要自己标 E3+。**

在 `notes` 里写：`evidence_level: E2`（该 Episode 最主要的证据等级）。

---

## 6. JSONL 记录 schema（字段必须齐全，不得改名）

```json
{
  "problem_id": "M1-001",
  "question_id": "ZY30-GS-01-L1.02",
  "source": {
    "repo_path": "讲义/高等数学/01_强化篇/第01讲_函数极限与连续.md",
    "section": "函数的概念与特性",
    "example_or_question": "例1.2",
    "year": null
  },
  "domain": "高等数学",
  "raw_problem": "",
  "problem_goal": "",
  "initial_state": {
    "objects": [],
    "constraints": [],
    "free_variables": [],
    "known_relations": [],
    "target_form": ""
  },
  "initial_geometry": {
    "representation_issue": "",
    "redundant_freedom": "",
    "coupling": "",
    "scale_competition": "",
    "dependency_structure": "",
    "information_risk": "",
    "state_transition_structure": "",
    "resource_or_bottleneck_structure": ""
  },
  "main_obstacle": "",
  "naive_routes": [
    { "route": "", "why_natural": "", "why_bad_or_expensive": "", "failure_type": "" }
  ],
  "trigger_signals": [],
  "key_transitions": [
    {
      "before_state": "",
      "operation": "",
      "after_state": "",
      "why_triggered": "",
      "preserved_information": "",
      "discarded_information": "",
      "new_structure_exposed": ""
    }
  ],
  "solution_skeleton": [],
  "certificate_or_closure": "",
  "anti_triggers": [],
  "transfer_candidates": [],
  "existing_operator_matches": [],
  "possible_new_operator": null,
  "confidence": "",
  "evidence_excerpt": "",
  "notes": ""
}
```

### 6.1 字段说明与质量要求

- **`problem_id`**：`<WORKER>-<三位序号>`，从 `001` 连续编号，不跳号。
- **`question_id`**：若原题带唯一编号（如 `M1-24-C-T01`、`WD-DS-C-1.1-T01`、`ZY30-GS-01-L1.02`），**必须填**；讲义例题无编号则填 `null`。
- **`raw_problem`**：题目原文。**保留 LaTeX**。OCR 乱码处用 `[OCR?]` 标注，不要静默改写。
- **`problem_goal`**：要得到什么（一句话）。
- **`initial_state.objects`**：问题里的对象（函数、矩阵、链表、进程、页面…）。
- **`initial_state.free_variables`**：还没定的自由度。
- **`initial_state.known_relations`**：已知约束/关系式。
- **`initial_state.target_form`**：目标以什么形式交付（数值？存在性？不等式？复杂度？）。
- **`initial_geometry`**：八个"问题几何"轴。**无则填 `""`，不要硬编。**
  - `representation_issue`：当前表示为什么不好用（如"函数以复合形式给出，自变量被遮蔽"）
  - `redundant_freedom`：有多少不影响目标的自由度
  - `coupling`：哪些量被绑在一起无法分开
  - `scale_competition`：是否有多尺度/多机制竞争（如 `x^4` 与 `y^2` 同趋零）
  - `dependency_structure`：量之间的依赖链/序
  - `information_risk`：哪些操作会不可逆地丢信息（如提前取绝对值）
  - `state_transition_structure`：是否本质是"状态+事件+转移"
  - `resource_or_bottleneck_structure`：资源/带宽/瓶颈结构（408 常用）
- **`main_obstacle`**：**最核心字段之一。**
  - ❌ 不要写"不会求极限"（这是能力描述，不是问题描述）
  - ✅ 要写"分子分母存在多个同阶机制，直接代换无法判断首次非零项"
  - ✅ 要写"两个子系统通过共享状态发生耦合，不能分别计算后直接相加"
- **`naive_routes`**：**至少 1 条**（材料能判断时）。
  - `route`：自然但差的做法
  - `why_natural`：为什么人第一反应会这么做
  - `why_bad_or_expensive`：代价/失效点
  - `failure_type`：填 anti-operator 标签（见 §8）
  - ❌ "直接分别估计两部分 → 过早取绝对值 → cancellation 被破坏" 这种要写出来
  - ✅ 这是后续 anti-trigger 的直接原料
- **`trigger_signals`**：**必须写成"看到什么就应该警觉什么"。**
  - ❌ "需要换元"
  - ✅ "递推式同时出现 `n a_n` 与 `(n+1)a_{n+1}` → shift 与 n-weight 同时存在 → 生成函数/微分编码可能自然出现"
  - ✅ "控制量对某些方向完全不变 → 查找 kernel / symmetry orbit → 不要直接估计"
  - ✅ 每条必须是**从题面可观察**的（Critic 会专门攻击这一点）
- **`key_transitions`**：**整个数据集最重要的部分。** 必须表示 `Before --Operation--> After`。
  - `before_state` / `after_state`：问题状态（不是算式快照，是"现在在问什么"）
  - `operation`：结构动作（用算子标签 + 一句话）
  - `why_triggered`：哪个 trigger 触发了它
  - `preserved_information`：保留了什么
  - `discarded_information`：丢掉了什么
  - `new_structure_exposed`：新暴露的结构（这是"之后为什么变容易"的答案）
  - 示例：
    ```
    Before:  研究 ff''+(f')^2 的零点数量
    Operation: 定义 F = f f'
    After:   问题变成研究 F' 的零点；目标可以通过制造 F 的多个零点后调用 Rolle
    ```
- **`solution_skeleton`**：字符串数组，只写**结构性步骤**，跳过机械计算。
- **`certificate_or_closure`**：这题靠什么"收口"（构造出对象？Rolle？归纳？矛盾？不变量？）
- **`anti_triggers`**：本题特有的"别这么干"警告。
- **`transfer_candidates`**：**结构迁移，不是"类似题也能用"。**
  - ❌ "类似题也能用"
  - ✅ "'控制量存在 kernel → 先 quotient' 可迁移到：Poincaré 减均值 / 线代 V/ker T / 齐次问题归一化"
- **`existing_operator_matches`**：数组，每项 `{"operator_id": "...", "is_primary_move": true/false, "why": "..."}`。
- **`possible_new_operator`**：`null` 或 `{"name": "CANDIDATE_...", "why_existing_fails": "...", "definition": "..."}`。
  - 用 `CANDIDATE_NEW_OPERATOR` 时**必须说明为什么现有标签解释不自然**。
- **`confidence`**：`high` / `medium` / `low` / `unknown`。
- **`evidence_excerpt`**：**从原文摘录**支撑你判断的句子（讲义 `分析`/`方法总结`/`注`/`考点及方法小结` 原话优先）。OCR 噪声照实摘。

  **⚠️ 硬性要求：必须是源文件中一段连续、逐字的原文。**
  以下做法**全部违规**（首轮实测 22 条里有 12 条犯了，占 55%）：
  - ❌ 用省略号把不相邻的两段拼起来：`"分析 ①可积不可求积… ②变限积分求导… 解应选(B)"`
  - ❌ 在摘录里插入自己的箭头/标注：`"分析 ∫_0^π xf(sinx)dx —难算→ 区间再现"`
  - ❌ 把多处原话重组、或把自己的总结写进去
  - ✅ 正确做法：**挑一段最强、最连续的原文**放进来（可以很长，也可以只截取一句），
    其余佐证放进 `notes`，并注明 `additional_evidence: <另一处原话或位置>`。

  自检方法：把你写的 `evidence_excerpt` 复制出来，到源文件里**搜一下**。
  搜不到 → 说明你改写或拼接了，必须换成一搜就中的连续原文。

  **⚠️ 高频错误：题目与推理依据不在同一个文件里。**
  实测已出现 3 次（M8-019、M6-002/004/006/007/008）。典型情形：
  - 题目来自 **`核心真题/`**，但支撑该思路的**方法说明在 `讲义/` 里**；
  - 题目在讲义的某一讲，但方法总结在**另一讲**。

  这时**不要**把别处的原文塞进 `evidence_excerpt`——那会让 `evidence_excerpt`
  与 `source.repo_path` 指向不同文件，回源核验必然失败。正确做法：

  1. **`evidence_excerpt` 只放 `source.repo_path` 所指文件内的连续原文**
     （若该文件里确实没有解释"为什么"的文字，就选一段最接近的，并在 notes 说明其局限）；
  2. **跨文件的推理依据**放到 `notes` 里，用
     `additional_evidence（逐字，<真实出处 repo_path> L<a>-L<b>）：<原文>`
     注明。**这段也必须逐字可回源核验。**

  **判据**：`evidence_excerpt` 必须能在 `source.repo_path` 里搜到。
  搜不到就是违规，不管那段话本身多么贴切。

  ### ⚠️ 关键区分：`evidence_excerpt` 的出处 ≠ `evidence_level` 的依据

  这两件事**必须分开**（M6 实测指出，我原先把它们混为一谈了）：

  | | 约束 | 为什么 |
  |---|---|---|
  | `evidence_excerpt` | **必须**出自 `source.repo_path` | 这是**可核验性**要求：摘录必须能被机器回源比对 |
  | `evidence_level` | 依据**整个仓库的材料**判断 | 这是**材料是否明说**的问题：E2 的定义是"材料明确陈述了该思路"，**没规定它必须在哪个文件里** |

  因此：

  - 若题目在真题、而讲义里**有**明确陈述该思路的原话（且已逐字记入 `additional_evidence`），
    则 `evidence_level` **仍可标 `E2`** —— 因为材料确实明说了，只是不在题目所在的那个文件里。
  - 只有当**整个仓库都找不到**明确陈述该思路的文字时，才降为 `E1`。
  - 无论标 E2 还是 E1，`evidence_excerpt` 都**必须**出自 `source.repo_path`。

  **错误做法**：因为"讲义原话不在所引文件里"就把 E2 降成 E1。
  这会把"材料明说"错误地记成"我自己推断"，**低估了证据强度**，方向与虚标 E2 相反但同样是失真。
- **`notes`**：补充。必须包含 `evidence_level: E?`。可放题型标签（辅助检索用）。

### 6.2 408 专属字段（C1–C4 worker 必须额外加）

在每条记录顶层增加：

```json
{
  "system_state": "",
  "resources": [],
  "agents_or_components": [],
  "invariants": [],
  "state_transition": [],
  "bottleneck": "",
  "local_vs_global_effect": "",
  "layer_interface": ""
}
```

408 中大量问题的核心不是静态对象，而是 **状态 + 事件 + 资源 + 不变量**。
- `state_transition`：`["就绪 → 运行（被调度）", ...]` 形式
- `local_vs_global_effect`：局部动作的全局后果（如"局部替换缺页 → 全局抖动"）
- `layer_interface`：跨层接口（如"虚拟地址 → TLB → 物理地址"）

---

## 7. 现有母算子标签（候选，**不允许强行匹配**）

> **⚠️ 动手前必读 [`OPERATOR_DEFINITIONS.md`](OPERATOR_DEFINITIONS.md)。**
>
> 本节只列**裸标签**，不含定义。实测后果（盲测预测者指出，已被独立验证）：
> 1. **同一道题被不同 worker 指派了不同标签**——`M1-16-A-T19` 被 M1/M2/M6 各立一条，
>    三个 worker 给出三套主算子。这很大程度不是"结构理解不同"，而是**没有共同定义**。
> 2. **盲测的 HIT/MISS 有一部分在测量命名约定**，而不是结构预测准确度。
>
> `OPERATOR_DEFINITIONS.md` 提供了：① 选标签的判定顺序；② **8 组最易混淆标签的边界**
> （附分界问句）；③ 全部算子的定义与实测出现次数；④ 哪些算子"证据不足、定义属推测"。
>
> **若某个结构动作在所有标签里都无格可填，请走 `CANDIDATE_NEW_OPERATOR` 路径，
> 不要硬塞进最接近的标签**——盲测预测者实测报告了至少 3 处这种情况。

```
STATE_REREPRESENTATION          FREEDOM_REORGANIZATION
QUOTIENT_KERNEL                 RESTRICT_SLICE
NORMALIZE                       SPACE_AUGMENTATION
AUXILIARY_OBJECT                DEPENDENCY_REORGANIZATION
LOW_BANDWIDTH_INTERFACE         INVARIANT_BLOCK_DECOMPOSITION
INFORMATION_AXIS_DECOMPOSITION  SHARED_WORLD_EMBEDDING
EXACT_ELIMINATION               INTERFACE_RENORMALIZATION
PROBE                           CRITICAL_SCALE_PROBE
COUNTEREXAMPLE_PROBE            RIGIDIFY
CERTIFICATE_PRODUCTION          BRIDGE_OBSERVABLE
CONSTRAINT_COLLISION            DEFECT_CENTERING
DEFECT_FACTORIZATION            UNIFORMIZATION
THICKNESS_EXTRACTION            SELF_IMPROVING_CLOSURE
ENVIRONMENT_REWEIGHTING         GLUE_LOCAL_TO_GLOBAL
INFORMATION_PRESERVATION        DEPENDENCY_ORDERING
REPAIR_SCALE_MATCHING           FRONTIER_NAVIGATION
STRUCTURAL_PROGRESS
```

允许创建 `CANDIDATE_NEW_OPERATOR`，但必须说明现有标签为何不自然。

---

## 8. Anti-operator 候选标签

```
PREMATURE_INFORMATION_LOSS      PREMATURE_ABSOLUTE_VALUE
PREMATURE_APPROXIMATION         BAD_REPRESENTATION_LOCK_IN
OVER_DECOUPLING                 MISSING_SHARED_WITNESS
LOCAL_REPAIR_GLOBAL_ERROR       DEPTH_TUNNEL_VISION
BRANCH_EXPLOSION                TARGET_DRIFT
PROXY_OBJECTIVE_DRIFT           SEARCH_EXHAUSTED_AS_REFUTED
PROMISING_AS_PROVED             DEPENDENCY_CYCLE
RECOMPUTE_WHOLE_FOR_LOCAL_CHANGE
```

同样允许新增（命名风格 `UPPER_SNAKE`）。

---

## 9. OCR 噪声处理规则

源资料是扫描 OCR 产物，公式常损坏（例：`$ecost$` 实为 `$e^{\cos t}$`；`2f(x)+x^2|f(1/x)/x|` 实为 `2f(x)+x^2f(1/x)`）。

规则：
1. **能从上下文无歧义恢复**的 → 恢复，并在 `notes` 记 `ocr_fixed: <原文片段>`。
2. **无法无歧义恢复**的 → 保留原文并标 `[OCR?]`，`confidence` 降级。
3. **绝不**根据"应该是什么"编造题目条件。题目条件错 → 整条轨迹报废。

---

## 10. 动手前的自检清单（每条 Episode 都要过）

- [ ] `main_obstacle` 描述的是**问题结构**，不是"学生不会"？
- [ ] 每条 `trigger_signals` 都是**从题面可观察**的，而不是从答案反推的？
- [ ] `key_transitions` 里 before/after **真的发生了结构变化**（不是同一句话换说法）？
- [ ] 每条 transition 都回答了**保留/丢掉了什么**？
- [ ] `naive_routes` 至少 1 条，且是**真的有人会走**的路？
- [ ] `transfer_candidates` 写的是**结构迁移**，不是"类似题也能用"？
- [ ] 没有把机械计算步骤升格成算子？
- [ ] 无法解释的地方**如实标了 UNKNOWN**，没有硬贴标签？
- [ ] `evidence_excerpt` 是**源文件里一段连续、逐字的原文**（没有 `…`、没有 `→`、没有你自己的标注）？
      自检：把它复制出来到源文件里搜一下，**搜不到就是违规**。
      （首轮实测：44 条里 35 条违规，占 80%——这是最常见的失分点。）
- [ ] `evidence_excerpt` 是**原文摘录**，不是自己写的？
- [ ] 记录里没有 `E3+` 自评？

---

## 11. 输出格式

### `<worker>.jsonl`
- UTF-8，**无 BOM**
- **一题一行**（一行一个完整 JSON 对象，不换行）
- 行尾 LF
- 不要包成数组，不要加 markdown 代码块围栏

### `<worker>.notes.md`
必含：
```markdown
# <worker> 抽取笔记

## 覆盖范围
| repo_path | 处理情况 | 产出 Episode 数 |

## 产出统计
- Episode 总数：
- confidence 分布：high/medium/low/unknown =
- evidence_level 分布：E0/E1/E2 =

## 未能处理的材料及原因

## UNKNOWN / UNEXPLAINED 清单
| problem_id | 现有最接近算子 | 为什么解释别扭 | 疑似缺失概念 |

## CANDIDATE_NEW_OPERATOR 候选
| 名称 | 触发场景 | 现有标签为何不够 | 出现题数 |

## 自检
- [ ] 已逐条过 §10 清单
- [ ] 源仓库未被修改
```

---

## 12. 已完成范例（照此深度写）

```json
{"problem_id":"M1-001","question_id":null,"source":{"repo_path":"讲义/高等数学/01_强化篇/第01讲_函数极限与连续.md","section":"函数的概念与特性","example_or_question":"例1.2","year":null},"domain":"高等数学","raw_problem":"设函数 f(x) 的定义域为 (0,+∞)，且满足 2f(x)+x^2 f(1/x)=(x^2+2x)/sqrt(1+x^2)，则 f(x)=____","problem_goal":"由含 f(x) 与 f(1/x) 的关系式解出 f(x) 的显式表达式","initial_state":{"objects":["未知函数 f","自变量 x","已知右端函数 g(x)"],"constraints":["定义域 (0,+∞)，x 与 1/x 都在域内"],"free_variables":["f 在 (0,+∞) 上的取值（无穷多自由度）"],"known_relations":["2f(x)+x^2 f(1/x)=g(x)，其中 g(x)=(x^2+2x)/sqrt(1+x^2)"],"target_form":"f(x) 的闭式表达式"},"initial_geometry":{"representation_issue":"关系式中同时出现 f(x) 与 f(1/x)，但 f 本身是待求对象；方程把两个未知量绑在一起","redundant_freedom":"f 的函数形式完全未定，自由度极大","coupling":"f(x) 与 f(1/x) 在同一方程中线性耦合","scale_competition":"","dependency_structure":"f(1/x) 的取值依赖 f 在 x 的倒数点上的值，形成自指","information_risk":"若把 f(1/x) 当作已知或近似，会不可逆地丢失关于 f 的信息","state_transition_structure":"","resource_or_bottleneck_structure":""},"main_obstacle":"只有一条关系式，却含两个未知对象 f(x) 与 f(1/x)；直接对 f(x) 做代数变形无法把它分离出来，方程欠定","naive_routes":[{"route":"直接对原式做代数变形，试图把 f(x) 解出来","why_natural":"目标是 f(x)，最直接的动作就是移项、通分、除系数","why_bad_or_expensive":"f(1/x) 不是常数而是另一个未知量，移项后得到 f(x)=[g(x)-x^2 f(1/x)]/2，右端仍含未知量，等于没解","failure_type":"BAD_REPRESENTATION_LOCK_IN"},{"route":"代入特殊值（如 x=1）试出 f(1)，再猜函数形式","why_natural":"只有一个方程时，试值是最省力的入口","why_bad_or_expensive":"x=1 时 1/x=x，方程退化为 3f(1)=g(1)，只能定一个点的值，无法定出整个函数","failure_type":"PREMATURE_APPROXIMATION"}],"trigger_signals":["关系式中 f(x) 与 f(1/x) 成对出现，且 x↦1/x 是自身为逆的对合映射（再作用一次回到 x）→ 说明该映射把方程映回自身 → 可以用它再生成一条独立方程","未知量个数(2) 等于可通过该对合生成的方程个数(2) → 方程组可闭","右端 g(x) 与 g(1/x) 形式不同，说明两条方程线性无关，能真正提供新信息"],"key_transitions":[{"before_state":"一个方程、两个未知对象 f(x) 与 f(1/x)，欠定，无法分离 f(x)","operation":"SPACE_AUGMENTATION + EXACT_ELIMINATION：把 x 写成 1/x，生成第二条方程；把 {f(x), f(1/x)} 当作线性方程组的两个未知量，联立消去 f(1/x)","after_state":"得到关于 f(x) 的线性方程组并解出唯一闭式 f(x)=x/sqrt(1+x^2)","why_triggered":"x↦1/x 是对合（involutive），把原关系式映回自身，因此再作用一次必然产生一条关于同一对未知量的新方程；未知量数恰为 2，方程组因此可闭","preserved_information":"f 在 (0,+∞) 上的全部信息——两条方程联合仍等价于原约束，没有近似或丢弃","discarded_information":"只消去了辅助未知量 f(1/x)，未丢失关于 f 的任何信息","new_structure_exposed":"'单个函数方程' 被重写为 '有限维线性方程组'，未知量从'整个函数'退化为'两个数'，问题从函数层面降到代数层面"}],"solution_skeleton":["识别关系式在 x↦1/x 下的对合不变性","将原式中的 x 替换为 1/x，得到第二条方程","将 f(x) 与 f(1/x) 视为两个未知量，联立线性消元","回代得到 f(x)=x/sqrt(1+x^2)"],"certificate_or_closure":"方程组的系数行列式非零（3≠0），保证 f(x) 被唯一确定；以'解出唯一闭式'收口","anti_triggers":["不要把 f(1/x) 当已知量或小量处理——它不是常数，是另一个未知量","不要只代入个别点（x=1）就宣称确定函数——点值无法定出函数"],"transfer_candidates":["'目标对象与它的对称像成对出现，且对称是自身的逆 → 再作用一次生成新方程' 可迁移到：递推式取倒数/取共轭后联立、函数方程 Cauchy 型求解、线代中 A 与 A^T 同时出现时转置取第二方程","'未知量数 = 可生成的独立方程数 → 方程组可闭' 是判断'还差什么'的通用计数信号"],"existing_operator_matches":[{"operator_id":"SPACE_AUGMENTATION","is_primary_move":true,"why":"核心动作是往约束空间里补进一条原本不显式存在的方程，把欠定系统变成可解系统"},{"operator_id":"EXACT_ELIMINATION","is_primary_move":false,"why":"消元是收尾动作，本身不改变问题结构，属于执行步骤"}],"possible_new_operator":null,"confidence":"high","evidence_excerpt":"分析 将x写成 1/x，找到方程组①，②，联立，消去 f(1/x) 即可. / 方法总结 用所给关系式，造出方程组，解出所需的量.","notes":"evidence_level: E2（讲义明确写出'造出方程组'这一思路）。题型标签：函数方程。原题 OCR 中右端被识别为 2f(x)+x^2|f(1/x)/x|，据'解'部分公式与'方法总结'可无歧义恢复为 2f(x)+x^2 f(1/x)；ocr_fixed: x^2|f(1/x)/x| → x^2 f(1/x)。"}
```

---

## 13. 写完后

1. 逐条过 §10 清单。
2. 写 `<worker>.notes.md`。
3. 用 `pwsh` 校验 JSONL 每行都是合法 JSON：
   ```powershell
   Get-Content outputs\raw_episodes\<worker>.jsonl -Encoding UTF8 | ForEach-Object { $_ | ConvertFrom-Json | Out-Null }; "OK"
   ```
4. 回报：Episode 数、confidence 分布、UNKNOWN 数、CANDIDATE_NEW_OPERATOR 数。
