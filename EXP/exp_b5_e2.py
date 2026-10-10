# -*- coding: utf-8 -*-
"""
exp_b5_e2 —— E-B5-2 真实接缝定位（PREREG/B5 §2）：规则表 v0.1 全链跑真仓。

靶①：topos-audit 自身 `topos/**/*.py`（吃狗粮，按包前缀过滤）；
靶②：audit-lab（`../../2026-10-08-21-39-17/audit-lab`，B3-E2 同款真仓）。

读数（PREREG §B 结构）：否决项清单 / 翻转边清单（R2·R3）/ 分量 H⁰（多节点分量）/
残差定位 / 人工核验清单（D-B5-2b 抽查输出）。[U] 读数——不冒充 [M]（T-B5-b）。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

from topos.core import seams                                  # noqa: E402
from topos.core import sheaf                                  # noqa: E402

AUDIT_LAB = os.path.normpath(os.path.join(
    REPO, "..", "..", "2026-10-08-21-39-17", "audit-lab"))


def _components(n, e_ws):
    """无向连通分量（sheaf 图底层）。返回 [[node...]...]（每分量升序）。"""
    adj = {i: set() for i in range(n)}
    for u, v, _s in e_ws:
        adj[u].add(v)
        adj[v].add(u)
    seen, comps = set(), []
    for s0 in sorted(adj):
        if s0 in seen:
            continue
        comp, stack = [], [s0]
        seen.add(s0)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in sorted(adj[x]):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        comps.append(sorted(comp))
    return comps


def analyze(name, repo_dir, prefix=None):
    """全链：抽取 → 过滤 → 分量 H⁰ → 残差。返回报告字典。"""
    modules, edges, vetoes = seams.extract(repo_dir)
    if prefix:
        edges = [e for e in edges if e[0].startswith(prefix)
                 and e[1].startswith(prefix)]
        vetoes = [v for v in vetoes if v[0].replace("\\", "/")
                  .startswith(prefix.replace(".", "/") + "/")]
        modules = [m for m in modules if m.startswith(prefix)]
    idx = {m: i for i, m in enumerate(modules)}
    e_ws = [(idx[u], idx[v], s) for u, v, a, s, ev in edges]
    n = len(modules)
    z = {i: 1.0 for i in range(n)}
    _e, r_sheaf = sheaf.residuals(n, e_ws, z) if e_ws else ({}, {i: 0.0 for i in range(n)})
    comps = [c for c in _components(n, e_ws) if len(c) > 1]
    comp_report = []
    for c in comps:
        rel = {g: k for k, g in enumerate(c)}
        sub = [(rel[u], rel[v], s) for u, v, s in e_ws
               if u in rel and v in rel]
        L = sheaf.sheaf_laplacian(len(c), sub)
        h0 = sheaf.h0_dimension(L)
        node_set = set(c)
        comp_flip = [{"edge": "%s -> %s" % (u, v),
                      "action": a, "evidence": ev}
                     for u, v, a, s, ev in edges
                     if s == -1 and idx[u] in node_set and idx[v] in node_set]
        comp_report.append({"nodes": [modules[i] for i in c], "h0": h0,
                            "frustrated": h0 == 0,
                            "flip_edges": comp_flip if h0 == 0 else []})
    flip = [{"src": u, "dst": v, "action": a, "evidence": ev}
            for u, v, a, s, ev in edges if s == -1]
    top = sorted(range(n), key=lambda i: (-r_sheaf.get(i, 0.0), i))[:10]
    rep = {"repo": name, "n_modules": len(modules), "n_edges": len(edges),
           "edges_by_action": {a: sum(1 for e in edges if e[2] == a)
                               for a in {e[2] for e in edges}},
           "vetoes": [{"at": v[0], "call": v[1], "detail": v[2]}
                      for v in vetoes],
           "flip_edges": flip,
           "components": comp_report,
           "top_residual": [{"module": modules[i], "residual":
                             round(r_sheaf.get(i, 0.0), 2)} for i in top
                            if r_sheaf.get(i, 0.0) > 0]}
    return rep


def main():
    print("E-B5-2 真实接缝定位（规则表 v0.1 [U]，非合成用例）")
    print("=" * 70)
    reps = []
    ok = True
    for name, path, prefix in (("topos-audit/topos", REPO, "topos."),
                               ("audit-lab", AUDIT_LAB, None)):
        if not os.path.isdir(path):
            print("跳过 %s（目录不存在：%s）" % (name, path))
            continue
        rep = analyze(name, path, prefix)
        reps.append(rep)
        print("\n■ %s：模块 %d，接缝边 %d %s，否决项 %d"
              % (name, rep["n_modules"], rep["n_edges"],
                 rep["edges_by_action"], len(rep["vetoes"])))
        for v in rep["vetoes"]:
            print("  [VETO] %s  %s  %s" % (v["at"], v["call"], v["detail"]))
        print("  分量（多节点）：")
        for c in rep["components"]:
            tag = " ← 不可拼接（H⁰=0）" if c["frustrated"] else ""
            print("    ker=%d  %s%s" % (c["h0"], ", ".join(c["nodes"]), tag))
            for fe in c["flip_edges"]:
                for at, det in fe["evidence"]:
                    print("      翻转边 %s  @%s  %s" % (fe["edge"], at, det))
        frus_pairs = {(fe["edge"], fe["action"])
                      for c in rep["components"] if c["frustrated"]
                      for fe in c["flip_edges"]}
        lonely = [fe for fe in rep["flip_edges"]
                  if (fe["src"] + " -> " + fe["dst"], fe["action"])
                  not in frus_pairs]
        if lonely:
            print("  树挂翻转边（不在奇环上，仍是契约越界）：")
            for fe in lonely:
                for at, det in fe["evidence"]:
                    print("    %s → %s (%s)  @%s  %s"
                          % (fe["src"], fe["dst"], fe["action"], at, det))
    n_frus = sum(1 for r in reps for c in r["components"] if c["frustrated"])
    n_flip = sum(len(r["flip_edges"]) for r in reps)
    print("\n" + "=" * 70)
    print("D-B5-2a（≥1 真实奇环分量 ker=0）：%d 个 → %s"
          % (n_frus, "咬合" if n_frus >= 1 else "不咬合"))
    print("D-B5-2b（翻转边人工抽查 ≥3 条，误报 ≤1/3）：候选 %d 条 → 人工核验见回执"
          % n_flip)
    out = {"schema": "b5-e2/1", "repos": reps,
           "n_frustrated_components": n_frus, "n_flip_edges": n_flip,
           "judged": {"D_B5_2a": n_frus >= 1, "D_B5_2b": None}}
    dest = os.path.join(HERE, "b5_e2.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
