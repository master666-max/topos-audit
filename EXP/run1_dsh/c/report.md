# topos space 报告

- schema: `topos-space/1`
- root: `D:\WorkBuddy专用！危险！！！！！！！！\2026-10-09-02-32-12\topos-audit\tools\repos\dsh-launcher`
- manifest: `D:\WorkBuddy专用！危险！！！！！！！！\2026-10-09-02-32-12\topos-audit\EXP\run1_dsh\manifest.json`
- 单元数: 250 ｜ 耗时: 13.49s

## 分层耦合边

| 层 | 边数 |
|---|---|
| call | 552 |
| control | 45 |
| data | 315 |
| return | 23 |
| vardep | 165 |
| **融合** | **762** |

> 非 call 层边 210 条——按「如实降级」口径计入融合，不作召回承诺。

## 覆盖诊断（必填三诊断）

| 指标 | 值 |
|---|---|
| 池数 n_pools | 3 |
| 最小池覆盖 c_min | 0 |
| 平均池覆盖 c_mean | 0.1 |
| 零覆盖率 zero_cover_rate | 0.904 |

池大小分布：`[3, 6, 15]`

## 场非空率

| 场 | 非空率 |
|---|---|
| age | 1.0 |
| anchor | 0.064 |
| churn | 1.0 |
| diffusion | 1.0 |
| forman | 0.948 |
| loc | 1.0 |

## 设计矩阵告警

- 池超 max_width=75 已丢弃: p_hot (81)
- 池小于 min_pool_size=3 已丢弃: p_stale_big (1)
- 空池已丢弃: p_semantic_hot
- 空池已丢弃: p_stale_hot

## 池概览

```json
[
 {
  "name": "p_anchor_breadth",
  "width": 15
 },
 {
  "name": "p_big1",
  "width": 3
 },
 {
  "name": "p_deep_conf",
  "width": 6
 }
]
```

## 解码后验（topos-belief/1）

- decoder: `nb`

| # | 单元 | 后验 |
|---|---|---|
| 1 | `0` | 0.3945 |
| 2 | `6` | 0.2886 |
| 3 | `8` | 0.2886 |
| 4 | `129` | 0.2851 |
| 5 | `110` | 0.2817 |
| 6 | `5` | 0.2628 |
| 7 | `33` | 0.2353 |
| 8 | `107` | 0.2291 |
| 9 | `4` | 0.2182 |
| 10 | `95` | 0.2165 |

> 其余 240 单元后验低于第 10 名，从略。
