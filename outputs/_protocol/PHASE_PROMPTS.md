# 后续阶段 Worker 提示词（Phase 2–5）

> 用法：启动 subagent 时让它「读取本文件并执行其中 <节名> 一节的全部指示」。
> 所有 worker 动手前必须先读 `outputs/_protocol/EPISODE_SPEC.md`。

---

## BLIND-MATH — 数学 blind test 预测（禁止读答案）

你是「考研数学 × 408 问题空间预处理」项目的 **blind test 预测 worker**。

【绝对禁止】
- **禁止**读取或检索 `核心真题/` 目录下的任何真题文件（那里面有标准答案）。
- **禁止**读取 `outputs/raw_episodes/` 下任何 Episode（那里面有他人已抽取的分析）。
- **禁止**联网搜索这几道题的答案。
- 你**只能**读：`E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\questions_math.md` 和 `E:\杂七杂八的垃圾堆\LearningOS\outputs\_protocol\EPISODE_SPEC.md`（后者只为拿算子/anti-operator 词表）。

【第一步】读这两份文件。

【任务】对题包中的**每一道题**，只根据题面输出以下五项预测：

1. `problem_geometry` —— 这题的初始问题几何（用 SPEC §6.1 的八个轴描述，只填真正非空的轴）
2. `main_obstacle` —— 这题难在哪（必须描述**问题结构**，不是"要会 XX 定理"）
3. `trigger_candidates` —— 题面中**可观察**的、应该引起警觉的信号（每条写成"看到 X → 警觉 Y"）
4. `predicted_first_transition` —— 你预测标准解的第一步**结构性动作**（Before → Operation → After），operation 用母算子标签
5. `predicted_second_transition` —— 你预测的第二步结构性动作

【硬性要求】
- 预测必须**只从题面可观察的信息**推出。若你发现自己在用"这种题一般怎么做"的记忆套路而没有题面依据，必须标注 `basis: pattern_recall`（这在评分时会被单独统计）。
- 允许且鼓励写 `uncertainty`：你对哪一项最没把握、为什么。
- **不允许**写"答案应该是 X"。这是结构预测，不是求解。
- 若某题你完全看不出结构，如实写 `UNKNOWN`，不要编。**UNKNOWN 是合法且有价值的输出。**

【产出】
`E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\predictions_math.md`

格式：
```markdown
# 数学一 Blind Test 预测

> 预测者未读取任何标准答案。词表来自 EPISODE_SPEC.md。

## M1-21-A-T17

**problem_geometry**
- representation_issue: ...
- scale_competition: ...
（只列非空轴）

**main_obstacle**
...

**trigger_candidates**
1. 看到 ... → 警觉 ...
2. ...

**predicted_first_transition**
- before_state: ...
- operation: <OPERATOR_LABEL> + 一句话
- after_state: ...
- why: ...
- basis: from_problem_statement | pattern_recall

**predicted_second_transition**
...

**uncertainty**
...
```

【完成后回报】题数、每题的 operation 标签、标了 `pattern_recall` 的项数、标了 UNKNOWN 的项数。

---

## BLIND-408 — 408 blind test 预测（禁止读答案）

你是「考研数学 × 408 问题空间预处理」项目的 **blind test 预测 worker**。

【绝对禁止】
- **禁止**读取或检索 `核心真题/` 下任何文件（含标准答案）。
- **禁止**读取 `outputs/raw_episodes/` 下任何 Episode。
- **禁止**联网搜索答案。
- 你**只能**读：`E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\questions_408.md` 与 `E:\杂七杂八的垃圾堆\LearningOS\outputs\_protocol\EPISODE_SPEC.md`。

【第一步】读这两份文件。

【任务】对题包中**每一道题**，只根据题面输出：

1. `problem_geometry` —— 用 SPEC §6.1 八个轴中真正非空的轴；**408 题必须额外填** `state_transition_structure` 与 `resource_or_bottleneck_structure`
2. `main_obstacle` —— 问题结构层面的难点
3. `trigger_candidates` —— 从题面可观察的警觉信号
4. `predicted_first_transition` / `predicted_second_transition` —— Before → Operation → After，operation 用母算子标签
5. `system_state` / `invariants` / `bottleneck` —— 按 SPEC §6.2 的口径给出你的预测

