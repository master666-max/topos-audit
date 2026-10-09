# -*- coding: utf-8 -*-
"""
topos.pool.design —— 设计矩阵 A ∈ {0,1}^{M×N} 构建：空池丢弃、constraints 强制、逐池告警。
条款来源（均实测）：宽度平衡（decode run1 阳性并集罩 93.7%）→ max_width；
覆盖均衡（E-X1 零覆盖 11.5% → 散布不可检出）→ 诊断必出；
覆盖均衡≠检测最优（E-X1 v4）→ constraints 只丢弃+告警，不做"自动补池"。
"""
import json
import sys


def build_design(pool_pairs, n, constraints=None):
    """[(name, set)] → (rows, warnings)。constraints: {max_width, max_pools, min_pool_size}。"""
    c = constraints or {}
    max_width = c.get("max_width")
    max_pools = c.get("max_pools")
    min_size = c.get("min_pool_size", 1)
    warnings = []
    rows = []
    for name, members in pool_pairs:
        if len(members) == 0:
            warnings.append("空池已丢弃: %s" % name)
            continue
        if len(members) < min_size:
            warnings.append("池小于 min_pool_size=%d 已丢弃: %s (%d)"
                            % (min_size, name, len(members)))
            continue
        if max_width is not None and len(members) > max_width:
            warnings.append("池超 max_width=%d 已丢弃: %s (%d)"
                            % (max_width, name, len(members)))
            continue
        rows.append((name, members))
    if max_pools is not None and len(rows) > max_pools:
        drop = rows[max_pools:]
        rows = rows[:max_pools]
        warnings.append("池数 %d 超 max_pools=%d，截断 %d 个（按清单顺序保留前 %d）"
                        % (len(rows) + len(drop), max_pools, len(drop), max_pools))
    return rows, warnings


def coverage(rows, n):
    """三诊断（必填契约字段）：c_min / c_mean / zero_cover_rate + 宽度分布。"""
    col_cnt = [0] * n
    for _name, members in rows:
        for i in members:
            col_cnt[i] += 1
    zero = sum(1 for x in col_cnt if x == 0)
    widths = sorted(len(m) for _name, m in rows)
    return {
        "n_pools": len(rows),
        "c_min": min(col_cnt) if col_cnt else 0,
        "c_mean": round(sum(col_cnt) / max(n, 1), 2),
        "zero_cover_rate": round(zero / max(n, 1), 4),
        "pool_sizes": widths,
    }
