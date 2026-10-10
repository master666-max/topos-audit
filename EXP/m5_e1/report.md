# topos space 报告

- schema: `topos-space/1`
- root: `D:\WorkBuddy专用！危险！！！！！！！！\2026-10-09-02-32-12\topos-audit\tools\repos\express-master\lib`
- manifest: `D:\WorkBuddy专用！危险！！！！！！！！\2026-10-09-02-32-12\topos-audit\EXP\m5_e1\manifest_js.json`
- 单元数: 35 ｜ 耗时: 0.02s

## 分层耦合边

| 层 | 边数 |
|---|---|
| call | 10 |
| control | 0 |
| data | 0 |
| return | 0 |
| vardep | 0 |
| **融合** | **10** |

## 覆盖诊断（必填三诊断）

| 指标 | 值 |
|---|---|
| 池数 n_pools | 2 |
| 最小池覆盖 c_min | 0 |
| 平均池覆盖 c_mean | 0.23 |
| 零覆盖率 zero_cover_rate | 0.7714 |

池大小分布：`[2, 6]`

## 场非空率

| 场 | 非空率 |
|---|---|
| anchor | 0.0 |
| forman | 0.4 |

## 设计矩阵告警

- 空池已丢弃: p_anchor

## 池概览

```json
[
 {
  "name": "p_curv_lo",
  "width": 6
 },
 {
  "name": "p_curv_hi",
  "width": 2
 }
]
```

## 解码后验（topos-belief/1）

- decoder: `nb`

| # | 单元 | 后验 |
|---|---|---|
| 1 | `0` | 0.0400 |
| 2 | `1` | 0.0400 |
| 3 | `2` | 0.0400 |
| 4 | `3` | 0.0400 |
| 5 | `4` | 0.0400 |
| 6 | `5` | 0.0400 |
| 7 | `6` | 0.0400 |
| 8 | `7` | 0.0400 |
| 9 | `8` | 0.0400 |
| 10 | `9` | 0.0400 |

> 其余 25 单元后验低于第 10 名，从略。