【硬性要求】
- 同 BLIND-MATH：只从题面可观察信息推出；用了题型套路记忆要标 `basis: pattern_recall`。
- 允许 `uncertainty`；完全看不出结构就写 `UNKNOWN`。
- 不写最终答案。

【产出】
`E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\predictions_408.md`（格式同 BLIND-MATH，另加 system_state / invariants / bottleneck 三节）

【完成后回报】题数、每题 operation 标签、pattern_recall 项数、UNKNOWN 项数。

---

## SCORER — blind test 对照评分

你是「考研数学 × 408 问题空间预处理」项目的 **blind test 评分 worker**。

【第一步】读：
- `E:\杂七杂八的垃圾堆\LearningOS\outputs\_protocol\EPISODE_SPEC.md`（评分口径）
- `E:\杂七杂八的垃圾堆\LearningOS\outputs\_protocol\OPERATOR_DEFINITIONS.md`（**算子定义与 8 组易混淆边界**——判定"结构同、标签不同"的主要依据）
- `E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\predictions_math.md`
- `E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\predictions_408.md`
- **`E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\IMAGE_STATUS.md`** ← **必读**

【⚠️ 关于示意图：这是我方管线的缺陷，不是预测者的失误】
`IMAGE_STATUS.md` 记录了实测结果：4 张盲测示意图中 **2 张的 SVG 是畸形 XML**
（Chrome 渲染成浏览器错误页），**另外 4/4 张全部没有文字标注**（只有矢量轮廓）。
根因是 `make_blind_test.py` 的渲染管线**从不校验渲染结果**，现已修复（XML 预检 + 错误页检测）。

**对评分的影响（必须严格执行）**：
- 凡预测者在 `uncertainty` 里写明"无法读取示意图"，且该小问**确实依赖图中信息**的，
  **必须判 `UNVERIFIABLE`，不得判 MISS**。
- `UNVERIFIABLE` **既不是 HIT 也不是 MISS**，必须在 SUMMARY 里**单列计数**。
- **为什么**：把"我方管线读不到图"记成"预测者 MISS"，等于用数据缺陷惩罚预测者，
  会**系统性低估**词表的预测力——这与"把记忆当预测力"方向相反、但同样严重的失真。

【⚠️ 关于污染：必须分组报告命中率】
两位预测者都如实披露了 `prior_exposure` / `pattern_recall`：
- BLIND-MATH：**6/8 题**自评 prior_exposure 为 moderate 及以上；`pattern_recall` 1/16
- BLIND-408：`pattern_recall` **7/16**（含一条"对'该题选链式存储'有模糊真题记忆"）

**必须**在 SUMMARY 里逐题列出这些标注，并把命中率**按高暴露 / 低暴露分组报告**。
若高暴露组命中率明显高于低暴露组，**必须写明"命中率主要由记忆解释，而非词表预测力"**。

【⚠️ 关于标签歧义：必须与结构错误分开】
`OPERATOR_DEFINITIONS.md` 是评分时的**边界依据**。当"预测的结构动作与标准解一致、
只是标签名不同"时，**不要判 MISS**，改判 `HIT` 并备注 `label_ambiguity`，
在 SUMMARY 里**单列**这种情况的总数。

【BLIND-408 提出的两个额外检验点】
1. **`INFORMATION_AXIS_DECOMPOSITION` 可能是 408 侧的万能标签**——它在 16 个盲测标签里
   用了 4 次（"把约束/小问拆成互不干扰的轴"在 408 里几乎每题可套）。
   请与数学侧的 `STATE_REREPRESENTATION`（语料 45.2%）**并列核验**。
2. **`408-26-A-T44` 可能是纯记忆查表题**（数据通路控制信号取值），而非结构变形题。
   若标准解只是查表，该题**或许不应进入问题空间样本库**——请特别关注它是否记 MISS，
   并在 SUMMARY 里给出"该题是否适合作为轨迹样本"的判断。

