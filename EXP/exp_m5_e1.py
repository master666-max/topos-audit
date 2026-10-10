# -*- coding: utf-8 -*-
"""
exp_m5_e1 —— E-M5-1 非 Python 链（PREREG/M5 §1）：express lib/ 全链跑通。

链路：langjs 抽取 → Space(lang=js) → space CLI → anchors 观测 → decode → next
→ seams→sheaf 无虚假证词检查。判据 D-M5-1a/b/c（PREREG §1）。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

from topos.core import langjs                                # noqa: E402
from topos.core import sheaf                                 # noqa: E402
from topos.cli import main as cli_main                       # noqa: E402

TARGET = os.path.join(REPO, "tools", "repos", "express-master", "lib")
OUT = os.path.join(HERE, "m5_e1")

#: JS 危险信号锚点（v0.1 最小集，对齐 anchors-bandit 精神）
JS_ANCHORS = [
    ["sink:eval", r"\beval\s*\("],
    ["sink:newFunction", r"\bnew\s+Function\s*\("],
    ["sink:exec", r"\bchild_process\b|\bexecSync\s*\(|\bspawnSync\s*\("],
    ["sink:fsSyncWrite", r"\bwriteFileSync\s*\(|\bappendFileSync\s*\("],
    ["sink:weakHash", r"createHash\s*\(\s*['\"]md5|sha1['\"]"],
]


def main():
    os.makedirs(OUT, exist_ok=True)
    # ① 抽取读数
    units = langjs.discover_units_js(TARGET)
    layers = langjs.extract_layers_js(TARGET, units)
    seams_js, vetoes = langjs.extract_seams_js(TARGET, units)
    req_edges = [e for e in seams_js if e[2] == "public_call"]
    files = sorted({u["file"] for u in units})
    print("E-M5-1 非 Python 链（express lib/，JS 后端 [U]）")
    print("=" * 64)
    print("① 抽取：文件 %d ｜ 单元 %d ｜ call 边 %d ｜ require 边 %d ｜ veto %d"
          % (len(files), len(units), len(layers["call"]), len(req_edges),
             len(vetoes)))
    d1a = len(units) >= 10 and len(req_edges) >= 6      # PREREG/M5 v1.1（实测 6=地面真值）
    print("D-M5-1a（单元 ≥10 且 require 边 ≥6，v1.1 实测口径）：%s"
          % ("咬合" if d1a else "不咬合"))

    # ② manifest（forman 分位切片 + 锚点场 notnull 池）
    mf = {
        "version": 3,
        "layers": {"call": 1.0},
        "fields": [
            {"name": "forman", "method": "graph",
             "params": {"formula": "forman_unweighted"}},
            {"name": "anchor", "method": "regex",
             "params": {"patterns": JS_ANCHORS}},
        ],
        "slicers": [
            {"name": "curv:lo", "field": "forman", "op": "quantile_le",
             "q": 0.34},
            {"name": "curv:hi", "field": "forman", "op": "quantile_gt",
             "q": 0.5},
            {"name": "anchor:any", "field": "anchor", "op": "notnull"},
        ],
        "pools": [{"name": "p_curv_lo", "expr": "curv:lo"},
                  {"name": "p_curv_hi", "expr": "curv:hi"},
                  {"name": "p_anchor", "expr": "anchor:any"}],
        "constraints": {"max_pool_pct": 0.6, "min_pool_size": 2},
    }
    mf_path = os.path.join(OUT, "manifest_js.json")
    with open(mf_path, "w", encoding="utf-8") as f:
        json.dump(mf, f, ensure_ascii=False, indent=1)

    # ③ space CLI（--lang js）
    sj = os.path.join(OUT, "space.json")
    rc_space = cli_main(["space", TARGET, "--axes", mf_path, "--json", sj,
                         "--lang", "js"])
    with open(sj, encoding="utf-8") as f:
        rep = json.load(f)
    print("② space CLI rc=%d ｜ 池 %s ｜ 单元 %d"
          % (rc_space, list(rep["pool_members"]), rep["n_units"]))

    # ④ anchors → obs.json（池内有锚点命中单元 → y=1，确定性信号）
    pats = [(t, re.compile(rx)) for t, rx in JS_ANCHORS]
    unit_hits = {i: [t for t, p in pats if p.search(u["src"])]
                 for i, u in enumerate(units)}
    hit_n = sum(1 for v in unit_hits.values() if v)
    obs = {}
    for nm, members in rep["pool_members"]:
        obs[nm] = 1 if any(unit_hits.get(i) for i in members) else 0
    oj = os.path.join(OUT, "obs.json")
    with open(oj, "w", encoding="utf-8") as f:
        json.dump(obs, f)
    print("③ anchors：命中单元 %d/%d ｜ obs=%s" % (hit_n, len(units), obs))

    # ⑤ decode → next
    bj = os.path.join(OUT, "belief.json")
    rc_dec = cli_main(["decode", sj, "--obs", oj, "--decoder", "nb",
                       "-o", bj])
    rc_next = cli_main(["next", sj, bj]) if rc_dec == 0 else 1
    with open(bj, encoding="utf-8") as f:
        bel = json.load(f)
    top = sorted(bel["belief"].items(), key=lambda kv: -kv[1])[:3]
    print("④ decode rc=%d ｜ next rc=%d ｜ belief top3=%s"
          % (rc_dec, rc_next,
             [(u_id.split("::")[1] if "::" in u_id else u_id, round(p, 4))
              for u_id, p in top]))
    d1b = (rc_space == 0 and rc_dec == 0 and rc_next == 0)
    print("D-M5-1b（三 CLI 全链零退出）：%s" % ("咬合" if d1b else "不咬合"))

    # ⑥ sheaf 无虚假证词（JS 规则 v0.1 全 +1 → 不允许 ker=0）
    idx = {u["file"]: i for i, u in enumerate(
        sorted(units, key=lambda u: u["file"]))}
    mod_names = sorted({u["file"] for u in units})
    m_idx = {m: i for i, m in enumerate(mod_names)}
    e_ws = [(m_idx[u], m_idx[v], s) for u, v, a, s, ev in seams_js]
    adj = {i: set() for i in range(len(mod_names))}
    for u, v, _s in e_ws:
        adj[u].add(v)
        adj[v].add(u)
    seen, frus, comps_n = set(), 0, 0
    for s0 in sorted(adj):
        if s0 in seen:
            continue
        comp, st = [], [s0]
        seen.add(s0)
        while st:
            x = st.pop()
            comp.append(x)
            for y in sorted(adj[x]):
                if y not in seen:
                    seen.add(y)
                    st.append(y)
        if len(comp) < 2:
            continue
        comps_n += 1
        rel = {g: k for k, g in enumerate(sorted(comp))}
        sub = [(rel[u], rel[v], s) for u, v, s in e_ws
               if u in rel and v in rel]
        L = sheaf.sheaf_laplacian(len(comp), sub)
        if sheaf.h0_dimension(L) == 0:
            frus += 1
    d1c = (frus == 0)
    print("⑤ sheaf：多节点分量 %d ｜ frustrated %d（JS 规则 v0.1 全 +1 下必须 0）"
          % (comps_n, frus))
    print("D-M5-1c（sheaf 无虚假证词 + veto 抽查）：%s" %
          ("咬合" if d1c else "不咬合"))
    if vetoes:
        for at, sym, det in vetoes:
            print("    [VETO] %s  %s  %s" % (at, sym, det))

    out = {"schema": "m5-e1/1", "target": "express lib/",
           "n_files": len(files), "n_units": len(units),
           "n_call_edges": len(layers["call"]),
           "n_require_edges": len(req_edges), "n_vetoes": len(vetoes),
           "anchor_hit_units": hit_n, "obs": obs,
           "components": comps_n, "frustrated": frus,
           "judged": {"D_M5_1a": d1a, "D_M5_1b": d1b, "D_M5_1c": d1c}}
    dest = os.path.join(HERE, "m5_e1.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)
    return 0 if (d1a and d1b and d1c) else 1


if __name__ == "__main__":
    raise SystemExit(main())
