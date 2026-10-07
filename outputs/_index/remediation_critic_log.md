# 整改变更日志

清单：`remediation_critic.json`

**模式**：已写盘（原文件已备份为 `*.pre_remediation.bak`）

- 清单条目：5
- **实际改动的记录数：5**

| worker | problem_id | 改动类型 | 结果 | 依据 |
|---|---|---|---|---|
| C2 | C2-018 | `set_notes_evidence_level` | ✅ evidence_level E2 -> E1 | critic/c2c3c4m7.md（C2 的 E2 是否偏高） |
| C2 | C2-020 | `set_notes_evidence_level` | ✅ evidence_level E2 -> E1 | critic/c2c3c4m7.md（C2 的 E2 是否偏高） |
| C3 | C3-012 | `strip_token_from_operation` | ✅ 从 operation 中移除 STRUCTURAL_PROGRESS（1 处） | critic/c2c3c4m7.md A-3 |
| C3 | C3-015 | `strip_token_from_operation` | ✅ 从 operation 中移除 PROXY_OBJECTIVE_DRIFT（1 处） | critic/c2c3c4m7.md A-3 |
| C3 | C3-015 | `drop_operator_match` | ✅ 移除母算子数组中的 TARGET_DRIFT（2 -> 1 条） | critic/c2c3c4m7.md A-3 + _index/vocabulary_placement.md |

## 为什么用清单而不是"自动理解报告"

Critic 的判定里既有**机械可判**的（词表错位、字段与自身 notes 矛盾），
也有**需要判断**的（"这条 E2 该不该降 E1"）。
若让脚本去"理解"报告，它必然会在需要判断的地方乱猜。
因此本工具只执行**清单里逐条写明**的改动——清单是数据文件，可复核、可回滚。

**未纳入本清单的整改项**（需要判断或需要 worker 回改）：

- C2 的 23 条 key_transitions[].operation 需回读原文，把真动作从 after_state 移回 operation、把原假设移入 why_triggered。属内容改写，非机械可判。
- M7 的 10 条截断摘录（含 M7-011 的 1 字符『即』）需回读原文补全。已由 verify_evidence.py 的 EXCERPT_TOO_SHORT 闸门标出。
- C3 的 20 条 raw_problem 口径（题面归题面）需回读原文重做。已由 check_episode_basis.py 加 basis_flag 标记。
- M7 的 34 条 operation 无算子标签——但 Critic 判其『是真动作、只是没写标签』，与 C2 的『不是动作』性质不同，改法也不同，需人工决定是否改。
- C2-011 与 C2-014 的主算子错位（承重动作是候选新算子本身，primary 却挂了 STATE_REREPRESENTATION）——需判断是否改挂，属语义决定。

