# 标注 schema v1.0.0 执行说明

本目录把既有协议和后续正式字段修正落成机器可读规范。它属于**执行既有协议**，不重设计 Teacher、Evaluator、Controller，也不改变 target-only 统计、启动时间盒或学生认证规则。

## 当前规范文件

- `question_annotation.schema.json`：逐题累积的标注 L0—L3。
- `question_annotations_bundle.schema.json`：标注记录集合及其生成元数据。
- `question_usage_role.schema.json`：独立的题目使用角色历史事件。
- `paper_usage_role.schema.json`：整卷使用角色历史事件。
- `usage_roles_bundle.schema.json`：整卷/题目角色事件集合；需配合跨事件校验器防止泄漏角色并存。
- `../config/canonical_sources_v1.json`：当前仓库唯一题源路径和数量基线。

## 已冻结的消歧

1. 正式主键使用 `question_id`；旧 prototype 的 `item_id` 只在迁移入口兼容。
2. L0 的完整性字段统一为 `question_completeness`；交接示例里的 `content_integrity` 视为旧别名。
3. L0 保留 `original_points` 和 `source_file`。虽然《标签说明》的最终简表漏列二者，但总体协议和交接都要求锁定分值与来源文件，不能在可执行 schema 中丢失。
4. 使用角色采用多条历史事件，不采用题目上的单值 `data_role`。同题可以同时属于 `RAW`、`TARGET_PRIOR`、`TRAIN` 等视图。
5. 启动角色的 canonical 枚举是 `STARTUP_TRAINING_ONLY`；旧文档中的 `STARTUP` 只作为概念简称，不写入数据。
6. 难度只允许 `basic / intermediate / advanced / very_advanced`。prototype 的 `highly_integrated` 迁移为 `very_advanced`，并保留迁移记录。
7. 前置按 `hard_prerequisite / soft_prerequisite` 分组。prototype 的 `hard / soft` 只是迁移输入值。
8. 原始 Markdown、派生标注、角色历史和学生作答继续分离；annotation 中禁止写答案、完整解析、使用角色和学生结果。
9. L0 必须保存 canonical `paper_id`、仓库相对 `source_file`、稳定 `source_locator` 和原题块 SHA-256；仅写 `locked: true` 不能代替不可变性校验。
10. `ADAPTIVE_DIAGNOSTIC`、`FIXED_AUDIT`、`SEALED` 均对 Teacher 隐藏；角色集合必须通过跨事件校验，不能与 active `TARGET_PRIOR` 或训练角色并存。

## 当前题库基线

按 canonical 路径扫描 `【唯一编号】`，当前有 8024 个唯一题目记录：

| 题源 | 数量 |
|---|---:|
| 数学一真题 | 431 |
| 408 真题 | 846 |
| 张宇基础30讲 | 876 |
| 数学二真题 | 431 |
| 数学三真题 | 431 |
| 张宇1000题 | 1041 |
| 王道408 | 2897 |
| 408经典练习题 | 1071 |
| 合计 | 8024 |

交接中的 8125 是估计值；差额来自王道408被估为2998，而实库为2897。除非以后真正导入缺失记录，否则不得为了对齐估计数而制造101条数据。

`delightful-salk/408经典练习题` 与 `配套习题/408/408经典练习题` 内容完全相同；canonical 路径固定为后者。根目录的50题精选也是数学一真题的派生集。两者均必须从全库计数中排除。

数学一与408的1277题只是**可进入目标统计的候选全集**，不是默认全部对 Teacher 激活 `TARGET_PRIOR`。FIXED_AUDIT、SEALED 和尚未退役的诊断题必须先隔离，退役后才可进入可见统计历史。

## 尚未伪装成“已解决”的问题

- 当前大题 ID 多数仍是整道题级，尚未完成“可独立判分的最小小问”原子化。schema 将 `question_id` 定义为最终原子 ID，但旧50题迁移先保留原 ID，并把多评分单元记录标为 `needs_review`；没有可靠子题分值时不自动拆题或编分。
- 当前没有独立 canonical knowledge dictionary。50题中的知识点 ID 仅作为迁移候选保留，不能据此宣称全库词典已冻结。
- `official_scope_coarse` 等 L1 字段在旧 prototype 中从未真实记录。迁移文件只做可追溯回填，状态保持 `needs_review`，不冒充历史候选标注。
- `teaching_diagnosis`、`difficulty_dimensions`、`novelty_features` 等 prototype 扩展字段不进入正式核心 schema。原文件继续作为只读历史证据，不覆盖、不删除。

## 明确废弃的字段

- `candidate_main_ability` → 迁移为 `candidate_main_knowledge`。
- `audited_main_ability` → 删除，不再创建。
- annotation 内的 `data_role / usage_role` → 移至角色历史表。
- `answer / solution / reference_answer / reference_solution` → 禁止进入标注。

## 执行顺序

先运行旧50题迁移和结构校验，确认 schema 与 QA 工具能处理真实数据；通过后再批量生成核心题库的 L0/L1，并对数学一、408 的大题做原子化结构 QA。L3 继续只对实际调用题按需完成。
