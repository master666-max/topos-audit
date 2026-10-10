# -*- coding: utf-8 -*-
"""
topos.stop.budget —— 预算回路（W4，B4 批，架构书 §7.4 控制回路）。

控制循环：σ 排序 → 开池（观测 y）→ belief 重解码 → 剩余 σ 重算 → 停止判据
→ 下一发或 STOP；预算 B 为硬上限（强制 STOP）。

「已确认价值」口径（PREREG/B4 §0）：开池揭示的 y ∈ {0,1} 不揭示池内缺陷数，
故已确认价值取 **belief 更新后已开池的价值均值最大者** max_{j∈opened} μ_j
——Weitzman"已开出的最大 w"在噪声群验下的信念代理。禁止用真值（T-B4-b）。
"""
from topos.stop import weitzman as W


def run_budget(pools, observe_fn, decode_fn, budget, se, sp, prior,
               coldstart=True, cost0=0.05):
    """预算回路。

    pools      : [(name, set)] 全候选池
    observe_fn : (name, members) → y ∈ {0,1}   （观测器：SynthOracle 或真信号源）
    decode_fn  : (pools_subset, obs) → belief   （解码器闭包）
    budget     : B（硬上限）
    cost0      : 一次池检测动作成本（缺陷价值单位，PREREG/B4 v1.4 默认 0.05；
                 v1.1 拍 0.5 与审计语义不齐 → 自适应臂结构性休眠，见 v1.4 修订）

    返回 trace：{"opened": [name...], "y": [...], "beliefs": {t: belief},
                 "stopped_at": t 或 None}
    """
    opened, ys, beliefs = [], [], {}
    stopped_at = None
    for t in range(budget):                    # 开池动作 ≤ budget 次（v1.2）
        remaining = [(nm, m) for nm, m in pools if nm not in set(opened)]
        if not remaining:
            stopped_at = stopped_at if stopped_at is not None else t
            break
        if t == 0 and coldstart:
            # 冷启动：全员先验 belief，闭式 σ（θ 自标定）
            prior_belief = {}
            for _nm, m in pools:
                for i in m:
                    prior_belief[i] = prior
            mus = W.pool_value_mean(pools, prior_belief)
            theta = W.global_theta(list(mus.values()),
                                   [cost0] * len(pools))
            sigmas = {nm: W.sigma_coldstart(mus[nm], cost0, theta)
                      for nm, _m in pools}
        else:
            belief = beliefs[t - 1] if t > 0 else {}
            sigmas = {}
            for nm, m in remaining:
                probs = [belief.get(i, 0.0) for i in m]
                sigmas[nm] = W.sigma_exact(probs, cost0)
        if t > 0:
            # 停止判据自 t≥1 生效（v1.3：STOP ⇔ max(剩余σ) ≤ 0 —— 群验开池不兑现
            # 价值，无 Weitzman"已拿价值"项；σ 已含成本 c₀）
            if W.stop_decision({k: v for k, v in sigmas.items()
                                if k not in set(opened)}, 0.0):
                stopped_at = t
                break
            pick = W.next_pool([(nm, m) for nm, m in remaining
                                if nm in sigmas], sigmas)
        else:
            # t=0 强制开：σ 序；σ 全零按 μ 降序兜底（v1.2）
            pick = W.next_pool(remaining, sigmas)
            if pick is None:
                mus0 = mus if (t == 0 and coldstart) else \
                    W.pool_value_mean(pools, beliefs[t - 1] if t else {})
                cand = sorted(remaining, key=lambda p: (-mus0.get(p[0], 0.0),
                                                        len(p[1]), p[0]))
                pick = (cand[0][0], cand[0][1])
        name, members = pick
        y = observe_fn(name, members)
        opened.append(name)
        ys.append(y)
        obs = [(opened[k], ys[k]) for k in range(len(opened))]
        sub_pools = [(nm, dict(pools)[nm]) for nm in opened]
        beliefs[t] = decode_fn(sub_pools, obs)
    return {"opened": opened, "y": ys, "beliefs": beliefs,
            "stopped_at": stopped_at}