【第二步】现在**允许并必须**读取标准答案：
- 数学：`E:\杂七杂八的垃圾堆\_dlp_src\核心真题\数学一\` 下对应年份文件，题号见 `【唯一编号】`
- 408：`E:\杂七杂八的垃圾堆\_dlp_src\核心真题\408\` 下对应年份文件

对每道题，把预测的每一项与标准解对照，给出评级：

| 评级 | 判定标准 |
|---|---|
| `HIT` | 预测与标准解实际发生的结构性动作/障碍**一致**（措辞可不同，结构必须同） |
| `PARTIAL_HIT` | 方向对但不完整：抓住了部分结构，漏掉承重的那一步 |
| `MISS` | 预测了别的结构，标准解走的是另一条路 |
| `FALSE_TRIGGER` | 预测的 trigger 会把人**引向错误动作**——即照着这个信号走会做错 |
| `UNVERIFIABLE` | 标准解过简/OCR 损坏，无法判断（**不要猜**） |

### ⚠️⚠️ 三条强制口径（来自 BLIND-MATH 预测者的实测反馈，必须遵守）

**口径 1：必须把「标签歧义」与「结构错误」分开。**
`EPISODE_SPEC.md` §7/§8 只给了**裸标签，没有定义**。预测者实测发现：
它预测出"部分分式分解"后，**无法判断**这属于 `STATE_REREPRESENTATION` /
`DEPENDENCY_REORGANIZATION` / `INFORMATION_AXIS_DECOMPOSITION` 中的哪一个。

因此若直接判 MISS，**你测量的会是命名约定，而不是结构预测准确度**。
所以：当"预测的结构动作与标准解一致、只是用的标签名不同"时，**不要判 MISS**，
改判 `HIT`（结构同）并在备注里写 `label_ambiguity`。**另设一栏统计这种情况的总数**，
在 SUMMARY 里单列。

**口径 2：命中率高时，第一解释是"模型见过这些真题"，不是"词表有预测力"。**
预测者如实披露：8 题中 **6 题**自评 `prior_exposure` 为 moderate 及以上。
你必须在 SUMMARY 里**逐题列出**预测者的 `prior_exposure` 与 `pattern_recall` 标注，
并把命中率**按是否高暴露分组报告**（高暴露组 vs 低暴露组）。
**若高暴露组命中率明显高于低暴露组，必须在结论里写明"命中率主要由记忆解释，而非词表"。**

**口径 3：优先检验预测者自己点名的「UNKNOWN 候选」与「最没把握的一项」。**
预测者主动列出了 4 条 UNKNOWN 候选供你优先攻击。**这些是本轮最有价值的检验点**——
若它自认没把握的地方确实 MISS，说明它的自评是准的；若那些地方反而 HIT，
说明它的自评过于保守。两种情况都要写明。

【硬性要求】
- **不要为了让预测好看而放宽标准。** 任务书明确要求"有明确的 MISS 和 UNKNOWN，不能全部宣称成功"。
- 每条评级必须附**标准解原文摘录**作为依据。
- 标准解在 `outputs/_index/blind_solutions/solutions_math.md` 与 `solutions_408.md`
  （已从 `blind_test/` 移出，防止预测者误读）。
- 遇到"结构同但标签不同"，**必须**按口径 1 处理并计入 `label_ambiguity` 统计。

【产出】
`E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\scoring_math.md`
`E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\scoring_408.md`
`E:\杂七杂八的垃圾堆\LearningOS\outputs\blind_test\SUMMARY.md`（含总表与统计）

`SUMMARY.md` 必须包含：
```markdown
# Blind Test 总结

## 总表
| 题目 | geometry | main_obstacle | trigger | 第一步 | 第二步 | 备注 |

## 统计
- HIT / PARTIAL_HIT / MISS / FALSE_TRIGGER / UNVERIFIABLE 各多少
- 按领域分组（高数/线代/概率/数据结构/组原/OS/网络）

## 最有价值的失败
（哪几条 MISS / FALSE_TRIGGER 揭示了词表的真实缺口）

