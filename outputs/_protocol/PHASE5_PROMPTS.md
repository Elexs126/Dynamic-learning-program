# Phase 5 聚合 Worker 提示词

> 用法：启动 subagent 时让它「读取本文件并执行其中 <节名> 一节的全部指示」。
> 所有 worker 动手前必须先读 `outputs/_protocol/EPISODE_SPEC.md`。

---

## TRIGGER-INDEX — 触发信号索引构建

你是「考研数学 × 408 问题空间预处理」项目的 **Trigger Index 构建 worker**。

【第一步】读：
- `outputs/_protocol/EPISODE_SPEC.md`
- `outputs/_index/trigger_signals_raw.jsonl`（扁平化的全部 trigger 信号）
- `outputs/_index/operator_stats.json`（算子跨域统计）
- `outputs/raw_episodes/*.jsonl`（需要时回查原文）
- `outputs/critic/*.md`（**必须先读**：被 Critic 判定为"不可从题面观察"的 trigger 一律不得进入索引）

【任务】把 trigger 信号语义聚类成可检索的索引条目。

**核心要求：signal 必须是「看到什么就应该警觉什么」，而不是知识点。**
- ❌ `需要用到泰勒公式`
- ✅ `分子分母存在多个同阶机制，且变量共同趋零 → 首次非零项未知 → 不要直接等价代换，先做尺度比较`

【产出】`E:\杂七杂八的垃圾堆\LearningOS\outputs\trigger_index.json`

结构：
```json
{
  "generated_from": "outputs/raw_episodes/*.jsonl",
  "episode_count": 0,
  "entries": [
    {
      "id": "T-001",
      "signal": "从题面可观察的警觉信号（一句话，写成'看到 X'）",
      "diagnosis": "这个信号意味着什么问题结构",
      "candidate_actions": ["OPERATOR_LABEL", "..."],
      "observable": true,
      "observability_note": "在题面的哪一部分能看到它",
      "positive_examples": ["problem_id", "..."],
      "counterexamples": ["problem_id（同信号但动作不同）"],
      "danger": "照这个信号走可能犯什么错",
      "evidence_level": "E3",
      "domains": ["高等数学", "数据结构"],
      "anti_trigger_refs": ["A-002"]
    }
  ]
}
```

【硬性要求】
- 每个 entry 至少 2 条 `positive_examples`（否则并入别的 entry 或降级到 `weak_entries`）。
- `observable` 必须为 true 才能进主索引；从答案反推出来的信号放进 `non_observable_entries` 并说明。
- 必须显式列出 `counterexamples`：**同一个信号在不同题里导向不同动作**的情况——这是防止"万能解释"的关键。
- `evidence_level` 用 `outputs/_index/operator_stats.json` 的机械推导值，不要自己拔高。
- 目标 25–45 条主条目。宁可少而准。

【完成后回报】条目数、被剔除的不可观察信号数、evidence_level 分布、跨领域条目数。

---

## ANTI-TRIGGER-INDEX — 反触发索引构建

你是「考研数学 × 408 问题空间预处理」项目的 **Anti-trigger Index 构建 worker**。

【第一步】读：
- `outputs/_protocol/EPISODE_SPEC.md`
- `outputs/_index/anti_trigger_raw.jsonl`（扁平化的 anti_triggers + naive_routes）
- `outputs/trigger_index.json`（若已生成，需交叉引用）
- `outputs/critic/*.md`（被 Critic 判为"敷衍"的错误路线不得进入索引）

【任务】把"自然但差"的做法聚成可检索的反触发条目。

【产出】`E:\杂七杂八的垃圾堆\LearningOS\outputs\anti_trigger_index.json`

结构：
```json
{
  "entries": [
    {
      "id": "A-001",
      "temptation": "为了便于估计立即取绝对值",
      "danger_signal": "原式存在正负相消",
      "lost_information": "cancellation",
      "failure_pattern": "取绝对值后各项同号，上界估计失效或过松",
      "failure_type": "PREMATURE_ABSOLUTE_VALUE",
      "examples": ["problem_id", "..."],
      "repair": "推迟有损操作，先在原符号下完成估计再取模",
      "domains": ["高等数学"],
      "related_triggers": ["T-004"]
    }
  ]
}
```

