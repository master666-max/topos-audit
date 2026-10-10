# -*- coding: utf-8 -*-
"""
exp_b4_e1 —— E-B4-1 预算-召回模拟：Weitzman 自适应 vs 固定下钻基线（PREREG/B4 §1）。

判据（v1.4 口径 c₀=0.05；v1.1 的 0.5 已废，敏感性 sweep 见 b4_e1_c*.json）：
- D-B4-1（同预算召回更高）：k=8 时 recall_A ≥ max(recall_B, recall_C)
- D-B4-2（同召回预算更省）：达 0.9×recall_A(8) 的首达池数 N_A ≤ N_B 且 ≤ N_C
召回口径：开过的池覆盖到的真缺陷 |dset ∩ ∪opened| / D（控制层视角，解码质量不掺入）。
臂：A=Weitzman 自适应（belief 驱动 σ + 停止）；B=固定随机序（纯深度下钻）；
C=冷启动静态 σ 序（固定排序下钻——区分「σ 排序」与「belief 更新」贡献）。
⚠️ Se/Sp=0.9/0.95 为拍定口径（非 M1 标定），读数以"仪器灵敏度"名义（T-B4-b）。
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
from topos.infer.decode import decode                         # noqa: E402
from topos.stop.budget import run_budget                      # noqa: E402
from topos.stop import weitzman as W                          # noqa: E402

N, D, SE, SP, TRIALS, BUDGET = 300, 8, 0.9, 0.95, 200, 8
COST0_DEFAULT = 0.05                                       # PREREG/B4 v1.4 重标定
COST0 = float(sys.argv[1]) if len(sys.argv) > 1 else COST0_DEFAULT  # sweep 钩子


def recall_cover(opened, dset, pool_map, k=None):
    ks = opened if k is None else opened[:k]
    covered = set()
    for nm in ks:
        covered |= pool_map[nm]
    return len(covered & dset) / D


def main():
    adj = C.gen_graph(N, seed=C.SEED)
    pools = C.narrow_pools(adj, N, seed=C.SEED + 1, n_pools=60)
    pool_map = dict(pools)
    comp_id, _s = C.components(adj, N)
    allowed = {i for i in range(N) if comp_id == 0 or comp_id[i] == 0}
    prior = D / N

    def dec_fn(sub_pools, obs):
        return decode(sub_pools, obs, N, method="nb", se=SE, sp=SP,
                      prior=prior)

    print("E-B4-1 预算-召回模拟：N=%d 池=%d D=%d B=%d c₀=%.2f trials=%d "
          "（Se/Sp=%.2f/%.2f 拍定口径，非 M1 标定）"
          % (N, len(pools), D, BUDGET, COST0, TRIALS, SE, SP))
    curves = {arm: {k: [] for k in range(1, BUDGET + 1)}
              for arm in ("A", "B", "C")}
    stop_dist = []
    for t in range(TRIALS):
        rg = random.Random(C.SEED + 8000 + t * 17)
        dset = C.bfs_cluster(adj, allowed, D, rg)
        oracle = {}
        for nm, m in pools:
            oracle[nm] = (rg.random() < SE) if (m & dset) else (rg.random() >= SP)
        obs_fn = lambda nm, m: oracle[nm]                       # noqa: E731
        # 臂 A：Weitzman 自适应
        tr = run_budget(pools, obs_fn, dec_fn, BUDGET, SE, SP, prior,
                        coldstart=True, cost0=COST0)
        stop_dist.append(len(tr["opened"]))
        for k in range(1, BUDGET + 1):
            curves["A"][k].append(recall_cover(tr["opened"], dset, pool_map, k))
        # 臂 B：固定随机序（深度下钻）
        order_b = [nm for nm, _m in pools]
        rg.shuffle(order_b)
        for k in range(1, BUDGET + 1):
            curves["B"][k].append(recall_cover(order_b, dset, pool_map, k))
        # 臂 C：冷启动静态 σ 序（固定排序下钻）
        prior_belief = {}
        for _nm, m in pools:
            for i in m:
                prior_belief[i] = prior
        mus = W.pool_value_mean(pools, prior_belief)
        theta = W.global_theta(list(mus.values()), [COST0] * len(pools))
        sig0 = {nm: W.sigma_coldstart(mus[nm], COST0, theta)
                for nm, _m in pools}
        order_c = [nm for nm, _s in sorted(sig0.items(),
                                           key=lambda kv: (-kv[1], len(pool_map[kv[0]]), kv[0]))]
        for k in range(1, BUDGET + 1):
            curves["C"][k].append(recall_cover(order_c, dset, pool_map, k))
    mean = {arm: {k: round(statistics.mean(v), 4) for k, v in c.items()}
            for arm, c in curves.items()}
    print("\n预算-召回曲线（均值召回，臂 A 可能提前 STOP → 尾段持平）")
    print("%-4s | %-10s | %-10s | %-10s" % ("k", "A 自适应", "B 随机序", "C 静态σ"))
    print("-" * 46)
    for k in range(1, BUDGET + 1):
        print("%-4d | %-10.4f | %-10.4f | %-10.4f"
              % (k, mean["A"][k], mean["B"][k], mean["C"][k]))
    r8 = {arm: mean[arm][BUDGET] for arm in curves}
    print("-" * 46)
    print("k=8 召回：A=%.4f  B=%.4f  C=%.4f" % (r8["A"], r8["B"], r8["C"]))
    print("A 臂开池数：均值=%.2f 中位=%.1f 自然停止率=%.1f%%"
          % (statistics.mean(stop_dist), statistics.median(stop_dist),
             100 * sum(1 for s in stop_dist if s < BUDGET) / len(stop_dist)))

    def first_k(arm, target):
        for k in range(1, BUDGET + 1):
            if mean[arm][k] >= target:
                return k
        return BUDGET + 99                        # 未达标

    target = 0.9 * r8["A"]
    nA, nB, nC = first_k("A", target), first_k("B", target), first_k("C", target)
    print("目标 %.4f 召回首达池数：A=%s B=%s C=%s" % (target, nA, nB, nC))
    d1 = r8["A"] >= max(r8["B"], r8["C"])
    d2 = (nA <= nB) and (nA <= nC)
    print("D-B4-1（k=8 同预算召回更高）: %s" % ("咬合" if d1 else "不咬合"))
    print("D-B4-2（同召回预算更省）: %s（A=%s ≤ B=%s, C=%s）"
          % ("咬合" if d2 else "不咬合", nA, nB, nC))
    out = {"schema": "b4-e1/1", "n": N, "n_pools": len(pools), "d": D,
           "budget": BUDGET, "cost0": COST0, "trials": TRIALS, "seed": C.SEED,
           "se_sp": [SE, SP], "note_se_sp": "拍定口径，非 M1 标定",
           "curves_mean": mean, "stop_dist_mean": round(statistics.mean(stop_dist), 2),
           "first_k": {"A": nA, "B": nB, "C": nC, "target": round(target, 4)},
           "judged": {"D_B4_1": d1, "D_B4_2": d2}}
    fname = "b4_e1.json" if COST0 == COST0_DEFAULT \
        else "b4_e1_c%s.json" % repr(COST0).replace(".", "_")
    dest = os.path.join(HERE, fname)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)
    return 0 if (d1 and d2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
