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
    # 相对宽度（真仓必需）：三分位切片宽度随 N 线性增长，绝对 max_width 在大仓上
    # 会把所有切片砍光（stdlib N=18198 实测：默认清单产出 0 池、零覆盖 100%）
    if c.get("max_width_pct") is not None:
        pct_w = max(1, int(n * float(c["max_width_pct"])))
        max_width = pct_w if max_width is None else min(max_width, pct_w)
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


def coverage_fill(rows, n, constraints=None, prefix="fill_"):
    """B8 兜底覆盖池：把**未覆盖单元**按编号顺序切成等宽块追加为池。

    constraints=None ⇒ 不启用（返回 []，一行都不许加）。
    语义：不猜谁可疑，**只保证每个单元至少被一个池碰到**——
    等价于"人肉通读一遍"，与 D-B6-5 的 grep 对照臂同口径（grep 也是看全部）。
    这样设计是为了回答 **"到底是覆盖问题还是信号问题"**：
    兜底池不携带任何信号，若补满覆盖后 AUC 仍 ≈0.5 ⇒ 答案是信号问题（D-B8-4）。

    块宽 W = max(min_pool_size, min(max_width, max_width_pct·n))；
    尾块不足 min_pool_size 则并入前一块（**不得丢单元**）；总池数受 max_pools 上限约束。
    """
    if not constraints:
        return []
    c = constraints
    max_width = c.get("max_width")
    if c.get("max_width_pct") is not None:
        pct_w = max(1, int(n * float(c["max_width_pct"])))
        max_width = pct_w if max_width is None else min(max_width, pct_w)
    min_size = int(c.get("min_pool_size", 1))
    W = max(min_size, int(max_width)) if max_width else max(min_size, 1)
    max_pools = c.get("max_pools")

    covered = set()
    for _nm, m in rows:
        covered |= m
    uncovered = [i for i in range(n) if i not in covered]
    if not uncovered:
        return []

    out = []
    for s in range(0, len(uncovered), W):
        chunk = set(uncovered[s:s + W])
        if not chunk:
            continue
        if len(chunk) < min_size and out:
            out[-1] = (out[-1][0], out[-1][1] | chunk)   # 尾巴并入前一块，不丢单元
            continue
        out.append(("%s%02d" % (prefix, len(out) + 1), chunk))

    if max_pools is not None:
        room = max_pools - len(rows)
        if room <= 0:
            return []
        if len(out) > room:
            # 截断：把多余的块并进最后一个保留块，仍不丢单元
            keep, rest = out[:room], out[room:]
            if keep:
                merged = set(keep[-1][1])
                for _nm, m in rest:
                    merged |= m
                keep[-1] = (keep[-1][0], merged)
            out = keep
    return out


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
