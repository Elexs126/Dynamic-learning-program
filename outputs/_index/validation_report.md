# Raw Episodes 校验报告

- Episode 总数：**279**
- worker 数：12
- ERROR：0 ｜ WARNING：22

## 各 worker 产量

| worker | episodes |
|---|---:|
| C1 | 24 |
| C2 | 26 |
| C3 | 24 |
| C4 | 24 |
| M1 | 22 |
| M2 | 22 |
| M3 | 25 |
| M4 | 22 |
| M5 | 20 |
| M6 | 20 |
| M7 | 26 |
| M8 | 24 |

## confidence 分布

- high: 184
- medium: 82
- unknown: 8
- low: 5

## evidence_level 分布

- E1: 67
- E2: 212

- 提及 UNKNOWN/UNEXPLAINED 的 Episode：38
- 带 possible_new_operator 的 Episode：32

## WARNING（前 80 条）

- C2:5  WARN   main_obstacle 疑似能力描述而非问题结构（含 '不会'）: 资源分配图在当前状态下无环，但死锁仍可能在未来发生。判断'会不会死锁'需要关于未来的信息，而操作系统无法预知未来请求。因
- C3:1  WARN   naive_routes[0].failure_type='UNRESOLVED_CONSTRAINT_CONFLICT' 不在 anti-operator 词表内
- C3:3  WARN   naive_routes[0].failure_type='UNRESOLVED_CONSTRAINT_CONFLICT' 不在 anti-operator 词表内
- C3:10  WARN   naive_routes[0].failure_type='UNRESOLVED_CONSTRAINT_CONFLICT' 不在 anti-operator 词表内
- C4:24  WARN   main_obstacle 疑似能力描述而非问题结构（含 '不会'）: 序号空间是有限的，而连接会被反复建立；如果每次都用同一个初始序号，那么「历史上发出但仍在网络中滞留的旧报文段」的序号就会
- M1:14  WARN   existing_operator_matches[2].operator_id='MISSING_SHARED_WITNESS' 不在母算子词表内
- M2:21  WARN   existing_operator_matches[1].operator_id='UNKNOWN' 不在母算子词表内
- M3:4  WARN   naive_routes[0].failure_type='UNJUSTIFIED_SYMMETRY_TRANSFER' 不在 anti-operator 词表内
- M3:10  WARN   naive_routes[0].failure_type='NEWTON_LEIBNIZ_BLIND_APPLICATION' 不在 anti-operator 词表内
- M3:10  WARN   naive_routes[1].failure_type='NEWTON_LEIBNIZ_BLIND_APPLICATION' 不在 anti-operator 词表内
- M3:17  WARN   naive_routes[0].failure_type='NEWTON_LEIBNIZ_BLIND_APPLICATION' 不在 anti-operator 词表内
- M5:3  WARN   initial_state.constraints 为空列表——确认这题真的没有对应内容
- M5:4  WARN   initial_state.constraints 为空列表——确认这题真的没有对应内容
- M5:15  WARN   naive_routes[2].failure_type='DEPENDENCY_ORDERING' 不在 anti-operator 词表内
- M6:1  WARN   naive_routes[1].failure_type='MISMATCHED_ENCODING_ORDER' 不在 anti-operator 词表内
- M6:3  WARN   naive_routes[0].failure_type='MISSING_BOUNDARY_CASE' 不在 anti-operator 词表内
- M6:3  WARN   naive_routes[1].failure_type='MISMATCHED_ENCODING_ORDER' 不在 anti-operator 词表内
- M6:4  WARN   naive_routes[0].failure_type='MISMATCHED_ENCODING_ORDER' 不在 anti-operator 词表内
- M6:4  WARN   naive_routes[1].failure_type='MISSING_BOUNDARY_CASE' 不在 anti-operator 词表内
- M6:6  WARN   naive_routes[0].failure_type='MISSING_BOUNDARY_CASE' 不在 anti-operator 词表内
- M6:9  WARN   naive_routes[1].failure_type='MISSING_BOUNDARY_CASE' 不在 anti-operator 词表内
- M6:10  WARN   naive_routes[1].failure_type='MISSING_BOUNDARY_CASE' 不在 anti-operator 词表内

