# -*- coding: utf-8 -*-
"""
topos.infer.prior —— 图先验（扩散平滑）+ 池宽自适应强度（W5，PREREG/B3 T-B3-d）。

架构条款 §6.2：图先验救"证据太弱"，不救"证据太泛"——强度必须按池宽自适应，
宽池自动减弱、窄池才允许强先验。衰减曲线为预注册证伪对象（PREREG/B3 U-B3-1）。

搬迁自 mini-lab/decode_mini.power_lam_max（真仓 8.8× 实测件的谱部分）。
stdlib-only；[M] power_lam_max；[U] 衰减曲线（证伪判据见 PREREG/B3 §3）。
"""
import math
import random


def power_lam_max(adj, n, iters=60, seed=7):
    """幂迭代估计图拉普拉斯最大特征值 λmax（对称 L = D - A）。

    搬迁自 decode_mini.power_lam_max（逐字节同口径）。
    返回 float；孤立图（无边）返回 0。
    """
    rng = random.Random(seed)
    x = [rng.gauss(0, 1) for _ in range(n)]
    lam = 0.0
    for _ in range(iters):
        y = [0.0] * n
        for u in range(n):
            s = len(adj[u]) * x[u]
            for v in adj[u]:
                s -= x[v]
            y[u] = s
        ny = math.sqrt(sum(q * q for q in y)) or 1e-30
        nx = math.sqrt(sum(q * q for q in x)) or 1e-30
        lam = sum(p * q for p, q in zip(x, y)) / nx
        x = [q / ny for q in y]
    return lam


def mean_pool_width(pools, n):
    """每单元的平均所属池宽 w̄_i（所属池宽度的算术平均；无池单元 = None）。"""
    wsum = [0.0] * n
    cnt = [0] * n
    for _name, members in pools:
        w = len(members)
        for i in members:
            wsum[i] += w
            cnt[i] += 1
    out = [None] * n
    for i in range(n):
        if cnt[i]:
            out[i] = wsum[i] / cnt[i]
    return out


def adaptive_alpha(pools, adj, n, lam_max=None):
    """泛度自适应扩散强度（PREREG/B3 T-B3-d **v2 曲线**，v1.2 修订）。

    φ_i = w̄_i / N（w̄_i = i 所属池平均宽；零覆盖单元取场景中位 φ）；
    g(φ) = 1                （φ ≤ 0.1 —— 证据细粒度，先验满强度）
    g(φ) = 1/(1+(φ/0.1)²)   （φ > 0.1 —— 证据泛化，先验平滑衰减）
    α_i = (1/λmax)·g(φ_i)。

    v1 曲线（w0/(w0+w̄)）死因登记：窄池段强度砍半，救弱通道失效（PREREG v1.2）。
    返回 (alphas, meta)。
    """
    if lam_max is None:
        lam_max = power_lam_max(adj, n)
    widths = mean_pool_width(pools, n)
    have = [w for w in widths if w is not None]
    phi_med = (sorted(have)[len(have) // 2] / n) if have else 0.0
    inv = 1.0 / lam_max if lam_max > 0 else 0.0
    alphas = [0.0] * n
    for i in range(n):
        w = widths[i]
        phi = (w / n) if w is not None else phi_med
        g = 1.0 if phi <= 0.1 else 1.0 / (1.0 + (phi / 0.1) ** 2)
        alphas[i] = inv * g
    meta = {"lam_max": round(lam_max, 4), "phi_med": round(phi_med, 5),
            "widths": widths,
            "alpha_max": round(max(alphas) if alphas else 0.0, 6)}
    return alphas, meta


def fixed_alpha(adj, n, lam_max=None):
    """固定强度（mini-lab 口径）：α = 1/λmax，全单元同值。"""
    if lam_max is None:
        lam_max = power_lam_max(adj, n)
    a = 1.0 / lam_max if lam_max > 0 else 0.0
    return [a] * n, {"lam_max": round(lam_max, 4), "phi_med": None,
                     "widths": [None] * n, "alpha_max": round(a, 6)}


def diffuse(z0, adj, n, alphas, steps):
    """逐单元加权扩散：z ← z − α_u·(deg(u)·z_u − Σ_{v∼u} z_v)，steps 步。

    alphas 逐单元（自适应 / 固定两种模式都走这里）。
    α_u ≤ 1/λmax 保证步进稳定（mini-lab 定标口径）。
    """
    z = list(z0)
    for _ in range(steps):
        y = [0.0] * n
        for u in range(n):
            a = alphas[u]
            if a == 0.0:
                continue
            s = len(adj[u]) * z[u]
            for v in adj[u]:
                s -= z[v]
            y[u] = a * s
        z = [z[u] - y[u] for u in range(n)]
    return z
