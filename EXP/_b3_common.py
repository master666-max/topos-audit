# -*- coding: utf-8 -*-
"""
_b3_common —— B3(W5) 实验共享基建（E-B3-1/2/3 共用；下划线=内部件）。

评估统一口径（PREREG/B3 §4）：
- belief 排序 → 秩和 AUC（并列 0.5，decode_mini v2 同式）
- 判阳 ⇔ belief > 0.5（两档分 0.9/0.05 与 NB p>0.5 统一）
- 平衡准确率 = (召回 + 特异度)/2；AUC 与平衡准确率**必须同时报**（§6.3 事故条款）
观测口径：mini-lab EXP-DEC 同式 (rg.random() < Se) if (p & dset) else (rg.random() >= Sp)
（= topos.infer.observe.SynthOracle 采样行）。
"""
import math
import random

SEED = 20261010


# ---------- 合成图：两团块 + 桥边 ----------

def gen_graph(n=300, seed=SEED, bridge=3):
    """两团各 n/2，团内 ER(p=0.06) + 团间 bridge 条桥边。返回 adj(list[set])。"""
    rng = random.Random(seed)
    adj = [set() for _ in range(n)]
    half = n // 2
    for u in range(n):
        lo, hi = (0, half) if u < half else (half, n)
        for v in range(lo, hi):
            if v != u and rng.random() < 0.06:
                adj[u].add(v)
                adj[v].add(u)
    for _ in range(bridge):
        u = rng.randrange(half)
        v = half + rng.randrange(n - half)
        adj[u].add(v)
        adj[v].add(u)
    return adj


def components(adj, n):
    """连通分量编号（0 = 最大分量）。返回 (comp_id, sizes)。"""
    comp = [-1] * n
    sizes = []
    for s in range(n):
        if comp[s] != -1:
            continue
        cid = len(sizes)
        stack, members = [s], []
        comp[s] = cid
        while stack:
            u = stack.pop()
            members.append(u)
            for v in adj[u]:
                if comp[v] == -1:
                    comp[v] = cid
                    stack.append(v)
        sizes.append(len(members))
    big = max(range(len(sizes)), key=lambda k: sizes[k])
    return [cid if cid == big else -2 for cid in comp], sizes


# ---------- 植入（decode_mini 同构） ----------

def bfs_cluster(adj, allowed, d, rng):
    starts = [i for i in allowed if len(adj[i]) >= 2]
    if not starts:
        starts = sorted(allowed)
    cl = {rng.choice(starts)}
    guard = 0
    while len(cl) < d and guard < 5000:
        guard += 1
        cand = [v for u in cl for v in adj[u] if v in allowed and v not in cl]
        if not cand:
            break
        cl.add(cand[rng.randrange(len(cand))])
    return cl


def scatter_set(adj, allowed, d, rng):
    out = set()
    guard = 0
    while len(out) < d and guard < 3000:
        guard += 1
        c = rng.choice(sorted(allowed))
        if all(c not in adj[j] and j not in adj[c] for j in out):
            out.add(c)
    while len(out) < d:
        out.add(rng.choice(sorted(allowed)))
    return out


# ---------- 池构造 ----------

def narrow_pools(adj, n, seed, width_lo=5, width_hi=8, n_pools=60):
    """窄池：BFS 团内采样，宽 5–8（E-B3-1 主口径；E-B3-3 窄池场景 n_pools≥40）。"""
    rng = random.Random(seed)
    comp_id, _sizes = components(adj, n)
    allowed = {i for i in range(n) if comp_id == 0 or comp_id[i] == 0}
    pools = []
    for k in range(n_pools):
        w = rng.randint(width_lo, width_hi)
        cl = bfs_cluster(adj, allowed, w, rng)
        if len(cl) >= 2:
            pools.append(("narrow:%d" % k, set(cl)))
    return pools


def wide_pools(adj, n, seed, n_pools=9, cover_frac=0.32):
    """宽切片池：每池罩住率 ≥cover_frac（E-B3-3 宽池场景；≥30% 判据满足）。"""
    rng = random.Random(seed)
    comp_id, _sizes = components(adj, n)
    nodes = [i for i in range(n) if comp_id == 0 or comp_id[i] == 0]
    w = max(int(len(nodes) * cover_frac), 4)
    pools = []
    starts = [nodes[k * len(nodes) // n_pools] for k in range(n_pools)]
    for k, s in enumerate(starts):
        cl = bfs_cluster(adj, set(nodes), w, random.Random(seed + 77 + k))
        if len(cl) < w:                       # 团内长不满 → 就近补
            rest = [x for x in nodes if x not in cl]
            rng.shuffle(rest)
            cl |= set(rest[:w - len(cl)])
        pools.append(("wide:%d" % k, cl))
    return pools


# ---------- 评估（§4 双指标强制） ----------

def auc_rank(belief, dset, n):
    """秩和 AUC（decode_mini v2 同式，吃 belief dict）。"""
    order = sorted(range(n), key=lambda i: belief[i])
    rank = [0.0] * n
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and belief[order[j + 1]] == belief[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for t in range(i, j + 1):
            rank[order[t]] = avg
        i = j + 1
    d = len(dset)
    rp = sum(rank[i] for i in dset)
    return (rp - d * (d + 1) / 2) / max(d * (n - d), 1)


def trial_eval(belief, dset, n):
    """单 trial 全指标：auc / bal / fnr / fpr（判阳 ⇔ belief > 0.5）。"""
    auc = auc_rank(belief, dset, n)
    rec = sum(1 for i in dset if belief[i] > 0.5) / len(dset)
    neg_n = n - len(dset)
    spec = sum(1 for i in range(n) if i not in dset and belief[i] <= 0.5) / max(neg_n, 1)
    fnr = 1.0 - rec
    fpr = 1.0 - spec
    return {"auc": auc, "bal": (rec + spec) / 2, "fnr": fnr, "fpr": fpr}


def mean(xs):
    return sum(xs) / max(len(xs), 1)


def obs_sample(pools, dset, se, sp, rng):
    """mini-lab EXP-DEC 同式观测（= SynthOracle 采样行）。"""
    return [(nm, (rng.random() < se) if (p & dset) else (rng.random() >= sp))
            for nm, p in pools]