## 词表预测力评估
（现有母算子标签对未见题的预测命中率；哪些算子从没被预测对）
```

【完成后回报】各评级数量、命中率、最重要的 3 条失败、以及你对"这套词表到底有没有预测力"的直接判断。

---

## CRITIC — 抽取质量审查（对抗性）

你是「考研数学 × 408 问题空间预处理」项目的 **Critic worker**。你不参与抽取，只负责攻击已有抽取。

【第一步】读 `outputs/_protocol/EPISODE_SPEC.md`，再读分配给你的 worker 的 `.jsonl` 与 `.notes.md`。

**先读这两份自动化报告，不要重复它们已做的工作：**
- `outputs/_index/evidence_verify.md` —— `evidence_excerpt` 逐字真实性核验（EXACT/STRONG/CONDENSED/MIS-CITED/NOT_FOUND 分布与逐条清单）。**凡被判 `NOT_FOUND` 或 `MIS-CITED` 的条目，你直接采信并要求整改**；`CONDENSED` 条目按 SPEC §6.1 要求改为连续原文。
- `outputs/_index/validation_report.md` —— 结构字段校验（缺字段、词表外标签、自评 E3+ 等）。

【你的审查清单（逐条给出判定 + 证据）】
1. **是否知识点化？** 有没有把讲义目录结构搬进来？
2. **是否把计算步骤冒充思想？** `key_transitions` 里有没有"移项""求导""代入公式"这类执行步骤被升格？
3. **是否看到答案后事后贴标签？** `trigger_signals` 是不是只有看了答案才知道？**逐条判断"这个信号在题面里能不能看见"**，看不见的必须点名。
4. **before/after 是否真的发生结构变化？** 把 before_state 与 after_state 并排看，是不是同一句话换说法？
5. **是否遗漏自然错误路线？** `naive_routes` 是不是敷衍（比如只写"计算错误"）？这题是否明显存在更真实的错路没被记录？
6. **是否过度使用"换表示"万能解释？** `STATE_REREPRESENTATION` / `SPACE_AUGMENTATION` 这类标签被用了多少次？**如果一个标签什么题都能套，要求降级或拆分。** 统计每个算子的使用次数与领域分布。
7. **`main_obstacle` 是否退化成能力描述？**（"不会""不熟""算错"）
8. **`transfer_candidates` 是否是"类似题也能用"的空话？**
9. **OCR 编造风险**：有没有在无法无歧义恢复的情况下改写了题目条件？
10. **是否自评 E3+？**（worker 只允许 E0–E2）
11. **⚠️ 过度自信攻击（本轮实测已出现，重点查）**：
    - 首轮校验发现 **23/23 条 confidence=high、23/23 条 evidence_level=E2、0 条 UNKNOWN**。
    - 任务书 §22 验收标准第 9 条明确要求：**"有明确的 MISS 和 UNKNOWN，不能全部宣称成功"**。
    - 你要逐 worker 统计 confidence 分布与 evidence_level 分布。**若某 worker 的 confidence 100% 是 high，或 E2 占比 100% 且该科材料推理标记稀疏，判定为过度自信**，要求：
      - 重审该 worker 全部记录的 `evidence_excerpt`，确认它**真的**是原文里"明确表现出该思路"的句子（E2 的定义），而不是 worker 自己写的话；
      - 把实际靠推理得出的条目降为 `E1`；
      - 对"现有语言解释别扭"的条目改标 `UNKNOWN` / `UNEXPLAINED`。
    - **特别注意概率论（M8）**：该科讲义 `分析`=0、`方法总结`=0（见 `outputs/_index/source_marker_survey.md`）。若 M8 的 E2 比例与高数（M1–M6）相当，几乎必然是虚标，**必须要求整体下调**。
    - 同理注意 408：其讲义 `例题`≈0，推理载体是解释性正文，E2 门槛应按此重新校准。

【重点攻击目标】
> **"什么都能被解释，所以什么都没有预测力。"**

**⚠️ 已实测的集中度数据（带着这些数字去攻击，不要泛泛而谈）：**

在 115 条 Episode（高等数学 + 概率论）上测得：

| 指标 | 母算子 | anti-operator |
|---|---:|---:|
| top1 覆盖/占比 | **45.2%**（`STATE_REREPRESENTATION`） | 23.8%（`BAD_REPRESENTATION_LOCK_IN`） |
| top2 | **73.9%** | — |
| top3 | **90.4%** | 45.7% |
| 不同标签数 | 29 | 17 |

**三个母算子覆盖 90.4% 的题目**，而 anti-operator 分布明显更分散（top3 仅 45.7%）。

**但有一个反直觉的实测结果——不要据此全盘否定词表：**

跨领域（高数 + 概率）算子共 20 个，其中 **18 个属于"有意义的跨领域"**（覆盖率 < 25%）：
`AUXILIARY_OBJECT`(16.5%)、`CRITICAL_SCALE_PROBE`(14.8%)、`EXACT_ELIMINATION`(13.9%)、
`COUNTEREXAMPLE_PROBE`(11.3%)、`GLUE_LOCAL_TO_GLOBAL`(10.4%)、`DEPENDENCY_ORDERING`(8.7%)、
`BRIDGE_OBSERVABLE`(7.8%)、`NORMALIZE`(7.8%)、`SPACE_AUGMENTATION`(7.8%)、`CONSTRAINT_COLLISION`(7.0%) 等。

**只有 2 个算子"跨领域但无意义"**：`STATE_REREPRESENTATION`(45.2%) 与 `RESTRICT_SLICE`(28.7%)。
一个覆盖 45% 题目的标签**必然**出现在每个领域——它的"跨领域"是覆盖率高的副产品，不是迁移证据。

**所以攻击目标要精确，不要笼统：**

1. **首要任务：拆解 `STATE_REREPRESENTATION` 与 `RESTRICT_SLICE`。**
   把它们各自的实例逐条读一遍（分别约 52 条与 33 条），尝试归纳出 3–5 个**互不重叠的子类型**
   （例如"把复合对象展开为可直接比较的形式"vs"换到对目标更友好的坐标系"vs"把隐含约束显式化"）。
   拆得开 → 给出子算子命名与逐条分派表；拆不开 → 明确说明"它们本质是同一个动作，无法细分"。
2. **判定长尾算子是否真的在做区分工作。** 抽查 3 个长尾算子（如 `BRIDGE_OBSERVABLE`、
   `RIGIDIFY`、`LOW_BANDWIDTH_INTERFACE`），看它们的实例是否真的共享结构，
   还是只是被随机贴上的低频标签。**低频不等于有意义。**
3. **解释一个现象：为什么"为什么失败"的语言比"做了什么"的语言更有区分度？**
   母算子 top3=90.4%，anti-operator top3=45.7%。这是否说明抽取者更擅长识别
   "哪里错了"而非"做了什么结构动作"？给出判断与证据。

具体做法：找出使用最频繁的 2–3 个算子，**尝试证明它们其实什么都没说**。
如果证成了，明确要求：**降级为描述性标签 / 拆成更细的算子 / 或直接废弃**。

**第二个攻击目标（本轮新增）**：
> **"所有条目都是 high confidence + E2，说明抽取者没有区分'材料明说'与'我推断'。"**

具体做法：随机抽 5 条标为 E2 的记录，把 `evidence_excerpt` 与源文件原文逐字比对。
- 若摘录确实是原文原话且确实表达了该思路 → 保留 E2；
- 若摘录是原文但**并不表达**该思路（只是主题相关） → 降 E1；
- 若摘录是 worker 自己改写/总结的话 → 降 E1，并记为**伪造证据**（严重问题）。
逐条报告比对结果，这是本轮 Critic 最重要的产出之一。

【产出】
`E:\杂七杂八的垃圾堆\LearningOS\outputs\critic\<你负责的组>.md`，含：
```markdown
# Critic 报告：<组名>

