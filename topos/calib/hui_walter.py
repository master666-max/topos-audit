# -*- coding: utf-8 -*-
"""
topos.calib.hui_walter —— Hui–Walter 潜类模型（L5）：两独立信号源 × 两群体 → Se/Sp。
判据（PREREG/B2 E-B2-1）：点估计 |err|<0.05；真值落 95% bootstrap CI；
ρ=0.4 相关对照下估计偏离（确认对假共识敏感，防假阳性仪器）。

实现：充分统计量 = 每群体 2×2 判定计数表；EM 在计数表上做（免逐单元循环）；
多随机重启防边界退化（Se=Sp=1 的非识别解）。纯 stdlib。
"""
import math
import random


def _b(x, p):
    """伯努利似然项：观测 x，概率 p。"""
    return p if x == 1 else (1.0 - p)


def _em(tables, init=None, max_iter=500, tol=1e-10):
    """tables = {group_id: {(a,b): count}}，a/b ∈ {0,1}。
    返回 {pi: {g}, se: {j}, sp: {j}, ll: loglik}。"""
    gs = sorted(tables)
    if init is None:
        init = {}
    pi = {g: init.get("pi", {}).get(g, 0.15 + 0.15 * k) for k, g in enumerate(gs)}
    se = dict(init.get("se", {0: 0.9, 1: 0.85}))
    sp = dict(init.get("sp", {0: 0.9, 1: 0.85}))
    prev = None
    for _it in range(max_iter):
        # E 步（计数表上）；M 步分母 = 全部单元的 w 之和（ADR：修正 v1.0 实现的
        # 分母 bug——曾错用"T=1 格的计数合计"，导致 EM 从真值出发 LL 直跌 314）
        w_all = {g: 0.0 for g in gs}     # Σ cnt·w（全部格）
        w0_all = {g: 0.0 for g in gs}    # Σ cnt·(1-w)（全部格）
        w1_j = {0: 0.0, 1: 0.0}          # Σ cnt·w·[T_j=1]
        w0_j = {0: 0.0, 1: 0.0}          # Σ cnt·(1-w)·[T_j=0]
        ll = 0.0
        for g in gs:
            tab = tables[g]
            n_g = sum(tab.values())
            num_g = 0.0
            for (a, b), cnt in tab.items():
                l1 = _b(a, se[0]) * _b(b, se[1])
                l0 = _b(a, 1.0 - sp[0]) * _b(b, 1.0 - sp[1])
                den = pi[g] * l1 + (1.0 - pi[g]) * l0
                w = (pi[g] * l1 / den) if den > 0 else 0.0
                w_all[g] += cnt * w
                w0_all[g] += cnt * (1.0 - w)
                num_g += cnt * w
                if a == 1:
                    w1_j[0] += cnt * w
                else:
                    w0_j[0] += cnt * (1.0 - w)
                if b == 1:
                    w1_j[1] += cnt * w
                else:
                    w0_j[1] += cnt * (1.0 - w)
                ll += cnt * math.log(max(den, 1e-300))
            pi[g] = num_g / n_g if n_g else pi[g]
        # M 步：Se_j = Σ w·[T_j=1] / Σ w；Sp_j = Σ (1-w)·[T_j=0] / Σ (1-w)（跨群体合并）
        sw = sum(w_all.values())
        sw0 = sum(w0_all.values())
        new_se = {j: (w1_j[j] / sw if sw > 0 else se[j]) for j in (0, 1)}
        new_sp = {j: (w0_j[j] / sw0 if sw0 > 0 else sp[j]) for j in (0, 1)}
        delta = max([abs(new_se[j] - se[j]) for j in (0, 1)] +
                    [abs(new_sp[j] - sp[j]) for j in (0, 1)])
        se, sp = new_se, new_sp
        if prev is not None and abs(ll - prev) < tol and delta < 1e-9:
            break
        prev = ll
    return {"pi": pi, "se": se, "sp": sp, "ll": ll}


