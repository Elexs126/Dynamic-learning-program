# 重复题目检测（E4/E5 与产量统计的污染评估）

由 `detect_duplicates.py` 用 `raw_problem` 的字符 4-gram Jaccard（阈值 0.62）检测。

## 为什么必须做这个检查

M8 发现并已由我独立验证：**概率强化篇的「精选例题」大量逐字取自历年真题**。
实例：真题 `M1-24-C-T09`（2024 第9题） ≡ 强化篇 ch04 例4.26，题干逐字相同。

## ⚠️ 真正有害的是「跨 worker 重复」

我最初以为要看"是否同一来源文件"，这是**错的**：三条都引同一份 2016 真题的 Episode
完全可能是**三个不同 worker 各自立条**（实测确实如此：`M1-021` / `M2-020` / `M6-018`）。
正确的判别轴是**是否跨 worker**——同一问题被多个 worker 各立一条会让
Episode 总数、算子证据、`n_distinct_sections` 全部虚高。

## 结果

- 扫描 Episode：279
- 近似重复对：**3**（**跨 worker** 3 对、同 worker 0 对）
- 重复组数：1，涉及 Episode 3 条
- **估算唯一题目数：277（虚高 2 条）**
- **同一题被不同 worker 指派了不同主算子的对数：2**

## 🔍 最有价值的一条：同一题、三个 worker、三套算子

`M1-16-A-T19`（2016 数一第19题：`f(0)=1, 0<f'<1/2, x_{n+1}=f(x_n)`）
被 **三个 worker 各立了一条 Episode**，而且**主算子互不相同**：

| Episode | worker | 指派的主算子 |
|---|---|---|
| `M1-021` | M1（极限） | RIGIDIFY、SELF_IMPROVING_CLOSURE、CERTIFICATE_PRODUCTION |
| `M2-020` | M2（微分） | GLUE_LOCAL_TO_GLOBAL、SELF_IMPROVING_CLOSURE |
| `M6-018` | M6（级数） | GLUE_LOCAL_TO_GLOBAL、DEPENDENCY_ORDERING、REPAIR_SCALE_MATCHING |

**这是对"算子指派可靠性"的一次天然测量。** 同一道题、同一份材料，
三个 worker 给出三套标签——这直接印证了前面几轮观察到的**算子过度使用**问题：
标签不是从题目结构中唯一读出的，而在很大程度上取决于**抽取者从哪个角度切进去**。

## 受影响的算子（其 E4 等级需人工复核）

| 算子 | 涉及的 problem_id 数 | problem_id |
|---|---:|---|
| `GLUE_LOCAL_TO_GLOBAL` | 3 | M1-021、M2-020、M6-018 |
| `RIGIDIFY` | 3 | M1-021、M2-020、M6-018 |

## 跨 worker 重复对明细

| 相似度 | A | worker | B | worker | 算子是否分歧 |
|---:|---|---|---|---|---|
| 1.000 | M1-021 | M1 | M2-020 | M2 | **是** |
| 1.000 | M1-021 | M1 | M6-018 | M6 | **是** |
| 1.000 | M2-020 | M2 | M6-018 | M6 |  |

## 使用建议

1. **不要把重复对当作 E4 证据**——它们是一道题的两个副本。
2. 凡上表列出的算子，`n_distinct_sections` 偏高、`derived_evidence_level` 可能被高估，
   其 E4 结论必须回到代表 Episode 人工确认。
3. **产量应报"唯一题目数"而不是"Episode 行数"**。本报告的估算值是保守下限
   （阈值 0.62 只抓到高相似度对，改写过的同题抓不到）。
4. 跨 worker 重复是**编排失误**（任务分配时未划清真题归属），不是 worker 的错；
   但它对统计的影响必须显式扣除。