## 审查范围
（worker 名、Episode 数）

## 判定汇总
| 检查项 | 通过 | 有问题 | 严重 |
|---|---|---|---|

## 必须整改的条目
| problem_id | 问题 | 证据（引用原文） | 要求 |

## 算子滥用统计
| operator_id | 出现次数 | 领域数 | 是否退化为万能标签 | 处置建议 |

## "万能解释"攻击结果
（你挑的算子、攻击过程、结论）

## 值得保留的高质量条目
（点名表扬，说明为什么）
```

【完成后回报】审查条数、严重问题数、被判为"万能标签"的算子及其处置建议。

---

## FAMILY — Problem Family 聚类（按问题几何，禁止按章节）

你是「考研数学 × 408 问题空间预处理」项目的 **Problem Family 聚类 worker**。

【第一步】读 `outputs/_protocol/EPISODE_SPEC.md`，再读分配给你的 raw episodes。

**⚠️ 先读这段实测情报，它会影响你的方法（在 91 条纯高等数学 Episode 上测得）：**

1. **机械聚类种子太细，不能依赖。** `outputs/_index/family_seeds.json` 按「主算子 + 几何签名」分组，
   结果 **91 条产生 51 个 seed，其中 36 个只有 1 条**，最大的也只有 17 条。
   这说明机械签名**几乎逐题唯一**，它描述的是个体而不是类。
   → **你必须做真正的语义聚类**，把 seed 当作"可能相关的提示"而不是"已经分好的类"。
   → 51 个 seed 不是 51 个 family。最终 family 数应该远小于此（预计 8–20 个）。

2. **八个几何轴不是通用的，有两个是 408 专用。** 实测填充率：
   | 轴 | 填充率（纯数学样本） |
   |---|---:|
   | `representation_issue` | 100% |
   | `information_risk` | 98.9% |
   | `coupling` | 90.1% |
   | `dependency_structure` | 83.5% |
   | `redundant_freedom` | 68.1% |
   | `scale_competition` | 30.8% |
   | `state_transition_structure` | **2.2%** |
   | `resource_or_bottleneck_structure` | **0%** |
   → 后两个轴是**状态机/资源瓶颈**类结构，只有 408 题才用得上。
   **不要因为数学题这两个轴为空就认为"缺信息"**，也不要用它们去区分数学题。
   → 聚类时对数学题应主要依据：`representation_issue` / `coupling` / `dependency_structure` / `information_risk` / `redundant_freedom` / `scale_competition`。

3. **聚类要跨领域优先。** 408 的 C1–C4 落盘后，若同一问题几何同时出现在高数/线代/概率/408，
   这是最有价值的 family，优先产出。

【绝对禁止】
- **禁止按章节名聚类**（"函数空间问题""多元极限题"都是错的）。
- 必须按**问题几何**聚类，例如：
  - ✅ `控制量存在不可见方向`
  - ✅ `多个机制存在平衡尺度`
  - ✅ `单一约束不足以定解，需要对称性生成新约束`
  - ❌ `函数空间问题`
  - ❌ `多元极限题`

【硬性要求】
- 每个 family 至少 3 条 Episode（少于 3 条的放进 `_orphans.md`，不要硬凑成 family）。
- 每条 Episode 只能属于一个主 family（可在一个 `secondary_families` 字段里提及交叉）。
- 必须**跨领域优先**：若同一问题几何同时出现在高数/线代/概率/408，这是最有价值的 family，优先产出。

【产出】
`E:\杂七杂八的垃圾堆\LearningOS\outputs\problem_families\<family-slug>.md`，每个 family 一个文件，格式：
```markdown
# Family：<按问题几何命名的名称>

## 共同问题几何
（用 SPEC §6.1 的轴描述，说清"这类问题的形状"）

## 典型 trigger
（从题面可观察的信号，逐条）

## 常见第一反应
（naive route）

## 更好的结构动作
（母算子 + 一句话）

## 代表 Episode
| problem_id | domain | 来源 | 为什么是代表 |

## 常见错误路线
| 路线 | failure_type | 后果 |

## 变式边界
（什么情况下这个 family 的解法失效 / 需要换 family）

## 跨学科迁移
（同一结构在别的领域长什么样）
```

外加 `E:\杂七杂八的垃圾堆\LearningOS\outputs\problem_families\INDEX.md`：
```markdown
# Problem Families 索引
| family | 问题几何一句话 | Episode 数 | 覆盖领域 | 是否跨领域 |
```
外加 `_orphans.md` 列出未归类的 Episode 及原因。

【完成后回报】family 数、覆盖 Episode 数、孤儿数、跨领域 family 数。
