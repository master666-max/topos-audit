# -*- coding: utf-8 -*-
"""
exp_b3_e2 —— E-B3-2 真仓复现：audit-lab 案例口径（PREREG/B3 §2，v1.1）。

主判据 D-B3-2：audit-lab cluster 臂 FNR(COMP)/FNR(NB) ≥ 8
（mini-lab EXP-DEC 同空间实测 8.8× = 37.3% / 4.3%）。
池设计（v1.1 修订）：真仓专用 manifest 宽切片轴池型（罩住率 ~90%+，与 mini-lab 同构），
manifest 落盘 EXP/b3_real_manifest.json 可复核；被测空间本体 = topos.Space 融合图。
"""
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import _b3_common as C                                        # noqa: E402
from topos.space import Space                                 # noqa: E402
from topos.infer.decode import decode                         # noqa: E402

D, SE, SP, TRIALS = 8, 0.9, 0.95, 200
DECODERS = ("comp", "dd", "scomp", "nb")

DEFAULT_AUDIT_LAB = (r"D:\WorkBuddy专用！危险！！！！！！！！"
                     r"\2026-10-08-21-39-17\audit-lab")
DEFAULT_LIBXML = (r"C:\Users\26672\.workbuddy\binaries\python"
                  r"\versions\3.13.12\Lib\xml")

# 宽切片轴池型 manifest（相对分位 → 任意 N 适用；罩住率 = 三分位并集 ≈ 100%）
MANIFEST = {
    "version": 3,
    "layers": {"call": 1.0, "data": 0.5, "control": 0.3, "return": 0.3,
               "vardep": 0.5},
    "fields": [
        {"name": "loc", "layer": "L", "method": "ast",
         "params": {"metric": "lines"}},
        {"name": "forman", "layer": "L", "method": "graph",
         "params": {"formula": "forman_unweighted"}},
    ],
    "slicers": [
        {"name": "loc:lo", "field": "loc", "op": "quantile_le", "q": 0.34},
        {"name": "loc:mid", "field": "loc", "op": "between_q",
         "q_lo": 0.34, "q_hi": 0.67},
        {"name": "loc:hi", "field": "loc", "op": "quantile_gt", "q": 0.67},
        {"name": "curv:lo", "field": "forman", "op": "quantile_le", "q": 0.25},
        {"name": "curv:hi", "field": "forman", "op": "quantile_gt", "q": 0.75},
        {"name": "loc:notlo", "field": "loc", "op": "quantile_gt", "q": 0.2},
    ],
    "pools": [
        {"name": "p_lo", "expr": "loc:lo"},
        {"name": "p_mid", "expr": "loc:mid"},
        {"name": "p_hi", "expr": "loc:hi"},
        {"name": "p_curv_lo", "expr": "curv:lo"},
        {"name": "p_curv_hi", "expr": "curv:hi"},
        {"name": "p_hi_curvlo", "expr": {"all": ["loc:hi", "curv:lo"]}},
        {"name": "p_mid_curvhi", "expr": {"all": ["loc:mid", "curv:hi"]}},
        {"name": "p_lo_curvlo", "expr": {"all": ["loc:lo", "curv:lo"]}},
        {"name": "p_notlo", "expr": "loc:notlo"},
        {"name": "p_notlo_curvlo", "expr": {"all": ["loc:notlo", "curv:lo"]}},
        {"name": "p_hi_or_curvlo", "expr": {"any": ["loc:hi", "curv:lo"]}},
        {"name": "p_mid_or_lo", "expr": {"any": ["loc:mid", "loc:lo"]}},
        {"name": "p_hi_or_mid", "expr": {"any": ["loc:hi", "loc:mid"]}},
    ],
    "constraints": {"max_pool_pct": 0.6, "min_pool_size": 2},
}


def run_case(tag, sp):
    adj = sp.adj
    n = sp.n
    pools = [(nm, set(m)) for nm, m in sp.rows]
    comp_id, _sizes = C.components(adj, n)
    allowed = {i for i in range(n) if comp_id == 0 or comp_id[i] == 0}
    prior = D / n
    cov = sp.coverage
    print("\n[%s] N=%d 池=%d 罩住均值=%.2f 池宽=%s λ 载入中…"
          % (tag, n, len(pools), cov["c_mean"],
             sorted(len(m) for _n, m in pools)[:16]))
    res = {}
    for arm in ("cluster", "scatter"):
        agg = {m: {"auc": [], "bal": [], "fnr": [], "fpr": []} for m in DECODERS}
        for t in range(TRIALS):
            rg = random.Random(C.SEED + 1000 * (arm == "scatter") + t * 17)
            dset = (C.bfs_cluster(adj, allowed, D, rg) if arm == "cluster"
                    else C.scatter_set(adj, allowed, D, rg))
            obs = C.obs_sample(pools, dset, SE, SP, rg)
            for m in DECODERS:
                belief = decode(pools, obs, n, method=m, se=SE, sp=SP,
                                prior=prior)
                ev = C.trial_eval(belief, dset, n)
                for k in agg[m]:
                    agg[m][k].append(ev[k])
        res[arm] = {m: {k: round(statistics.mean(v), 4) for k, v in agg[m].items()}
                    for m in DECODERS}
    for arm in ("cluster", "scatter"):
        print("  [%s]" % arm)
        for m in DECODERS:
            r = res[arm][m]
            print("    %-6s AUC=%.4f bal=%.4f FNR=%.3f FPR=%.3f"
                  % (m, r["auc"], r["bal"], r["fnr"], r["fpr"]))
    ratio = (res["cluster"]["comp"]["fnr"]
             / max(res["cluster"]["nb"]["fnr"], 1e-9))
    print("  D-B3-2 口径比值 FNR(COMP)/FNR(NB) [cluster] = %.1fx" % ratio)
    return res, ratio, {"n": n, "n_pools": len(pools), "c_mean": cov["c_mean"],
                        "c_min": cov["c_min"]}


def main():
    mf_path = os.path.join(HERE, "b3_real_manifest.json")
    with open(mf_path, "w", encoding="utf-8") as f:
        json.dump(MANIFEST, f, ensure_ascii=False, indent=1)
    root_al = os.environ.get("AUDIT_LAB_DIR", DEFAULT_AUDIT_LAB)
    root_xml = os.environ.get("B3_LIBXML_DIR", DEFAULT_LIBXML)
    cases = {}
    ratios = {}
    for tag, root in (("audit-lab", root_al), ("stdlib-xml", root_xml)):
        if not os.path.isdir(root):
            print("[跳过 %s：目录不存在 %s]" % (tag, root))
            continue
        sp = Space(root, mf_path)
        res, ratio, meta = run_case(tag, sp)
        cases[tag] = dict(meta, res=res)
        ratios[tag] = ratio
    ratio_al = ratios.get("audit-lab")
    d32 = ratio_al is not None and ratio_al >= 8
    print("=" * 72)
    print("D-B3-2（audit-lab cluster FNR(COMP)/FNR(NB) ≥ 8）: %s（=%.1fx）"
          % ("咬合" if d32 else "不咬合",
             ratio_al if ratio_al is not None else float("nan")))
    out = {"schema": "b3-e2/1", "d": D, "se": SE, "sp": SP,
           "trials": TRIALS, "seed": C.SEED, "prior": D / 47,
           "manifest": mf_path, "cases": cases,
           "ratio_auditlab_cluster": ratio_al,
           "judged": {"D_B3_2": d32}}
    dest = os.path.join(HERE, "b3_e2.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)
    return 0 if d32 else 1


if __name__ == "__main__":
    raise SystemExit(main())
