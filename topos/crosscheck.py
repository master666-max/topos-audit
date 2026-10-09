# -*- coding: utf-8 -*-
"""
topos.crosscheck —— 对拍钩子：topos 手写件 vs 外部参考件（MIT/BSD，reference/ 内源码）。
  ① Forman 边曲率：topos.core.embed.forman_curvature vs GraphRicciCurvature(method="1d")
  ② λ₂：dense 拉普拉斯 eigsh vs LinearOperator(_matvec_L) eigsh
依赖 scipy/networkx（仅此命令；无则如实报跳过，不进运行时红线）。
基线：mini-lab 目录 154 边 max|Δ|=0、λ₂ Δ≤3.8e-15（reference/crosscheck-result.json）。
"""
import os
import sys
import types

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_GC = os.path.join(BASE, "reference", "GraphRicciCurvature")


def _load_gc():
    """加载 GraphRicciCurvature.FormanRicci；python-louvain 缺失用假模块 shim
    （FormanRicci 只用 util 的 logger/set_verbose，louvain 是死依赖）。"""
    try:
        import networkx  # noqa: F401
    except ImportError:
        return None, "networkx 未安装"
    sys.path.insert(0, REF_GC)
    if "community" not in sys.modules:
        fake = types.ModuleType("community")
        fake_cl = types.ModuleType("community.community_louvain")
        fake.community_louvain = fake_cl
        sys.modules["community"] = fake
        sys.modules["community.community_louvain"] = fake_cl
    try:
        from GraphRicciCurvature.FormanRicci import FormanRicci  # noqa: F401
        return FormanRicci, None
    except Exception as e:
        return None, str(e)


def crosscheck_dir(root, manifest_path=None):
    """返回 [(name, ok, detail)]；对拍口径与 reference/_crosscheck.py 相同。"""
    import numpy as np
    import networkx as nx
    from scipy.sparse import csgraph
    from scipy.sparse.linalg import eigsh, LinearOperator

    from topos.space import Space
    from topos.core.embed import forman_curvature, _matvec_L

    sp = Space(root, manifest_path)
    n = sp.n
    adj = {i: set(sp.adj.get(i, ())) for i in range(n)}
    results = []

    # ① Forman
    FormanRicci, err = _load_gc()
    if FormanRicci is None:
        results.append(("① Forman 对拍", None, "跳过: %s" % err))
    else:
        G = nx.from_dict_of_lists({i: sorted(adj[i]) for i in range(n)})
        G.remove_edges_from(nx.selfloop_edges(G))
        G = nx.convert_node_labels_to_integers(G)
        adj_g = {i: set(G.neighbors(i)) for i in G.nodes()}
        _, edge_curv = forman_curvature(adj_g, len(adj_g))
        F = FormanRicci(G, method="1d", verbose="ERROR")
        F.compute_ricci_curvature()
        gc = nx.get_edge_attributes(F.G, "formanCurvature")
        diffs = [abs(mine - gc.get(e, gc.get((e[1], e[0]))))
                 for e, mine in edge_curv.items()
                 if gc.get(e, gc.get((e[1], e[0]))) is not None]
        maxd = max(diffs) if diffs else float("inf")
        ok = len(diffs) == len(edge_curv) and maxd < 1e-9
        results.append(("① Forman 边曲率", ok,
                        "%d/%d 边, max|Δ|=%.2e" % (len(diffs), len(edge_curv), maxd)))

    # ② λ₂ 两路
    A = np.zeros((n, n))
    for u in adj:
        for v in adj[u]:
            A[u, v] = 1.0
    L = csgraph.laplacian(A, normed=False)
    op = LinearOperator((n, n),
                        matvec=lambda x: _matvec_L(adj, list(map(float, x)), n),
                        dtype=float)
    vd = np.sort(eigsh(L, k=2, which="SA", return_eigenvectors=False))
    vo = np.sort(eigsh(op, k=2, which="SA", return_eigenvectors=False))
    l2d = float(vd[1]) if abs(vd[0]) < 1e-9 else float(vd[0])
    l2o = float(vo[1]) if abs(vo[0]) < 1e-9 else float(vo[0])
    dd = abs(l2d - l2o)
    results.append(("② λ₂ 两路一致", dd < 1e-8,
                    "dense=%.6f operator=%.6f Δ=%.2e" % (l2d, l2o, dd)))
    return results
