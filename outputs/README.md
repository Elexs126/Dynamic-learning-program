# 考研数学 × 408 问题解决轨迹数据集

> **Problem-Solving Trajectory Dataset** — 从 `Elexs126/Dynamic-learning-program` 的讲义、核心真题、配套习题中预处理出的**问题轨迹样本库**。

---

## 0. 这个数据集不是什麼

**不是**知识点整理，**不是**教材摘要，**不是**题型归纳，**不是**重新编写的考研笔记。

以上四类产物对本项目基本无价值，抽取规范里已明令禁止（见 `_protocol/EPISODE_SPEC.md` §2）。

## 1. 这个数据集是什么

唯一总原则：

> **不要问"这题考什么知识点"，要问"这题为什么难，它是怎样被变成容易问题的"。**

数据集把每道题表示成一条**问题解决轨迹**：

```
问题形状 → 障碍诊断 → 触发信号 → 关键变形 → 新问题状态 → 后续动作
```

最终要能回答：**面对一个问题，人为什么会想到这样处理？**

---

## 2. 交付物结构

```
outputs/
├── raw_episodes/                    # 第一级产物：问题轨迹（一题一行 JSONL）
│   ├── M1.jsonl … M8.jsonl          # 数学：高数/线代/概率
│   ├── C1.jsonl … C4.jsonl          # 408：数据结构/组原/OS/网络
│   └── <worker>.notes.md            # 每个 worker 的抽取笔记（覆盖范围、UNKNOWN、候选新算子）
├── problem_families/                # 第二级产物：按问题几何聚类
├── trigger_index.json               # 第三级产物：触发信号索引（主 Agent 最常调用）
├── anti_trigger_index.json          # 第四级产物：反触发索引（自然但差的路线）
├── operator_evidence_matrix.csv     # 第五级产物：算子证据矩阵（判断算子是否跨领域）
├── unexplained_cases.md             # 第六级产物：现有语言解释不自然的案例
├── blind_test/                      # 预测力验证（禁读答案的盲测 + 对照评分）
├── coverage_report.md               # 覆盖边界与空白
├── MANIFEST.json                    # 文件清单 + SHA256
├── README.md                        # 本文件
├── _protocol/                       # 抽取契约与工具（可复跑）
│   ├── EPISODE_SPEC.md              # ★ 抽取规范（schema / 禁令 / 证据等级 / 词表）
│   ├── WORKER_ASSIGNMENTS.md        # 各 worker 的材料范围
│   ├── WORKER_PROMPTS_408.md        # 408 组提示词
│   ├── PHASE_PROMPTS.md             # Critic / Family / Blind 提示词
│   ├── PHASE5_PROMPTS.md            # 索引 / 未解释案例 / 覆盖报告提示词
│   └── tools/                       # 全部可复跑脚本
└── _index/                          # 支撑产物（题目清单、大纲映射、校验报告等）
```

---

## 3. 一条 Episode 长什么样

完整 schema 见 `_protocol/EPISODE_SPEC.md` §6。**最重要的五个字段**：

### A. `main_obstacle` — 这题难在哪
描述**问题结构**，不是能力描述。

- ❌ `不会求极限`
- ✅ `分子分母存在多个同阶机制，直接代换无法判断首次非零项`
- ✅ `两个子系统通过共享状态发生耦合，不能分别计算后直接相加`

### B. `trigger_signals` — 看到什么应该警觉什么
必须是**从题面可观察**的，不是从答案反推的。

- ❌ `需要换元`
- ✅ `递推式同时出现 n·aₙ 与 (n+1)·aₙ₊₁ → shift 与 n-weight 同时存在 → 生成函数/微分编码可能自然出现`

### C. `key_transitions` — 数据集最重要的部分
必须表示 `Before --Operation--> After`，并写明**保留了什么、丢掉了什么、新暴露了什么结构**。

```
Before:    研究 f·f'' + (f')² 的零点数量
Operation: 定义 F = f·f'
After:     问题变成研究 F' 的零点；可制造 F 的多个零点后调用 Rolle
```

### D. `naive_routes` — 自然但差的方向
至少一条**真的有人会走**的错路，附 `failure_type`（anti-operator 标签）。这是 anti-trigger 索引的直接原料。

