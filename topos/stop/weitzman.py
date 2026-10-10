# -*- coding: utf-8 -*-
"""
topos.stop.weitzman —— Pandora 盒子保留值 σ 与下一发选择（W4，B4 批）。

⚠️ 最优性声明（PREREG/B4 T-B4-a，架构书 §7.3）：本项目候选池从同一张耦合图切出，
**必然相关**——Weitzman (1979) 的最优性在相关盒子上退化，已知近似界 4.428。
本模块**不承诺最优**，只承诺"优于固定下钻基线"（PREREG/B4 D-B4-1/2 模拟验收）。

停止判据与 σ 定义见 PREREG/B4 §0（锁定）：
- 价值分布 w_j ~ Poisson-Binomial(池成员 belief)（belief 导出）
- σ_j：E[(w_j − σ)⁺] = c_j 的解（数值二分）；c_j ≥ μ_j → σ_j = 0
- 冷启动闭式 [T]：σ_j = μ_j − c_j/θ（仅 t=0，θ 从先验自标定）
- 策略：按 σ 降序开池；STOP ⇔ max(剩余 σ) ≤ max(已开池 belief 均值)
"""
import math

MAX_SIGMA_ITERS = 20      # 二分步数（容差 1e-4）
SIGMA_TOL = 1e-4


def pool_value_mean(pools, belief, exclude=()):
    """各候选池的缺陷期望价值 μ_j = Σ_{i∈m_j} p_i（exclude 的池不算候选）。"""
    out = {}
    for name, members in pools:
        if name in exclude:
            continue
        out[name] = sum(belief.get(i, 0.0) for i in members)
    return out


def _pmf_poisson_binomial(probs):
    """Poisson-Binomial PMF：成员独立 Bernoulli(p_i) 的成功数分布（卷积）。"""
    pmf = [1.0]
    for p in probs:
        pmf = [pmf[0] * (1 - p)] + [pmf[k] * (1 - p) + pmf[k - 1] * p
                                    for k in range(1, len(pmf))] + [pmf[-1] * p]
    return pmf


def sigma_exact(probs, c):
    """保留值 σ：解 E[(w−σ)⁺] = c，w ~ Poisson-Binomial(probs)。

    σ ∈ [0, len(probs)]；c ≥ μ（期望价值）时无正解 → 0.0。
    """
    n = len(probs)
    mu = sum(probs)
    if c <= 0:
        return float(n)
    if c >= mu:
        return 0.0
    pmf = _pmf_poisson_binomial(probs)

    def tail_cost(sig):
        return sum((k - sig) * pk for k, pk in enumerate(pmf) if k > sig)

    lo, hi = 0.0, float(n)                    # tail_cost(0)=μ ≥ c, tail_cost(n)=0 ≤ c
    for _ in range(MAX_SIGMA_ITERS):
        mid = (lo + hi) / 2
        if tail_cost(mid) > c:
            lo = mid
        else:
            hi = mid
        if hi - lo < SIGMA_TOL:
            break
    return (lo + hi) / 2


def sigma_coldstart(mu, c, theta):
    """冷启动闭式 [T]：σ = μ − c/θ（指数族近似，架构书 §7.2）。

    仅用于 t=0（无任何观测）。θ ≤ 0 或 σ ≤ 0 → 0.0（不值得开）。
    """
    if theta <= 0:
        return 0.0
    return max(mu - c / theta, 0.0)


def global_theta(mus, costs):
    """θ = Σμ / Σc（全局发现率，从先验 belief 自标定；Σc=0 → 0）。"""
    sc = sum(costs)
    return (sum(mus) / sc) if sc > 0 else 0.0


def next_pool(pools, sigmas):
    """下一发：argmax σ_j；并列取池宽小者，再并列取输入序。返回 (name, members)。"""
    best = None
    for k, (name, members) in enumerate(pools):
        key = (-sigmas.get(name, 0.0), len(members), k)
        if best is None or key < best[0]:
            best = (key, name, members)
    if best is None or sigmas.get(best[1], 0.0) <= 0.0:
        return None                            # 全部 σ=0 → 无下一发
    return best[1], best[2]


def stop_decision(sigmas, confirmed_value):
    """STOP ⇔ max(剩余 σ) ≤ 已确认价值（已开池的 belief 均值最大者，budget.py 口径）。"""
    if not sigmas:
        return True
    return max(sigmas.values()) <= confirmed_value
