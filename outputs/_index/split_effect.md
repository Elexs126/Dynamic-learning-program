# 算子拆分效果测量

由 `measure_split.py` 独立计算（只读 jsonl，不改动正式管线）。

- Episode 数：**279**
- 带 `sub_operator` 的匹配：**1**
- 无 `sub_operator` 的匹配（退回父类）：**695**
- `sub_operator: null`（判定"不属本算子"）：**0**
- `UNCLASSIFIED`（所有子类都装不下）：**0**

> **成功判据不是"拆出几个子类"，而是"头号标签还占多少"。**

### ⚠️ 分母口径（读数字前必须知道）

本表分母是**全部 279 条 Episode**，即"该标签覆盖了全部 Episode 的百分之几"。

`aggregate.py` 的 `top1_coverage` 用的是**排除 UNKNOWN 条目之后**的分母
（它把"worker 自己说装不下"的条目剔出了算子统计）。因此**两者绝对值不可直接比较**：
同一状态下本表报 ~39%，`aggregate.py` 报 ~35%。

**为什么仍以本表做拆分前后对比**：两次测量都由本工具在同一口径下完成，
**差值有效**。引用绝对值时必须写明口径。

## 母算子：粗粒度（父标签）

| 算子 | Episode 数 | 占全部 Episode |
|---|---:|---:|
| `STATE_REREPRESENTATION` | 110 | 39.4% |
| `RESTRICT_SLICE` | 63 | 22.6% |
| `AUXILIARY_OBJECT` | 51 | 18.3% |
| `EXACT_ELIMINATION` | 34 | 12.2% |
| `BRIDGE_OBSERVABLE` | 33 | 11.8% |
| `CRITICAL_SCALE_PROBE` | 31 | 11.1% |
| `INFORMATION_AXIS_DECOMPOSITION` | 31 | 11.1% |
| `DEPENDENCY_ORDERING` | 29 | 10.4% |

**粗粒度 top1 = 39.4% ｜ top2 = 22.6% ｜ top3 = 18.3%**

## 母算子：细粒度（sub_operator 优先）

| 子算子 | Episode 数 | 占全部 Episode |
|---|---:|---:|
| `STATE_REREPRESENTATION` | 110 | 39.4% |
| `RESTRICT_SLICE` | 63 | 22.6% |
| `AUXILIARY_OBJECT` | 51 | 18.3% |
| `EXACT_ELIMINATION` | 34 | 12.2% |
| `BRIDGE_OBSERVABLE` | 33 | 11.8% |
| `CRITICAL_SCALE_PROBE` | 31 | 11.1% |
| `INFORMATION_AXIS_DECOMPOSITION` | 31 | 11.1% |
| `DEPENDENCY_ORDERING` | 29 | 10.4% |
| `CONSTRAINT_COLLISION` | 26 | 9.3% |
| `SPACE_AUGMENTATION` | 25 | 9.0% |
| `LOW_BANDWIDTH_INTERFACE` | 24 | 8.6% |
| `GLUE_LOCAL_TO_GLOBAL` | 23 | 8.2% |
| `DEPENDENCY_REORGANIZATION` | 22 | 7.9% |
| `COUNTEREXAMPLE_PROBE` | 20 | 7.2% |

**细粒度 top1 = 39.4% ｜ top2 = 22.6% ｜ top3 = 18.3%**

## 结论

| 口径 | top1 |
|---|---:|
| 粗粒度（父标签） | **39.4%** |
| 细粒度（子标签） | **39.4%** |
| **降幅** | **0.0 个百分点** |

⚠️ **细粒度 top1 仍高于 25%% 阈值**——拆分未充分，或该结构确实普遍。

> 对照：`math_high1.md` 对 M1-M4 预估"拆后 top1 从 38.5% 降到 13.2%"。
> 本表是全库实测，与预估不同属正常（预估只覆盖 4 个 worker）。

## anti-operator：粗粒度 vs 细粒度

| 口径 | 头号标签 | 次数 | 占比 |
|---|---|---:|---:|
| 粗粒度 | `BAD_REPRESENTATION_LOCK_IN` | 147 | 23.0% |
| 细粒度 | `BAD_REPRESENTATION_LOCK_IN` | 147 | 23.0% |

