# topos space 报告

- schema: `topos-space/1`
- root: `D:\WorkBuddy专用！危险！！！！！！！！\2026-10-09-02-32-12\topos-audit\tools\repos\dsh-launcher`
- manifest: `D:\WorkBuddy专用！危险！！！！！！！！\2026-10-09-02-32-12\topos-audit\EXP\run1_dsh\manifest.json`
- 单元数: 169 ｜ 耗时: 10.11s

## 分层耦合边

| 层 | 边数 |
|---|---|
| call | 301 |
| control | 41 |
| data | 199 |
| return | 19 |
| vardep | 110 |
| **融合** | **445** |

> 非 call 层边 144 条——按「如实降级」口径计入融合，不作召回承诺。

## 覆盖诊断（必填三诊断）

| 指标 | 值 |
|---|---|
| 池数 n_pools | 4 |
| 最小池覆盖 c_min | 0 |
| 平均池覆盖 c_mean | 0.39 |
| 零覆盖率 zero_cover_rate | 0.6923 |

池大小分布：`[4, 5, 16, 41]`

## 场非空率

| 场 | 非空率 |
|---|---|
| age | 1.0 |
| anchor | 0.095 |
| churn | 1.0 |
| diffusion | 1.0 |
| forman | 0.917 |
| loc | 1.0 |

## 设计矩阵告警

- 空池已丢弃: p_stale_big
- 池小于 min_pool_size=3 已丢弃: p_big1 (2)
- 空池已丢弃: p_stale_hot

## 池概览

```json
[
 {
  "name": "p_anchor_breadth",
  "width": 16
 },
 {
  "name": "p_hot",
  "width": 41
 },
 {
  "name": "p_deep_conf",
  "width": 4
 },
 {
  "name": "p_semantic_hot",
  "width": 5
 }
]
```

## 解码后验（topos-belief/1）

- decoder: `nb`

| # | 单元 | 后验 |
|---|---|---|
| 1 | `21` | 0.9724 |
| 2 | `33` | 0.9720 |
| 3 | `26` | 0.9654 |
| 4 | `36` | 0.9521 |
| 5 | `20` | 0.8997 |
| 6 | `14` | 0.4826 |
| 7 | `10` | 0.4793 |
| 8 | `43` | 0.4760 |
| 9 | `31` | 0.4706 |
| 10 | `23` | 0.4698 |

> 其余 159 单元后验低于第 10 名，从略。