def hui_walter(tables, n_restarts=10, seed=20261009):
    """多随机重启 EM，取对数似然最大解。返回与 _em 同构的 dict。"""
    rng = random.Random(seed)
    best = None
    for k in range(n_restarts):
        if k == 0:
            init = {"pi": {}, "se": {0: 0.9, 1: 0.85}, "sp": {0: 0.9, 1: 0.85}}
        else:
            init = {"pi": {}, "se": {0: rng.uniform(0.5, 0.99), 1: rng.uniform(0.5, 0.99)},
                    "sp": {0: rng.uniform(0.5, 0.99), 1: rng.uniform(0.5, 0.99)}}
        res = _em(tables, init=init)
        if best is None or res["ll"] > best["ll"]:
            best = res
    return best


def bootstrap_ci(tables, n_boot=1000, seed=20261009):
    """参数 bootstrap：每群体 2×2 表多项式重采样 → 重跑 EM → 百分位 CI。"""
    rng = random.Random(seed)
    samples = {"pi": {g: [] for g in tables}, "se": {0: [], 1: []}, "sp": {0: [], 1: []}}
    for _b_i in range(n_boot):
        tab_b = {}
        for g, tab in tables.items():
            n_g = sum(tab.values())
            keys = list(tab)
            probs = [tab[k] / n_g for k in keys]
            new_tab = {k: 0 for k in keys}
            for _ in range(n_g):
                u = rng.random()
                acc = 0.0
                for k, p in zip(keys, probs):
                    acc += p
                    if u <= acc:
                        new_tab[k] += 1
                        break
            tab_b[g] = new_tab
        try:
            res = hui_walter(tab_b, n_restarts=5, seed=seed + _b_i)
        except (ValueError, ZeroDivisionError):
            continue
        for g in tables:
            samples["pi"][g].append(res["pi"][g])
        for j in (0, 1):
            samples["se"][j].append(res["se"][j])
            samples["sp"][j].append(res["sp"][j])

    def pct(xs):
        if not xs:
            return (float("nan"), float("nan"))
        s = sorted(xs)
        return (s[int(0.025 * len(s))], s[min(int(0.975 * len(s)), len(s) - 1)])

    return {"pi": {g: pct(v) for g, v in samples["pi"].items()},
            "se": {j: pct(v) for j, v in samples["se"].items()},
            "sp": {j: pct(v) for j, v in samples["sp"].items()}}


def synth_two_sources(n1, n2, pi1, pi2, se1, sp1, se2, sp2, rho_fp=0.0, seed=7):
    """合成两源两群体数据。
    rho_fp>0 时在误报侧注入共享成分（假共识对照）：
    P(E1=1,E2=1|d=0) = e1·e2 + ρ·sqrt(e1(1-e1)e2(1-e2))。"""
    rng = random.Random(seed)
    tables = {1: {}, 2: {}}
    for g, n, pi in ((1, n1, pi1), (2, n2, pi2)):
        for _i in range(n):
            d = 1 if rng.random() < pi else 0
            if d == 1:
                t1 = 1 if rng.random() < se1 else 0
                t2 = 1 if rng.random() < se2 else 0
            else:
                e1, e2 = 1.0 - sp1, 1.0 - sp2
                if rho_fp > 0.0:
                    p11 = e1 * e2 + rho_fp * math.sqrt(max(e1 * (1 - e1) * e2 * (1 - e2), 0.0))
                    p11 = min(p11, min(e1, e2))
                    u = rng.random()
                    if u < p11:
                        t1 = t2 = 1
                    elif u < p11 + (e1 - p11):
                        t1, t2 = 1, 0
                    elif u < p11 + (e1 - p11) + (e2 - p11):
                        t1, t2 = 0, 1
                    else:
                        t1 = t2 = 0
                else:
                    t1 = 1 if rng.random() < e1 else 0
                    t2 = 1 if rng.random() < e2 else 0
            k = (t1, t2)
            tables[g][k] = tables[g].get(k, 0) + 1
    return tables
