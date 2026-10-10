# -*- coding: utf-8 -*-
"""
exp_b5_e1 —— E-B5-1 新语义保持实验（PREREG/B5 §1）：规则表 v0.1 产符号 + sheaf 读数，
X5 三判据口径移植（X5a′ H⁰ / X5b′ 残差定位 / X5c′ TV 对照）+ R4 否决项无误报。

fixture：5 模块合成仓（显式模板 + 种子化 decoy），奇数 trial 用 R2 翻转闭环、偶数 trial
用 R3 翻转闭环、balanced 组全 R1 环——三种植入方式都要过判据，防止"只对一种符号成立"。
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import _b3_common as C                                        # noqa: E402
from topos.core import seams                                  # noqa: E402
from topos.core import sheaf                                  # noqa: E402

TRIALS = 10

_TPL = {
    "m_a.py": (
        "import m_b\nimport m_c\nimport m_d\nimport m_e\nimport pickle\n"
        "def go(x):\n"
        "    {cycle_edge}\n"
        "    m_c.pub(x)\n"
        "    {decoys}\n"
        "    m_d.CACHE.append(x)\n"
        "    m_d.REG[k] = 1\n"
        "    eval(x)\n"
        "    pickle.loads(b'z')\n"
        "def go2(x):\n    return x\n"
        "k = 'key'\n"
    ),
    "m_b.py": (
        "SINK = {{}}\n"
        "import m_c\n"
        "def _helper(x):\n    return x\n"
        "def open_api(x):\n    return x\n"
        "def bridge(x):\n    m_c.pub(x)\n"
    ),
    "m_c.py": "import m_a\ndef pub(x):\n    m_a.go2(x)\n",
    "m_d.py": "CACHE = []\nREG = {{}}\n",
    "m_e.py": "def pub(x):\n    return x\n",
}

CYCLE = {
    "r2": "m_b._helper(x)",                        # R2 翻转闭环
    "r3": "m_b.SINK[k] = x",                       # R3 翻转闭环
    "bal": "m_b.open_api(x)",                      # R1 平衡环
}
DECOY_POOL = ["m_e.pub(x)", "m_b.open_api(x)", "m_b.bridge(x)", "m_c.pub(x)"]


def build_repo(w, mode, rng):
    os.makedirs(w, exist_ok=True)
    decos = rng.sample(DECOY_POOL, rng.randint(0, 3))
    tpl = {name: body for name, body in _TPL.items()}
    tpl["m_a.py"] = _TPL["m_a.py"].format(
        cycle_edge=CYCLE[mode],
        decoys="\n    ".join(decos))
    tpl["m_b.py"] = _TPL["m_b.py"].format()
    tpl["m_d.py"] = _TPL["m_d.py"].format()
    for name, body in tpl.items():
        with open(os.path.join(w, name), "w", encoding="utf-8") as f:
            f.write(body)
    return w


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


def seam_component_h0(n, e_ws, has_flip):
    """PREREG §B 分量读数：取承载接缝的分量（frustrated=含翻转边的分量；
    balanced=最大多节点分量），孤立单模块分量平凡 ker=1 不进判读。"""
    comps = [c for c in _components(n, e_ws) if len(c) > 1]
    if not comps:
        return None, 0
    flip_nodes = {u for u, v, s in e_ws if s == -1} | \
                 {v for u, v, s in e_ws if s == -1}
    if has_flip:
        target = next((c for c in comps if flip_nodes & set(c)), None)
    else:
        target = max(comps, key=len)
    if target is None:
        return None, 0
    rel = {g: k for k, g in enumerate(target)}
    sub = [(rel[u], rel[v], s) for u, v, s in e_ws
           if u in rel and v in rel]
    L = sheaf.sheaf_laplacian(len(target), sub)
    return target, sheaf.h0_dimension(L)


def one_trial(w, mode, rng):
    """跑单 trial，返回读数字典。"""
    for fn in os.listdir(w):
        os.remove(os.path.join(w, fn))
    build_repo(w, mode, rng)
    modules, edges, vetoes = seams.extract(w)
    idx = {m: i for i, m in enumerate(modules)}
    e_ws = [(idx[u], idx[v], s) for u, v, a, s, ev in edges]
    n = len(modules)
    z = {i: 1.0 for i in range(n)}
    e_res, r_sheaf = sheaf.residuals(n, e_ws, z)
    r_tv = sheaf.tv_residuals({i: set() for i in range(n)}, z)
    flip_edges = [(u, v) for u, v, a, s, ev in edges if s == -1]
    f = len(flip_edges)
    top = set(sorted(range(n), key=lambda i: (-r_sheaf[i], i))[:max(1, 2 * f)])
    hit = all((idx[u] in top or idx[v] in top) for u, v in flip_edges) \
        if f else True
    tv_hit = sum(1 for v in r_tv.values() if v > 0)
    veto_ok = len(vetoes) == 1 and vetoes[0][1] == "eval"
    comp, h0_seam = seam_component_h0(n, e_ws,
                                      has_flip=any(s == -1 for _, _, s in e_ws))
    return {"h0": h0_seam, "comp_size": len(comp) if comp else 0,
            "flip_hit": hit, "f": f, "n_flip_edges": len(flip_edges),
            "tv_nonzero": tv_hit, "veto_ok": veto_ok,
            "n_edges": len(edges), "n_modules": n}


def main():
    w = os.path.join(HERE, "_b5_repo")
    os.makedirs(w, exist_ok=True)
    rows = {"r2": [], "r3": [], "bal": []}
    for t in range(TRIALS):
        rg = random.Random(C.SEED + 500 + t * 13)
        rows["r2" if t % 2 == 0 else "r3"].append(
            one_trial(w, "r2" if t % 2 == 0 else "r3", rg))
        rows["bal"].append(one_trial(w, "bal", rg))
    a_frus = sum(1 for r in rows["r2"] + rows["r3"] if r["h0"] == 0)
    a_bal = sum(1 for r in rows["bal"] if r["h0"] == 1)
    b_hit = sum(1 for r in rows["r2"] + rows["r3"] if r["flip_hit"])
    c_sep = sum(1 for r in rows["r2"] + rows["r3"] if r["tv_nonzero"] <= 3)
    d_ok = sum(1 for r in rows["r2"] + rows["r3"] + rows["bal"]
               if r["veto_ok"])
    n_frus, n_bal = len(rows["r2"]) + len(rows["r3"]), len(rows["bal"])
    print("E-B5-1 新语义保持（规则表 v0.1 产符号，X5 口径）trial=%d×3 组"
          % TRIALS)
    print("-" * 60)
    print("D-B5-1a H⁰：frustrated ker=0 %d/%d ｜ balanced ker=1 %d/%d"
          % (a_frus, n_frus, a_bal, n_bal))
    print("D-B5-1b 残差定位（翻转边端点 ∈ top-2f）：%d/%d" % (b_hit, n_frus))
    print("D-B5-1c TV 对照分离（≤3/10 口径，此处 z≡+1 预期全盲）：%d/%d"
          % (c_sep, n_frus))
    print("D-B5-1d R4 否决项（恰 1 条 eval、零误报）：%d/%d"
          % (d_ok, n_frus + n_bal))
    d1 = (a_frus == n_frus and a_bal == n_bal)
    d2 = (b_hit == n_frus)
    d3 = (c_sep == n_frus)
    d4 = (d_ok == n_frus + n_bal)
    print("-" * 60)
    print("D-B5-1a: %s ｜ D-B5-1b: %s ｜ D-B5-1c: %s ｜ D-B5-1d: %s"
          % ("咬合" if d1 else "不咬合", "咬合" if d2 else "不咬合",
             "咬合" if d3 else "不咬合", "咬合" if d4 else "不咬合"))
    out = {"schema": "b5-e1/1", "trials_per_group": TRIALS,
           "modes": list(rows), "rows": rows,
           "judged": {"D_B5_1a": d1, "D_B5_1b": d2, "D_B5_1c": d3,
                      "D_B5_1d": d4}}
    dest = os.path.join(HERE, "b5_e1.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)
    return 0 if (d1 and d2 and d3 and d4) else 1


if __name__ == "__main__":
    raise SystemExit(main())