【硬性要求】
- 每个 entry 至少 1 条真实 example（来自 `anti_trigger_raw.jsonl`），不得凭空构造。
- `repair` 必须是**可执行的动作**，不是"要小心"。
- `lost_information` 必须写清**具体丢了什么**（cancellation？对称性？量纲？witness 一致性？）。
- 目标 15–30 条。允许少于 15 条，但要在文件里写 `coverage_note` 说明材料限制。
- 若某个 `failure_type` 在原始数据中只出现 1 次，标 `evidence_level: E1` 并说明。

【完成后回报】条目数、failure_type 分布、被剔除的敷衍条目数。

---

## UNEXPLAINED — 未解释案例整理

你是「考研数学 × 408 问题空间预处理」项目的 **Unexplained Cases worker**。

【第一步】读：
- `outputs/_protocol/EPISODE_SPEC.md`
- `outputs/raw_episodes/*.jsonl`（重点看 `possible_new_operator` 非 null 的、notes 里含 UNKNOWN/UNEXPLAINED 的）
- `outputs/critic/*.md`

【任务】**只收录**两类问题：
1. 现有问题空间语言解释起来**别扭**的；
2. 标准解里出现了**明显的新型结构变换**、现有母算子标签都不贴的。

**这是极重要的产物，不要隐藏失败样本。** 任务书明确要求"有明确的 MISS 和 UNKNOWN，不能全部宣称成功"。

【产出】`E:\杂七杂八的垃圾堆\LearningOS\outputs\unexplained_cases.md`

每条写：
```markdown
### U-001 <一句话标题>

- **问题**：problem_id / 来源 / 题干摘要
- **现有最接近算子**：XXX
- **为什么解释别扭**：（具体说明这个标签哪里不贴——是粒度不对？方向反了？还是它其实描述了结果而非动作？）
- **标准解实际做了什么**：（附原文摘录）
- **疑似缺失概念**：（用一句话命名这个缺失的结构动作）
- **是否值得新增母算子**：是 / 否 / 待定 + 理由
- **出现次数**：在多少道题里出现（决定是否够格升级为母算子）
```

开头必须有汇总表与统计。结尾必须有：
```markdown
## 对本体论的反省
（现有词表在哪些方向上有系统性盲区）
```

【硬性要求】
- 至少收录 8 条（若材料确实不足，如实说明并给出实际条数）。
- **不得**把"其实能解释"的题塞进来充数。
- 若某条在 ≥3 道题里重复出现，必须明确建议升级为母算子。

【完成后回报】条数、建议新增母算子数、最主要的本体论盲区。

---

## COVERAGE — 覆盖报告

你是「考研数学 × 408 问题空间预处理」项目的 **Coverage Report worker**。

【第一步】读：
- `outputs/_protocol/EPISODE_SPEC.md`
- `outputs/_index/operator_stats.json`、`outputs/_index/geometry_axes.json`
- `outputs/problem_families/INDEX.md` 与各 family 文件
- `outputs/trigger_index.json`、`outputs/anti_trigger_index.json`
- `outputs/unexplained_cases.md`
- `outputs/blind_test/SUMMARY.md`
- `考试大纲/2026考研数学一考试大纲.md`、`考试大纲/2026考研408考试大纲.md`（在源仓库 `E:\杂七杂八的垃圾堆\_dlp_src\` 下，**只用于确定覆盖边界**）

【任务】写 `E:\杂七杂八的垃圾堆\LearningOS\outputs\coverage_report.md`。

**不要报告"处理了多少章节"。** 必须回答：

### 数学
- 考研数学大纲中的问题世界，**哪些已经有充分的问题轨迹覆盖**？
- 哪些 **problem geometry 仍然空白**？（对照 `geometry_axes.json` 与大纲）
- 哪些 operator 证据**已经跨高数/线代/概率**？
- 哪些**只存在于单域**？

### 408
- 数据结构/OS/计组/网络中，**哪些问题族已经可以用统一语言解释**？
- **"状态—资源—不变量—转移"是否足以覆盖大多数问题？**（给出比例与反例）
- **还缺什么结构**？

### 预测力
- Blind test 命中率说明了什么？词表在哪些方向上有预测力、哪些没有？

【硬性要求】
- 每个判断必须附**数据依据**（引用具体统计数字或 problem_id）。
- 必须明确列出**空白与失败**，不得只报成功。
- 必须给出"下一步最该补什么"的排序建议。

【完成后回报】报告路径、空白 geometry 数、单域算子数、跨域算子数、你给出的下一步优先级。
