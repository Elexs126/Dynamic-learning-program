# 标注 schema v1.0.0 执行说明

本目录把既有协议和后续正式字段修正落成机器可读规范。它属于**执行既有协议**，不重设计 Teacher、Evaluator、Controller，也不改变 target-only 统计、启动时间盒或学生认证规则。

2026-09-06更新了人读执行口径：核心来源不再提前全量L2，教材按需抽取，补充API建设预算及人工离线Evaluator路径。本次未修改JSON配置、schema或脚本；规则说明不代表机器校验或自动限额已经支持，兼容边界见文末。

## 当前规范文件

- `question_annotation.schema.json`：逐题累积的标注 L0—L3。
- `question_annotations_bundle.schema.json`：标注记录集合及其生成元数据。
- `question_usage_role.schema.json`：独立的题目使用角色历史事件。
- `paper_usage_role.schema.json`：整卷使用角色历史事件。
- `usage_roles_bundle.schema.json`：整卷/题目角色事件集合；需配合跨事件校验器防止泄漏角色并存。
- `attempt_record.schema.json`：append-only 作答日志的单行记录；答案、题干、作答过程和解析均禁止进入。
- `../配置/canonical_sources_v1.json`：当前仓库唯一题源路径和数量基线。
- `../配置/evaluator_public_contract_v1.json`：Teacher可见的Evaluator接口与不透明池句柄；不包含隐藏题身份。
- `../运行记录/attempts_v1.jsonl`：正式作答日志，Day 0 为0字节、0条记录。

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
11. `teacher_visible:false`只是数据声明，不构成访问控制。隐藏身份、原文及已知副本不得进入Teacher可读范围；人工离线保管或独立系统均须真实满足隔离条件后才能使用隐藏测评，自动化路径仍需独立存储和进程。
12. attempts 使用 append-only JSONL；单次记录只保存学生自核结果和运行元数据，能力状态与认证等级由历史派生，不能覆盖原尝试。

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

`系统文件/历史归档/重复副本/408经典练习题` 与 `配套习题/408/408经典练习题` 内容完全相同；canonical 路径固定为后者，归档副本不得参与扫描。`系统文件/标签/考研数学一真题精选50题_23章节全覆盖.md` 也是数学一真题的派生集，不能重复计数。

数学一与408的1277题只是**可进入目标统计的候选全集**，不是默认全部对 Teacher 激活 `TARGET_PRIOR`。FIXED_AUDIT、SEALED 和尚未退役的诊断题必须先隔离，退役后才可进入可见统计历史。

## 尚未伪装成“已解决”的问题

- 当前大题 ID 多数仍是整道题级，尚未完成“可独立判分的最小小问”原子化。schema 将 `question_id` 定义为最终原子 ID，但旧50题迁移先保留原 ID，并把多评分单元记录标为 `needs_review`；没有可靠子题分值时不自动拆题或编分。
- 当前没有独立 canonical knowledge dictionary。50题中的知识点 ID 仅作为迁移候选保留，不能据此宣称全库词典已冻结。
- 当前共享工作区不能提供Teacher与Evaluator的真实访问隔离；`evaluator_public_contract_v1.json` 只定义接口，不能证明固定审计或密封题已经分配。
- `official_scope_coarse` 等 L1 字段在旧 prototype 中从未真实记录。迁移文件只做可追溯回填，状态保持 `needs_review`，不冒充历史候选标注。
- `teaching_diagnosis`、`difficulty_dimensions`、`novelty_features` 等 prototype 扩展字段不进入正式核心 schema。原文件继续作为只读历史证据，不覆盖、不删除。

## 明确废弃的字段

- `candidate_main_ability` → 迁移为 `candidate_main_knowledge`。
- `audited_main_ability` → 删除，不再创建。
- annotation 内的 `data_role / usage_role` → 移至角色历史表。
- `answer / solution / reference_answer / reference_solution` → 禁止进入标注。

## 执行顺序

复用已完成的Day 0准备、迁移及校验结果，不因本轮文档修订重跑。全库L0/L1先取得可机械获得的元数据，语义字段保持来源与不确定性；按近期实际需要补充L2教学字段及L3，对用于统计或即将调用的大题处理必要原子化QA。

FIXED_AUDIT、SEALED由满足隔离条件的人工离线Evaluator或独立系统私下分配，尚未满足时保持default-deny。E只纳入Teacher可见且主标签、分值和原子口径核对完整的整卷年份，不把缺失或隐藏当0。教材批次按需调用，额外后台建设遵守API预算；数值预算未明确时暂停。

## 本轮修改边界与兼容规则

- 2153是核心来源候选规模，1277是目标考试统计候选全集，均不是提前全量L2完成数或当前E样本数。
- 字段级审核完成与整条L2/L3完成必须分开。沿用已有规范保存可表达的候选及审核证据；若schema不能表达局部完成，继续保留候选状态并暂缓相应正式E统计，不绕过校验、伪造必填值或另造平行正式表。
- 人工离线测评回传不暴露身份的汇总，不能把池句柄伪装成question_id，也不能为适配attempts而公开真实题号。现有逐题日志暂不承载不兼容的汇总；离线保存明细，按整卷/科目结果做周审计，未知维度不推定认证。
- 本轮没有修改机器配置/schema/脚本，也没有建立API自动封顶或测评存储接口。已有结构校验PASS不能证明这些新增执行规则已经自动实现。
- 教材映射、Scope及批次表内容未改，JSON与Markdown的原有结构数据继续保留；批次导航完整不等于授权全量执行。