### E. `transfer_candidates` — 结构迁移
- ❌ `类似题也能用`
- ✅ `"控制量存在 kernel → 先 quotient" 可迁移到：Poincaré 减均值 / 线代 V/ker T / 齐次问题归一化`

---

## 4. 证据等级

每条抽象标注等级（`notes` 里的 `evidence_level:` 字段）：

| 等级 | 含义 |
|---|---|
| `E0` | worker 自己联想，材料无支持 |
| `E1` | 从单个答案事后推断 |
| `E2` | 单题分析文字**明确表现**这一思路（原文原话） |
| `E3` | 多道题反复出现同一 trigger → transition |
| `E4` | 不同章节/题型出现相同问题结构 |
| `E5` | 跨领域重复出现（高数+线代+概率，或数学+408） |

**worker 只允许自评 `E0`–`E2`**；`E3`–`E5` 由聚合脚本按机械规则推导（见 `_index/operator_stats.json` 的 `derived_evidence_level`）：

```
n_domains >= 2                              -> E5
n_distinct_sections >= 2 且 n_episodes >= 2 -> E4
n_episodes >= 2                             -> E3
n_episodes == 1                             -> E1
```

**只有 E3 以上才值得进入稳定 ontology。**

---

## 5. 词表

### 母算子（32 个候选标签）
```
STATE_REREPRESENTATION   FREEDOM_REORGANIZATION   QUOTIENT_KERNEL
RESTRICT_SLICE           NORMALIZE                SPACE_AUGMENTATION
AUXILIARY_OBJECT         DEPENDENCY_REORGANIZATION
LOW_BANDWIDTH_INTERFACE  INVARIANT_BLOCK_DECOMPOSITION
INFORMATION_AXIS_DECOMPOSITION  SHARED_WORLD_EMBEDDING
EXACT_ELIMINATION        INTERFACE_RENORMALIZATION
PROBE                    CRITICAL_SCALE_PROBE     COUNTEREXAMPLE_PROBE
RIGIDIFY                 CERTIFICATE_PRODUCTION   BRIDGE_OBSERVABLE
CONSTRAINT_COLLISION     DEFECT_CENTERING         DEFECT_FACTORIZATION
UNIFORMIZATION           THICKNESS_EXTRACTION     SELF_IMPROVING_CLOSURE
ENVIRONMENT_REWEIGHTING  GLUE_LOCAL_TO_GLOBAL     INFORMATION_PRESERVATION
DEPENDENCY_ORDERING      REPAIR_SCALE_MATCHING    FRONTIER_NAVIGATION
STRUCTURAL_PROGRESS
```

### Anti-operator（15 个候选标签）
```
PREMATURE_INFORMATION_LOSS   PREMATURE_ABSOLUTE_VALUE   PREMATURE_APPROXIMATION
BAD_REPRESENTATION_LOCK_IN   OVER_DECOUPLING            MISSING_SHARED_WITNESS
LOCAL_REPAIR_GLOBAL_ERROR    DEPTH_TUNNEL_VISION        BRANCH_EXPLOSION
TARGET_DRIFT                 PROXY_OBJECTIVE_DRIFT      SEARCH_EXHAUSTED_AS_REFUTED
PROMISING_AS_PROVED          DEPENDENCY_CYCLE
RECOMPUTE_WHOLE_FOR_LOCAL_CHANGE
```

worker 可以创建 `CANDIDATE_NEW_OPERATOR`，但**必须说明现有标签为何解释不自然**。所有候选汇总在 `unexplained_cases.md` 与各 `notes.md` 里。

---

## 6. 怎么用（主 Agent 检索工作流）

这是本数据集存在的意义：**让主 Agent 不再翻整章讲义，而是直接检索轨迹。**

### 典型检索路径

```
1. 手上有一道新题
   ↓
2. 提取它的「问题几何」（8 个轴，见 SPEC §6.1）
   → 在 problem_families/INDEX.md 里找同名/近名 family
   ↓
3. 用题面里可观察的信号查 trigger_index.json
   → 拿到 diagnosis + candidate_actions
   ↓
4. 用候选动作查 operator_evidence_matrix.csv
   → 看该算子在别的领域长什么样、代表题是哪些
   ↓
5. 用 anti_trigger_index.json 检查"我准备走的这条路是不是已知的坑"
   ↓
6. 需要看完整轨迹 → 按 problem_id 打开 raw_episodes/<worker>.jsonl
```

