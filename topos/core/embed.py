# -*- coding: utf-8 -*-
"""
topos.core.embed —— 图上连续量：连通分量 / Forman 曲率 / 零依赖 Lanczos 扩散嵌入。
搬迁自 mini-lab/coord_mini（E1 咬合件：λ₂ 残差 1e-7 / N=2000 2.2s；selftest 11/11）。
对外部锚的对拍见 reference/_crosscheck.py（6/6：154 边曲率零差、λ₂ Δ≤3.8e-15）。

地位（E-X1 v3/v4 双判据不咬合后的降级决议）：嵌入坐标是**仪表**（可视化/邻接查询），
不进入池设计控制回路。
"""
import math
import random
from collections import defaultdict

SEED = 20261009


def components(adj, n):
    """并查集连通分量 → ([comp_id per unit], [sizes desc])。"""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for u, nbrs in adj.items():
        for v in nbrs:
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv
    comp = defaultdict(int)
    for i in range(n):
        comp[find(i)] += 1
    sizes = sorted(comp.values(), reverse=True)
    roots = sorted(comp.keys(), key=lambda r: -comp[r])
    comp_id = {}
    for rank, r in enumerate(roots):
        comp_id[r] = rank
    return [comp_id[find(i)] for i in range(n)], sizes


def forman_curvature(adj, n):
    """1d 单位权 Forman：c(e) = 4 − deg(u) − deg(v)；节点曲率 = min(邻边)。
    与 GraphRicciCurvature method="1d" 精确一致（154 边对拍 max|Δ|=0）。"""
    node_curv = {}
    edge_curv = {}
    for u in range(n):
        vals = []
        for v in adj.get(u, ()):
            c = 4 - len(adj.get(u, ())) - len(adj.get(v, ()))
            edge_curv[(min(u, v), max(u, v))] = c
            vals.append(c)
        node_curv[u] = min(vals) if vals else None
    return node_curv, edge_curv


# ---------------- 零依赖谱件（Lanczos m=80 全重正交化 + Jacobi 对角化 T） ----------------

def _matvec_L(adj, x, n):
    """y = L·x，L = D − A（与 scipy csgraph.laplacian 逐列零差）。"""
    y = [0.0] * n
    for u in range(n):
        s = len(adj[u]) * x[u]
        for v in adj[u]:
            s -= x[v]
        y[u] = s
    return y


def _jacobi_eig(A, sweeps=60):
    n = len(A)
    a = [row[:] for row in A]
    V = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    scale = max(1.0, max(abs(a[i][i]) for i in range(n)))
    for _ in range(sweeps):
        off = sum(a[p][q] ** 2 for p in range(n - 1) for q in range(p + 1, n))
        if off < 1e-18 * scale * scale:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                apq = a[p][q]
                if abs(apq) < 1e-13 * scale:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * apq)
                t = 1.0 / (abs(theta) + math.sqrt(theta * theta + 1.0))
                if theta < 0:
                    t = -t
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for i in range(n):
                    aip, aiq = a[i][p], a[i][q]
                    a[i][p] = c * aip - s * aiq
                    a[i][q] = s * aip + c * aiq
                rowp, rowq = a[p], a[q]
                for i in range(n):
                    api, aqi = rowp[i], rowq[i]
                    rowp[i] = c * api - s * aqi
                    rowq[i] = s * api + c * aqi
                for i in range(n):
                    vip, viq = V[i][p], V[i][q]
                    V[i][p] = c * vip - s * viq
                    V[i][q] = s * vip + c * viq
    vals = [a[i][i] for i in range(n)]
    order = sorted(range(n), key=lambda r: vals[r])
    return [vals[r] for r in order], [[V[i][r] for r in order] for i in range(n)]


def diffusion_embedding(adj, n, k=3, m_steps=80, seed=SEED):
    """Lanczos(m=80, 全重正交化) → 扩散嵌入 coords（距离=传播时间）。
    返回 (coords: {i: [k 维]}, used, lam_residual=|λ₁|)。λ₁≈0 的残差即谱件质量读数。"""
    rng = random.Random(seed)
    V = []
    v = [rng.gauss(0, 1) for _ in range(n)]
    nr = math.sqrt(sum(p * p for p in v))
    V.append([p / nr for p in v])
    alphas, betas = [], []
    beta_prev = 0.0
    for j in range(m_steps):
        w = _matvec_L(adj, V[j], n)
        alpha = sum(p * q for p, q in zip(V[j], w))
        alphas.append(alpha)
        w = [wi - alpha * V[j][i] for i, wi in enumerate(w)]
        if j > 0:
            w = [wi - beta_prev * V[j - 1][i] for i, wi in enumerate(w)]
        for c in range(j + 1):
            vc = V[c]
            d = sum(p * q for p, q in zip(vc, w))
            if d != 0.0:
                for i in range(n):
                    w[i] -= d * vc[i]
        beta = math.sqrt(sum(p * p for p in w))
        if j == m_steps - 1 or beta < 1e-12:
            break
        betas.append(beta)
        V.append([p / beta for p in w])
        beta_prev = beta
    ms = len(alphas)
    T = [[0.0] * ms for _ in range(ms)]
    for i in range(ms):
        T[i][i] = alphas[i]
        if i + 1 < ms and i < len(betas):
            T[i][i + 1] = T[i + 1][i] = betas[i]
    vals, vecs = _jacobi_eig(T)
    coords = {i: [] for i in range(n)}
    used = 0
    for r in range(ms):
        theta = vals[r]
        if theta < 1e-6:
            continue
        if used >= k:
            break
        coef = [vecs[j][r] for j in range(ms)]
        for i in range(n):
            coords[i].append(sum(coef[j] * V[j][i] for j in range(ms)))
        used += 1
    return coords, used, vals[0]
