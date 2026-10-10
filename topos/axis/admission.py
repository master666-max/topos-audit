# -*- coding: utf-8 -*-
"""
topos.axis.admission —— 轴准入三准则的工具化（设计 §4.5「可算化（M2 落地）」欠账补齐）。

三读数（对候选池 vs 已有池集合）：
  Δcov     单位覆盖增量 = |候选 \\ ∪已有| / |候选|（0 = 纯冗余覆盖）
  max_rho  候选隶属向量与每个已有池隶属向量的 Pearson |ρ| 最大值
           （设计初筛：|ρ| < 0.3 才过）
  Δlogdet  池空间 Fisher 信息矩阵行列式增量
           G = A W Aᵀ（A=设计矩阵，W=diag(1/(d̂(1−d̂))) 伯努利信息权重），
           Δ = log(1 + w·aᵀG⁻¹a)（矩阵行列式引理；重复池 = 独立重复测量的增益）

诚实边界：单位空间的完整 FIM（含 Se/Sp 导数与 (1−d)² 修正）留 M2 精化；重复池的
Δlogdet 只反映「同池二次测量」的增益，覆盖冗余由 Δcov/|ρ| 两个读数兜住——三读数
合看，不许单读数下准入结论。
"""
import json
import math


def _pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def _logdet(g, n):
    """对称正半定矩阵的 logdet（高斯消元，半正定退化 → -inf）。"""
    m = [[float(g[i][k]) for k in range(n)] for i in range(n)]
    logdet = 0.0
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            return float("-inf")
        if piv != col:
            m[col], m[piv] = m[piv], m[col]
        piv_val = m[col][col]
        logdet += math.log(abs(piv_val))
        for r in range(col + 1, n):
            factor = m[r][col] / piv_val
            for k in range(col, n):
                m[r][k] -= factor * m[col][k]
    return logdet


def admit(pool_members, candidate, dhat=None, se=0.9, sp=0.95):
    """候选池准入三读数。

    pool_members: [(name, [unit_idx...])] 已有池
    candidate:    (name, [unit_idx...])
    dhat:         {unit_idx: 后验}（缺省全 0.04——未解码时的仪器先验名义值）
    返回 {dcov, max_rho, rho_vs, dlogdet, verdict_hint}
    """
    k = se + sp - 1.0
    dhat = dhat or {}
    w = lambda i: 1.0 / max(1e-9, dhat.get(i, 0.04) * (1 - dhat.get(i, 0.04)))

    cand = set(candidate[1])
    existing_union = set()
    for _nm, ms in pool_members:
        existing_union |= set(ms)
    dcov = len(cand - existing_union) / len(cand) if cand else 0.0

    all_pools = list(pool_members) + [candidate]
    n = max([max(ms) + 1 for _nm, ms in all_pools if ms] or [1])

    def gmat(pools):
        m = len(pools)
        g = [[0.0] * m for _ in range(m)]
        for a in range(m):
            sa = set(pools[a][1])
            for b in range(a, m):
                sb = set(pools[b][1])
                inter = sa & sb
                v = sum(w(i) for i in inter)
                g[a][b] = v
                g[b][a] = v
        return g

    g0 = gmat(pool_members)
    g1 = gmat(list(pool_members) + [candidate])
    ld0, ld1 = _logdet(g0, len(g0)), _logdet(g1, len(g1))
    dlogdet = round(ld1 - ld0, 6) if (ld0 > float("-inf") and
                                      ld1 > float("-inf")) else None

    rhos = {}
    for nm, ms in pool_members:
        s = set(ms)
        xs = [1.0 if i in s else 0.0 for i in range(n)]
        ys = [1.0 if i in cand else 0.0 for i in range(n)]
        rhos[nm] = round(_pearson(xs, ys), 4)
    # 语义（RUN1/设计 §4.5 校正）：正相关 ρ = 覆盖重叠（冗余，初筛红线）；
    # 负 ρ = 互补覆盖（组测试想要的高质量互补），不算冗余。
    max_rho = max(rhos.values()) if rhos else 0.0          # 带符号（信息）
    max_rho_pos = max([0.0] + [v for v in rhos.values()])  # 冗余判定用
    hint = ("Δcov>0 且正相关 ρ<0.3 → 过初筛；Δlogdet 仅计独立测量增益，"
            "覆盖冗余看 Δcov/正相关 ρ——三读数合看；负 ρ=互补覆盖（好）")
    return {"dcov": round(dcov, 4), "max_rho": max_rho,
            "max_rho_pos": max_rho_pos, "rho_vs": rhos,
            "dlogdet": dlogdet, "verdict_hint": hint}


def from_space_json(space_json, cand_name, cand_members, belief_json=None):
    """便捷入口：从 space.json 取 pool_members/units，belief 取 d̂。"""
    with open(space_json, encoding="utf-8") as f:
        rep = json.load(f)
    dhat = None
    if belief_json:
        with open(belief_json, encoding="utf-8") as f:
            dhat = {int(k): v for k, v in
                    json.load(f).get("belief", {}).items()}
    pools = [(nm, [int(i) for i in ms]) for nm, ms in rep["pool_members"]]
    return admit(pools, (cand_name, [int(i) for i in cand_members]),
                 dhat=dhat)