### 具体命令示例

```bash
# 找某个 trigger 信号
python -c "import json;d=json.load(open('trigger_index.json'));[print(e['signal'],e['candidate_actions']) for e in d['entries'] if '尺度' in e['signal']]"

# 找某个算子的全部证据
grep STATE_REREPRESENTATION operator_evidence_matrix.csv

# 找某道题的完整轨迹
grep '"problem_id": "M3-024"' raw_episodes/M3.jsonl | python -m json.tool
```

### 关键文件优先级

| 想干什么 | 读哪个 |
|---|---|
| 快速判断"这题该怎么想" | `trigger_index.json` |
| 避免走已知的错路 | `anti_trigger_index.json` |
| 判断一个想法是不是跨领域的通用结构 | `operator_evidence_matrix.csv` + `_index/operator_stats.json` |
| 看某个问题几何的完整画像 | `problem_families/<family>.md` |
| 看现有语言解释不了的题 | `unexplained_cases.md` |
| 了解覆盖边界与空白 | `coverage_report.md` |
| 抽查原始轨迹 | `raw_episodes/*.jsonl` |

---

## 7. 质量闸门

数据集经过**十道自动化校验**，全部可在 `_protocol/tools/` 下复跑。
完整的复跑命令与**顺序要求**见 `coverage_report.md` §14。

> **⚠️ 顺序很重要**：`build_coverage_data.py` 汇总前面各报告的数字。
> 若先跑它、后跑闸门，它会引用**过期快照**——本项目实际发生过一次。

### 闸门总表

