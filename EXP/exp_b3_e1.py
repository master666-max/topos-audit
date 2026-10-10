# -*- coding: utf-8 -*-
"""
exp_b3_e1 —— E-B3-1 合成图四解码器对照（PREREG/B3 §1，v1.1）。

判据：
- D-B3-1a：COMP/DD/SCOMP/NB 全部产出 AUC + 平衡准确率读数（数字即读数）。
- D-B3-1b：cluster 臂 NB 的 AUC ≥ DD 的 AUC。
口径：n=300 两团图、窄池（宽 5–8 × 60）、D=8、Se=0.9、Sp=0.95、200 trials、种子 20261010。
stdlib-only。
"""
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))                     # topos 包根
sys.path.insert(0, HERE)

import _b3_common as C                                        # noqa: E402
from topos.infer.decode import decode                         # noqa: E402

N, D, SE, SP, TRIALS = 300, 8, 0.9, 0.95, 200
DECODERS = ("comp", "dd", "scomp", "nb")


def main():
    adj = C.gen_graph(N, seed=C.SEED)
    pools = C.narrow_pools(adj, N, seed=C.SEED + 1, n_pools=60)
    comp_id, _sizes = C.components(adj, N)
    allowed = {i for i in range(N) if comp_id == 0 or comp_id[i] == 0}
    print("E-B3-1 合成对照：N=%d 池=%d（宽 5-8） D=%d Se=%.2f Sp=%.2f trials=%d"
          % (N, len(pools), D, SE, SP, TRIALS))
    prior = D / N
    res = {}
    for arm in ("cluster", "scatter"):
        agg = {m: {"auc": [], "bal": [], "fnr": [], "fpr": []} for m in DECODERS}
        for t in range(TRIALS):
            rg = random.Random(C.SEED + 100 * (arm == "scatter") + t * 17)
            dset = (C.bfs_cluster(adj, allowed, D, rg) if arm == "cluster"
                    else C.scatter_set(adj, allowed, D, rg))
            obs = C.obs_sample(pools, dset, SE, SP, rg)
            for m in DECODERS:
                belief = decode(pools, obs, N, method=m, se=SE, sp=SP,
                                prior=prior)
                ev = C.trial_eval(belief, dset, N)
                for k in agg[m]:
                    agg[m][k].append(ev[k])
        res[arm] = {m: {k: round(statistics.mean(v), 4)
                        for k, v in agg[m].items()} for m in DECODERS}
    # 报表（双指标强制：AUC + 平衡准确率同表）
    print("\n%-8s | %-24s | %-24s | %-14s" % ("臂", "AUC（排序质量）", "平衡准确率", "FNR / FPR"))
    print("-" * 80)
    for arm in ("cluster", "scatter"):
        for m in DECODERS:
            r = res[arm][m]
            print("%-8s | %-24s | %-24s | %.3f / %.3f"
                  % (arm if m == "comp" else "",
                     "%s=%.4f" % (m, r["auc"]),
                     "bal=%.4f" % r["bal"], r["fnr"], r["fpr"]))
        print("-" * 80)
    # 判据
    d1a = all(len(res[a][m]) == 4 for a in res for m in DECODERS)
    d1b = res["cluster"]["nb"]["auc"] >= res["cluster"]["dd"]["auc"]
    print("D-B3-1a（四解码器读数齐全）: %s" % ("咬合" if d1a else "不咬合"))
    print("D-B3-1b（cluster 臂 AUC_NB %.4f ≥ AUC_DD %.4f）: %s"
          % (res["cluster"]["nb"]["auc"], res["cluster"]["dd"]["auc"],
             "咬合" if d1b else "不咬合"))
    out = {"schema": "b3-e1/1", "n": N, "n_pools": len(pools), "d": D,
           "se": SE, "sp": SP, "trials": TRIALS, "seed": C.SEED,
           "prior": prior, "res": res,
           "judged": {"D_B3_1a": d1a, "D_B3_1b": d1b}}
    dest = os.path.join(HERE, "b3_e1.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)
    return 0 if (d1a and d1b) else 1


if __name__ == "__main__":
    raise SystemExit(main())
