# -*- coding: utf-8 -*-
"""
_crosscheck.py —— 参考件接口对拍（一次性校验，不进运行时）。

对拍三件：
  A. Forman 边曲率：mini-lab 手写（c=4-deg(u)-deg(v)，1d 单位权） vs GraphRicciCurvature.FormanRicci(method="1d")
  B. 拉普拉斯矩阵：coord_mini._matvec_L 逐列 vs scipy.sparse.csgraph.laplacian
  C. λ2 数值：scipy eigsh（dense L 与 LinearOperator 两路互证）
测试图：karate club（34 节点，标准基准）+ mini-lab 自身调用图（真仓口径）。
"""
import importlib.util
import json
import os
import sys

import numpy as np
import networkx as nx
from scipy.sparse import csgraph
from scipy.sparse.linalg import eigsh, LinearOperator

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
MINI = os.path.join(os.path.dirname(TOP), "mini-lab")  # mini-lab 在工作区根
sys.path.insert(0, MINI)
sys.path.insert(0, os.path.join(HERE, "GraphRicciCurvature"))

import coord_mini as cm  # noqa: E402

# shim：python-louvain 装不上（pip 源问题），FormanRicci 只用 util 的 logger/set_verbose，louvain 是死依赖
import types as _types
_fake_comm = _types.ModuleType("community")
_fake_cl = _types.ModuleType("community.community_louvain")
_fake_comm.community_louvain = _fake_cl
sys.modules["community"] = _fake_comm
sys.modules["community.community_louvain"] = _fake_cl

from GraphRicciCurvature.FormanRicci import FormanRicci  # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + "  |  " + detail)


# ---------- 测试图 ----------

def karate():
    G = nx.karate_club_graph()
    G = nx.Graph((u, v) for u, v in G.edges())  # 去掉 weight 属性（GC 会自动走加权路径）
    G = nx.relabel.convert_node_labels_to_integers(G)
    adj = {i: set(G.neighbors(i)) for i in G.nodes()}
    return G, adj, len(adj)


def minilab_callgraph():
    units = cm.discover_units(MINI)
    adj_full = cm.build_call_graph(units)
    n = len(units)
    adj = {i: set(adj_full.get(i, ())) | {v for v in range(n) if i in adj_full.get(v, ())}
           for i in range(n)}
    G = nx.from_dict_of_lists({i: sorted(adj[i]) for i in range(n)} if False else
                              {i: sorted(j for j in adj[i]) for i in range(n)})
    G.remove_edges_from(nx.selfloop_edges(G))
    G = nx.convert_node_labels_to_integers(G)
    adj = {i: set(G.neighbors(i)) for i in G.nodes()}
    return G, adj, len(adj)


# ---------- A: Forman 对拍 ----------

def forman_check(tag, G, adj, n):
    node_curv, edge_curv = cm.forman_curvature(adj, n)
    F = FormanRicci(G, method="1d", verbose="ERROR")
    F.compute_ricci_curvature()
    gc = nx.get_edge_attributes(F.G, "formanCurvature")
    if not gc:
        check("A/%s Forman 边曲率" % tag, False, "GC 未输出 formanCurvature 属性")
        return
    diffs = [abs(mine - gc.get((u, v), gc.get((v, u)))) for (u, v), mine in edge_curv.items()
             if gc.get((u, v), gc.get((v, u))) is not None]
    total = len(diffs)
    maxd = max(diffs) if diffs else float("inf")
    sample = [(u, v, mine, gc.get((u, v), gc.get((v, u))))
              for (u, v), mine in list(edge_curv.items())[:5]]
    detail = "%d/%d 边对比, max|Δ|=%.2e; 样例(mine vs GC): %s" % (
        total, len(edge_curv), maxd,
        "; ".join("(%d,%d) %s vs %s" % s for s in sample))
    check("A/%s Forman 边曲率" % tag, total == len(edge_curv) and maxd < 1e-9, detail)


# ---------- B: matvec ≡ L ----------

def laplacian_check(tag, adj, n):
    A = np.zeros((n, n))
    for u in adj:
        for v in adj[u]:
            A[u, v] = 1.0
    L_ref = csgraph.laplacian(A, normed=False)
    L_mine = np.column_stack([
        cm._matvec_L(adj, [1.0 if i == col else 0.0 for i in range(n)], n)
        for col in range(n)])
    maxd = float(np.max(np.abs(L_ref - L_mine)))
    check("B/%s matvec≡L" % tag, maxd < 1e-12, "max|Δ|=%.2e" % maxd)
    return L_ref


# ---------- C: λ2 ----------

def lambda2_check(tag, L, adj, n):
    vals_dense = eigsh(L, k=2, which="SA", return_eigenvectors=False)
    l2_dense = float(np.sort(vals_dense)[0])  # 升序后第一个非平凡（λ1≈0 在更前？k=2 即 λ1,λ2）
    l2_dense = float(np.sort(vals_dense)[1]) if abs(np.sort(vals_dense)[0]) < 1e-9 \
        else float(np.sort(vals_dense)[0])
    op = LinearOperator((n, n), matvec=lambda x: cm._matvec_L(adj, list(map(float, x)), n),
                        dtype=float)
    vals_op = eigsh(op, k=2, which="SA", return_eigenvectors=False)
    so = np.sort(vals_op)
    l2_op = float(so[1]) if abs(so[0]) < 1e-9 else float(so[0])
    dd = abs(l2_dense - l2_op)
    check("C/%s λ2 两路一致" % tag, dd < 1e-8,
          "dense=%.6f operator=%.6f Δ=%.2e" % (l2_dense, l2_op, dd))
    return l2_dense


def main():
    for tag, builder in (("karate", karate), ("mini-lab", minilab_callgraph)):
        G, adj, n = builder()
        print("== 图: %s (N=%d, E=%d) ==" % (tag, n, G.number_of_edges()))
        forman_check(tag, G, adj, n)
        L = laplacian_check(tag, adj, n)
        lambda2_check(tag, L, adj, n)
    print()
    ok = sum(1 for _, s, _ in results if s)
    print("总判定: %d/%d PASS" % (ok, len(results)))
    with open(os.path.join(HERE, "crosscheck-result.json"), "w", encoding="utf-8") as f:
        json.dump([{"name": a, "pass": b, "detail": c} for a, b, c in results],
                  f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
