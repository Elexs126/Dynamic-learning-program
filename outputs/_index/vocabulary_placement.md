# 词表错位扫描（标签放进了错误的数组）

由 `scan_vocabulary_placement.py` 生成。母算子词表解析自 SPEC §7，anti-operator 词表解析自 §8。

- 母算子词表：34 个标签
- anti-operator 词表：16 个标签
- **错位条目：2**

| 类型 | 条数 | 处置 |
|---|---:|---|
| `ANTI_OPERATOR_IN_MOTHER_ARRAY` | 1 | 移入 naive_routes[].failure_type（它是 anti-operator） |
| `PLACEHOLDER_IN_MOTHER_ARRAY` | 1 | 移出数组，改由 notes / possible_new_operator 表达 |

## 明细

| problem_id | worker | 数组下标 | operator_id | 类型 | is_primary_move |
|---|---|---:|---|---|---|
| M1-014 | M1 | 2 | `MISSING_SHARED_WITNESS` | ANTI_OPERATOR_IN_MOTHER_ARRAY | False |
| M2-021 | M2 | 1 | `UNKNOWN` | PLACEHOLDER_IN_MOTHER_ARRAY | False |

## 为什么必须处理

`existing_operator_matches` 的语义是"**这一步属于哪个结构动作**"。
把 anti-operator（描述失败）或占位符 `UNKNOWN` 放进去，会让下游：

- 把它们当成正常的结构动作统计进覆盖率；
- 在按 `is_primary_move` 聚合时把"worker 承认解释不了"的条目当成证据。

**注**：`aggregate.py` 已通过 `NON_OPERATOR_LABELS` 在统计时排除这类标签，
所以**统计数字是干净的**；但原始数据仍应修正，以免下游直接读 JSONL 时被误导。

