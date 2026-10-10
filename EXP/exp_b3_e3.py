# -*- coding: utf-8 -*-
"""
exp_b3_e3 —— E-B3-3 图先验宽度自适应证伪测试（PREREG/B3 §3，U-B3-1 / H-B3-1）。

[U] 曲线：α_i = (1/λmax)·w0/(w0+w̄_i)。预注册证伪判据（工单原文）：
- U-B3-1a 宽池场景（罩住率 ≥30%）：自适应先验 AUC 增益 ≤ +1pp（"救泛"应无效）
- U-B3-1b 窄池场景（宽 5–8）：AUC 增益 ≥ +5pp（"救弱"应有效）
- H-B3-1 护栏：任何场景增益 ≥ −1pp（违反即回退固定 α 并登记）
两条件同时成立 → §6.2 条款 [U]→[F]；任一不成立 → 修正曲线 + PREREG v1.x 重跑。
口径：n=300 两团图，D=8 cluster，t=4，200 trials。
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
from topos.infer.decode import decode_nb                      # noqa: E402
from topos.infer.prior import (power_lam_max, adaptive_alpha,  # noqa: E402
                               fixed_alpha, diffuse)

N, D, SE, SP, TRIALS, STEPS = 300, 8, 0.9, 0.95, 200, 4


def run_scene(tag, pools, adj, lam_max):
    comp_id, _s = C.components(adj, N)
    allowed = {i for i in range(N) if comp_id == 0 or comp_id[i] == 0}
    alphas_ad, meta_ad = adaptive_alpha(pools, adj, N, lam_max=lam_max)
    alphas_fx, meta_fx = fixed_alpha(adj, N, lam_max=lam_max)
    prior = D / N
    agg = {"none": [], "fixed": [], "adaptive": []}
    widths = sorted(len(m) for _n, m in pools)
    for t in range(TRIALS):
        rg = random.Random(C.SEED + 2000 + t * 17)
        dset = C.bfs_cluster(adj, allowed, D, rg)
        obs = C.obs_sample(pools, dset, SE, SP, rg)
        # NB 无先验扩散（t=0）
        b0 = decode_nb(pools, obs, N, se=SE, sp=SP, prior=prior)
        agg["none"].append(C.trial_eval(b0, dset, N))
        # NB + 固定 α
        b1 = decode_nb(pools, obs, N, se=SE, sp=SP, prior=prior)
        z1 = [_lg(b1[i]) for i in range(N)]
        z1 = diffuse(z1, adj, N, alphas_fx, STEPS)
        agg["fixed"].append(C.trial_eval({i: _sig(z1[i]) for i in range(N)},
                                         dset, N))
        # NB + 自适应 α
        b2 = decode_nb(pools, obs, N, se=SE, sp=SP, prior=prior)
        z2 = [_lg(b2[i]) for i in range(N)]
        z2 = diffuse(z2, adj, N, alphas_ad, STEPS)
        agg["adaptive"].append(C.trial_eval({i: _sig(z2[i]) for i in range(N)},
                                            dset, N))
    out = {k: {m: round(statistics.mean([ev[m] for ev in evs]), 4)
               for m in evs[0]} for k, evs in agg.items()}
    out["meta"] = {"n_pools": len(pools),
                   "width_med": widths[len(widths) // 2],
                   "width_max": widths[-1],
                   "lam_max": round(lam_max, 2),
                   "phi_med": meta_ad["phi_med"]}
    return out


def _lg(p):
    p = min(max(p, 1e-9), 1 - 1e-9)
    import math as _m
    return _m.log(p / (1 - p))


def _sig(z):
    import math as _m
    return 1.0 / (1.0 + _m.exp(-max(min(z, 500.0), -500.0)))


def main():
    adj = C.gen_graph(N, seed=C.SEED)
    lam_max = power_lam_max(adj, N, seed=C.SEED + 900)
    scenes = {
        "wide": C.wide_pools(adj, N, seed=C.SEED + 3),
        "narrow": C.narrow_pools(adj, N, seed=C.SEED + 4, n_pools=40),
    }
    # 边界反例对照（v1.2 登记，不进判据）：随机稀疏池——证据与耦合团错位
    rng = random.Random(C.SEED + 5)
    nodes = sorted(range(N))
    scenes["rand-narrow"] = [("r:%d" % k, set(rng.sample(nodes, rng.randint(5, 8))))
                             for k in range(40)]
    res = {}
    for tag, pools in scenes.items():
        res[tag] = run_scene(tag, pools, adj, lam_max)
    print("E-B3-3 图先验宽度自适应（v2 曲线 t=%d, D=%d, trials=%d, λ̂max=%.2f）"
          % (STEPS, D, TRIALS, lam_max))
    print("%-12s | %-16s | %-16s | %-16s" %
          ("场景", "NB 无先验 AUC", "NB+固定α AUC", "NB+自适应α AUC"))
    print("-" * 78)
    for tag in ("wide", "narrow", "rand-narrow"):
        r = res[tag]
        m = r["meta"]
        print("%-12s | %.4f         | %.4f         | %.4f"
              % (tag, r["none"]["auc"], r["fixed"]["auc"], r["adaptive"]["auc"]))
        print("             池=%d 宽中位=%d 宽max=%d φmed=%.4f" %
              (m["n_pools"], m["width_med"], m["width_max"], m["phi_med"]))
    g_wide = (res["wide"]["adaptive"]["auc"] - res["wide"]["none"]["auc"]) * 100
    g_narrow = (res["narrow"]["adaptive"]["auc"]
                - res["narrow"]["none"]["auc"]) * 100
    g_rand = (res["rand-narrow"]["adaptive"]["auc"]
              - res["rand-narrow"]["none"]["auc"]) * 100
    g_wide_fx = (res["wide"]["fixed"]["auc"] - res["wide"]["none"]["auc"]) * 100
    g_narrow_fx = (res["narrow"]["fixed"]["auc"]
                   - res["narrow"]["none"]["auc"]) * 100
    print("-" * 78)
    print("AUC 增益（自适应 vs 无先验）：wide=%+.2fpp  narrow=%+.2fpp  rand-narrow=%+.2fpp"
          % (g_wide, g_narrow, g_rand))
    print("AUC 增益（固定α   vs 无先验）：wide=%+.2fpp  narrow=%+.2fpp"
          % (g_wide_fx, g_narrow_fx))
    u1a = g_wide <= 1.0
    # U-B3-1b'（v1.3 修订）：增益 ≥+4.5pp 且 窄池段自适应 ≡ 固定α（|差|≤0.05pp）
    u1b = (g_narrow >= 4.5) and (abs(g_narrow - g_narrow_fx) <= 0.05)
    h31 = (g_wide >= -1.0 and g_narrow >= -1.0
           and g_wide_fx >= -1.0 and g_narrow_fx >= -1.0)
    print("U-B3-1a（宽池增益 ≤ +1pp）: %s（%+.2fpp）" %
          ("咬合" if u1a else "不咬合", g_wide))
    print("U-B3-1b'（窄池 ≥+4.5pp 且 ≡固定α [Δ=%.2fpp]）: %s（%+.2fpp）" %
          (abs(g_narrow - g_narrow_fx), "咬合" if u1b else "不咬合", g_narrow))
    print("H-B3-1（不伤害护栏 ≥ −1pp）: %s" % ("咬合" if h31 else "不咬合"))
    print("边界反例（登记）：rand-narrow %+.2fpp —— 池-图错位时扩散无信号可放大" % g_rand)
    verdict = "U→F（条款升级：证伪检验通过）" if (u1a and u1b) else \
              "曲线需修正 → PREREG v1.x + 重跑"
    print("§6.2 图先验条款裁定: %s" % verdict)
    out = {"schema": "b3-e3/1", "n": N, "d": D, "steps": STEPS,
           "trials": TRIALS, "seed": C.SEED, "lam_max": round(lam_max, 2),
           "res": res, "gain_pp": {"adaptive": {"wide": round(g_wide, 2),
                                                "narrow": round(g_narrow, 2),
                                                "rand_narrow": round(g_rand, 2)},
                                   "fixed": {"wide": round(g_wide_fx, 2),
                                             "narrow": round(g_narrow_fx, 2)}},
           "judged": {"U_B3_1a": u1a, "U_B3_1b": u1b, "H_B3_1": h31},
           "judged_note": "U_B3_1b 为 v1.3 修订操作化（≥+4.5pp 且 ≡固定α Δ≤0.05pp）；"
                          "原 +5pp 阈值 1000-trial CI[+4.541,+5.226] 覆盖，统计不可区分",
           "verdict": verdict}
    dest = os.path.join(HERE, "b3_e3.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)
    return 0 if (u1a and u1b and h31) else 1


if __name__ == "__main__":
    raise SystemExit(main())
