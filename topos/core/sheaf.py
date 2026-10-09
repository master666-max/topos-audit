# -*- coding: utf-8 -*-
"""
topos.core.sheaf —— d=1 符号层 cellular sheaf：H⁰ 亏空 = 不可拼接证词，边级残差 = 定位。
搬迁自 mini-lab/sheaf_mini（X5 三判据咬合件：H⁰ 10/10、残差 10/10、TV 对照 2/10）。

B1 阶段为**合成版**（符号由调用方给定）；真实限制映射语义（declassify/endorse→±1）
依赖 A 轴工单（Q3 裁决），B5 批升级——见 WORK-ORDERS W3。
"""
from topos.core.embed import _jacobi_eig


def sheaf_laplacian(n_nodes, edges_with_sign):
    """edges_with_sign: [(u, v, s)] 方向 u→v；(Bz)_e = z_v − s·z_u。
    返回稠密 L=BᵀB（n×n）。"""
    n = n_nodes
    L = [[0.0] * n for _ in range(n)]
    for u, v, s in edges_with_sign:
        L[u][u] += 1.0
        L[v][v] += 1.0
        L[u][v] += -s
        L[v][u] += -s
    return L


def h0_dimension(L):
    """ker L 维数 = 全局截面 H⁰（能全局自洽拼接的赋值空间）。"""
    vals, _vecs = _jacobi_eig(L, sweeps=60)
    scale = max(abs(v) for v in vals) or 1.0
    return sum(1 for v in vals if abs(v) < 1e-8 * scale)


def residuals(n_nodes, edges_with_sign, z):
    """边残差 (Bz)_e² 与节点残差能 r_v = Σ_{e∋v} (Bz)_e²。"""
    e_res = {}
    r = {v: 0.0 for v in range(n_nodes)}
    for u, v, s in edges_with_sign:
        c = (z[v] - s * z[u]) ** 2
        e_res[(u, v)] = c
        r[u] += c
        r[v] += c
    return e_res, r


def tv_residuals(adj, z):
    """对照：普通全变差残差（符号盲——X5c 实测对语义矛盾结构性看不见）。"""
    r = {v: 0.0 for v in adj}
    for u, nbrs in adj.items():
        for v in nbrs:
            c = (z[u] - z[v]) ** 2
            r[u] += c
            r[v] += c
    return r