| # | 工具 | 抓什么 | 本轮结果 |
|---|---|---|---:|
| 1 | `validate_episodes.py` | 字段齐全/类型/`problem_id` 连续/408 八字段/**空值**（存在≠有内容）/自评 E3+ | 0 ERROR |
| 2 | **`verify_evidence.py` ★** | `evidence_excerpt` 逐字回源 + **引用错题** + **摘录过短** | 268/279 |
| 3 | `check_episode_basis.py` | `raw_problem` **是否真的是题面**（分诊） | 41 条标记 |
| 4 | `check_operation_labels.py` | `key_transitions[].operation` **是否真在描述动作** | 86 条 |
| 5 | `scan_vocabulary_placement.py` | 标签放进了**错误的词表数组** | 2 条 |
| 6 | `detect_duplicates.py` | 跨 worker 重复题 → 产量虚高 | 3 对 |
| 7 | `audit_evidence_level.py` | **证据等级被低估**（跨文件 E2 候选） | 15 条 |
| 8 | `check_observability.py` | trigger 信号的符号级可观察性（**分诊**） | 199 SYMBOL_MISSING |
| 9 | `anti_operator_usage.py` | anti-operator 是否被一致使用 | 21 标签 |
| 10 | `discover_inline_markers.py` | 材料推理标记词（**发现式，不猜名字**） | 44 个 |

### 闸门 2 详解：`verify_evidence.py` ★

**本数据集最关键的检查。** 把每条 `evidence_excerpt` 规范化后回源文件逐字比对：

| 判定 | 含义 |
|---|---|
| `EXACT` | 逐字一致（合格） |
| `STRONG` / `WEAK` | OCR 尾部差异 / OCR 破坏严重 |
| `CONDENSED` | 用 `…`/`→` 拼接了非连续片段（内容真但违规） |
| `MIS-CITED` | 内容真但 `repo_path` 写错 |
| **`WRONG_QUESTION_BLOCK`** | 摘录逐字为真，但落在**另一道题**的题块里 |
| **`EXCERPT_TOO_SHORT`** | 摘录短到无法承载"这段原文支持了该思路" |
| `NOT_FOUND` | 全库找不到 → **疑似伪造** |

```bash
python _protocol/tools/verify_evidence.py \
  --src <源仓库根> --json _index/evidence_verify.json --md _index/evidence_verify.md
```

**为什么这道闸门必须存在**：`evidence_excerpt` 是下游核验"这个触发信号到底是不是从题面可观察"的**唯一凭据**。如果摘录里混着抽取者自己的箭头和重组，`E2`（材料明说）与 `E1`（我推断）的界线就消失了——那正是任务书要求 Critic 攻击的"事后贴标签"。

> 首轮实测：全库 **80% 的记录在这个字段上违规**（拼接摘录）。经两轮纠正后达到 **100% 逐字**。
> 这个数字变化过程本身是本数据集最有价值的方法论发现之一。

**后两种判定的来历**（都是 Critic 发现、而旧版闸门静默放过的）：

- `WRONG_QUESTION_BLOCK`：`C1-004` 是 2009 真题第 42 题，摘录却落在第 41 题的题块里。
  **旧版只问"这个文件里搜不搜得到"，不问摘录属不属于本题。**
- `EXCERPT_TOO_SHORT`：`M7-011` 的摘录是 **1 个字符「即」**。
  **1 个字符的串在任何文件里都能命中**，逐字性检查在这类条目上完全失效。

### ⚠️ 闸门的能力边界

**闸门能验格式、验逐字、验一致性，但验不了语义。** 实测有三类缺陷，**十道闸门全部放过**：

| 缺陷 | 为什么闸门抓不到 |
|---|---|
| `raw_problem` 不是题面 | 没有闸门在问"这个字段的语义是否成立" |
| `operation` 填的不是动作 | 同上 |
| worker 声称已修但未落盘 | 需**交叉核对两个文件**（notes vs JSONL） |

**这三类只有对抗性 Critic 审查能发现。** 本项目因此设了三份 Critic 报告，覆盖全部 12 个 worker。

### 其余工具

| 工具 | 作用 |
|---|---|
| `aggregate.py` | 生成算子证据矩阵、集中度、聚类种子、扁平化 trigger/anti-trigger |
| `build_indexes.py` | 由原始信号生成 `trigger_index.json` / `anti_trigger_index.json` |
| `build_coverage_data.py` | 汇总各闸门数字为 coverage 数据表（**必须最后跑**） |
| `make_blind_test.py` | 从真题抽题并**剥离答案块**；渲染示意图（**含 XML 预检 + 错误页检测**） |
| `check_solution_richness.py` | 测量标准解的"推理厚度"（太薄则只能判 UNVERIFIABLE） |
| `apply_remediation.py` | 按**显式清单**改数据，留可审计变更日志（缺省只预览） |
| `package.py` | 规范化 + 清理临时文件 + 打包 + 生成 MANIFEST |

---

## 8. 已知限制（诚实披露）

### 8.1 材料层面的限制

| 限制 | 说明 | 影响 |
|---|---|---|
| **概率讲义推理层最薄** | `分析` 标记 **0 处 / 10732 行**，仅靠 `考点及方法小结` 支撑 | M8 的 Episode 证据等级**天然偏低**（E1 比例更高）。这是材料属性，不是抽取质量问题 |
| **七门课用三套推理标记词** | 高数用 `分析`+`方法总结`+`注`；线代无 `方法总结`；概率用 `考点及方法小结`；408 用解释性正文 | 任何"统一正则抽推理句"的管线都会在概率与 408 上系统性漏抽 |
| **408 讲义是设计说明驱动** | 四门课 `例题` 计数 0–14，`考点追踪` 高达 148–181 | 408 的主要轨迹证据来自**真题解析**；`考点追踪` 是年份指针，**不是推理** |
| **OCR 噪声普遍** | 扫描件转写，公式与代码常损坏（如 `$ecost$` 实为 `$e^{\cos t}$`） | 按 SPEC §9 处理：能无歧义恢复就恢复，否则标 `[OCR?]` 降 confidence，**绝不编造题目条件**。多道题因题干自相矛盾被**整条放弃** |

### 8.2 数据集自身的限制

| 限制 | 说明 |
|---|---|
| **算子集中度偏高** | 在仅覆盖高等数学的 91 条上，前三算子覆盖 **83.6%**。词表在单领域内区分度弱，这是 Critic 的首要攻击目标 |
| **`E3`–`E5` 是机械推导** | 由"领域数/章节数/题数"推出，不等于语义上真的同构。使用时应回到代表 Episode 核对 |
| **`transfer_candidates` 未经实证** | 是抽取者的结构类比，**没有做过迁移实验**，应视为待验证假设而非结论 |
| **可复现性有缺口** | 部分 worker 的中间构建脚本在一次误删事故中丢失（M1/M2/M5/M6 的 builder）。正式产物与校验脚本完整，但**逐条重跑生成过程不完全可复现** |
| **抽取者与被抽取者同源风险** | 抽取由 LLM worker 完成，可能存在系统性偏好（如偏爱 `STATE_REREPRESENTATION`）。Critic 与 Blind Test 就是为暴露这一点而设 |

---

## 9. 来源与出处

| 项 | 值 |
|---|---|
| 源仓库 | `Elexs126/Dynamic-learning-program`（GitHub, public） |
| 源仓库用途 | 用户既有的数学一＋408 备考系统；本数据集**只读**使用其讲义/真题/习题 |
| 唯一题目编号体系 | 沿用源仓库既有编码（`M1-YY-C-TNN`、`408-YY-A-TNN`、`WD-*`、`ZY30-*`），Episode 的 `question_id` 直接挂靠，不另造命名空间 |
| 题目总量基线 | 源仓库 `系统文件/系统配置/canonical_sources_v1.json` 声明 8022 条；本次抽取器独立解析得到数学一 431 + 408 846，**与声明值完全一致** |

---

## 10. 环境与依赖

- **Python**：3.x，仅用标准库（`json`/`io`/`re`/`os`/`csv`/`hashlib`），无第三方依赖
- **SVG→PNG 渲染**（盲测示意图）：需要本机 Chrome 或 Edge（headless 截图），路径见 `make_blind_test.py` 的 `CHROME_CANDIDATES`
- **换行与编码**：所有 `.jsonl`/`.json`/`.md` 为 UTF-8 **无 BOM**、LF；`operator_evidence_matrix.csv` 为 UTF-8 **带 BOM**（便于 Excel 直接打开）

---

## 11. 复跑方式

```bash
# 1. 结构校验
python _protocol/tools/validate_episodes.py --out _index/validation_report.md --json _index/validation_report.json

# 2. 证据真实性
python _protocol/tools/verify_evidence.py --src <源仓库根> --md _index/evidence_verify.md --json _index/evidence_verify.json

# 3. 聚合（算子矩阵 + 集中度 + 聚类种子）
python _protocol/tools/aggregate.py --dir raw_episodes --outdir .

# 4. 材料与大纲支撑产物
python _protocol/tools/survey_markers.py --src <源仓库根>
python _protocol/tools/parse_syllabus.py --src <源仓库根>

# 5. 重新生成盲测题包（含示意图暂存）
python _protocol/tools/make_blind_test.py extract <真题目录> --ids <题号列表> --out blind_test/questions_408.md --src-root <源仓库根>

# 6. 规范化 + 清理 + 打包 + MANIFEST
python _protocol/tools/package.py --outputs . --dest <目标目录>
```

---

## 12. 当前快照

> 数据规模与质量指标的权威来源是生成出来的报告，本表为**定稿时快照**。
> 数字变了以报告为准——本表的作用是让人一眼看到量级，而不是替代报告。

| 指标 | 值 | 权威来源 |
|---|---|---|
| **Episode 总数** | **279** | `_index/validation_report.md` |
| 结构校验 ERROR | **0**（22 warning，均为 SPEC §8 允许的词表外标签） | 同上 |
| **估算唯一题目数** | **277**（虚高 2；3 对跨 worker 重复） | `_index/duplicates.md` |
| **`evidence_excerpt` 逐字率** | **268 / 279（96.1%）** | `_index/evidence_verify.md` |
| ↳ 另两类非逐字 | `WRONG_QUESTION_BLOCK` 1 ｜ `EXCERPT_TOO_SHORT` 10 | 同上 |
| **证据等级** | E2 **212** ｜ E1 **67** | `_index/evidence_level_audit.md` |
| 算子数 | **32** 出现 ｜ 29 跨领域 ｜ 28 "有意义"（判据已失效，见下） | `_index/operator_stats.json` |
| **母算子 top1 / top2 / top3** | **34.8% / 53.4% / 69.9%** | 同上 |
| anti-operator 集中度 | top1 23.4% ｜ top3 **43.4%**（21 个标签） | 同上 |
| **候选新算子** | **28**（达升级阈值 ≥3 次者 **1**） | `_index/unexplained_raw.md` |
| **UNKNOWN / UNEXPLAINED** | **38** 条 | 同上 |
| 无任何母算子命中的 Episode | **0**（⚠️ 见 `coverage_report.md` §9 的解释） | 同上 |
| **未修已知缺陷** | **53 条**（占 19%） | **`coverage_report.md` §11** |
| 大纲覆盖边界 | 2 track / 7 门课 / 46 主题 / 567 条目 | `_index/syllabus_map.json` |
| **材料行内标记** | **44 个**（≥3 次） | **`_index/inline_markers.md`** |
| 题目清单 | 数学一 **431** + 408 **846** | `_index/inv_math1.json` / `inv_408.json` |
| 盲测 | 80 格：HIT 63 ｜ PARTIAL 15 ｜ MISS 2 ｜ **FALSE_TRIGGER 0** | `blind_test/SUMMARY.md` |
| **问题族** | **22 族 + 1 孤儿组 + 4 UNASSIGNED = 255** | `problem_families/family_index.json` |
| ↳ 跨领域（**两个口径，不可互换**） | 宽（≥2 领域）**18** ｜ 严（数学×408）**10** | 同上 |
| Critic 报告 | **3 份**，覆盖全部 12 个 worker | `critic/*.md` |

**⚠️ 三处必须注意的引用事项**：

1. **材料标记词的权威来源已换。** 早期 `_index/source_marker_survey.md` 由"**猜标记名再搜**"得出，
   **三次被 worker 抓出漏项**（漏 `良哥解读`/`展示新知`/`学习札记`/`【评注】`/`【提示】`，
   且完全未覆盖 408 的答案层 `【解答】`）。**权威版本是 `_index/inline_markers.md`**。
2. **"无任何母算子命中 = 0"不是好消息。** 一套从不"解释不了"的词表本身就值得怀疑。
   完整解释见 `coverage_report.md` §9——结论是"**缺格**"而非"过泛"。
3. **`cross_domain_meaningful` 字段已失效，不应引用。** 该判据在 top1 较高时**恒真**
   （实测 34/35 满足），不携带信息。

**⚠️ 关于 top1 的数字变化**（读旧版本材料时须知道）：

| 时点 | top1 | 说明 |
|---|---:|---|
| 179 条（8 个 worker） | 45.2% | 早期报告引用的数字 |
| 279 条（12 个 worker，门控未修） | 38.0% | — |
| 门控修正后 | 34.9% | 排除"worker 自己说装不下"的条目 |
| **279 条（最终，冻结）** | **34.8%** | — |

**top1 随语料变大而下降，且 UNKNOWN 门控的修正额外拉低了它**——
即**"万能标签"的覆盖率有一部分是统计假象**。凡引用 45.2% 论证"三个标签吃掉九成"的旧表述，
都应改用 34.8%（结论方向不变，量级已变）。

---

## 13. 与源仓库其他系统的关系

本数据集**不修改**源仓库任何内容（源仓库全程只读），也**不替代**源仓库既有的标注体系：

| 源仓库既有 | 本数据集 | 关系 |
|---|---|---|
| `question_annotation_v1.2.schema.json`（L0–L3 标注） | Episode（问题轨迹） | **互补**：前者记"这题考什么、值多少分"，后者记"这题为什么难、怎么变容易" |
| `系统文件/题目标注/`（L1/L2/L3 累积标注） | `raw_episodes/` | 通过 `question_id` 关联，不重复计数 |
| `考试大纲/` | `_index/syllabus_map.json` | 后者是前者的结构化形式，**仅用于确定覆盖边界** |

源仓库的 `完整执行协议.md` 明确规定"系统不提供、不保存、不验证答案库"。本数据集**不建立答案库**：`evidence_excerpt` 只摘录讲义与真题中**关于思路的原话**，且必须逐字可回源核验。
