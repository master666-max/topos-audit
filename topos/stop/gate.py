# -*- coding: utf-8 -*-
"""
topos.stop.gate —— 覆盖率前置门（B7 §1.1，三态 NEXT/STOP/BLOCKED-COVERAGE）。

**为什么必须有这道门**：`infer/decode.py:98` 的 `z = [lp] * n` ⇒ **零票单元的后验恒等于先验**。
仪器对那部分代码说的一切"没问题"都是**先验的回声，不是观测的结论**；而 σ 回路会在这种
状态下庄严宣布"不必再审"（RUN1：zcr=0.904 仍输出 STOP）。见 `PREREG/B7.md` §0。

**契约（B7 §1.1，锁定）**：

- `zero_cover_rate > θ_cov` ⇒ **BLOCKED-COVERAGE**（既不是 NEXT 也不是 STOP）
- θ_cov **见数据前写死 = 0.30**，只许收紧不许放宽（T-B7-a）
- θ_cov 缺失或非法 ⇒ **raise**，不给默认值（对齐"缺失即 bug，不存在可选优化"）
- BLOCKED-COVERAGE **不是失败态也不是观察态**，它是一个**有内容的结论**：
  "以当前设计矩阵，本仪器无权对未覆盖部分下任何判断"

**本模块不碰**：σ 公式、解码器、抽取器（B7 §1.3 防混轴）。
"""
import math

THETA_COV_DEFAULT = 0.30          # B7 §1.1 见数据前写死；只许收紧
DEFAULT_CONSTRAINTS = {"max_width": 400, "max_width_pct": 0.03,
                       "max_pools": 64, "min_pool_size": 3}

VERDICT_BLOCKED = "BLOCKED-COVERAGE"
VERDICT_PASS = "PASS"


def _check_theta(theta_cov):
    if theta_cov is None:
        raise ValueError("θ_cov 缺失：不许静默回落给默认值（B7 §1.1）")
    if isinstance(theta_cov, bool) or not isinstance(theta_cov, (int, float)):
        raise ValueError("θ_cov 必须是数值，实为 %r" % (theta_cov,))
    t = float(theta_cov)
    if not (0 < t <= 1):
        raise ValueError("θ_cov 必须落在 (0, 1]，实为 %r" % (theta_cov,))
    return t


def _effective_width(n, constraints):
    """单池可覆盖单元数的上界 W：min(max_width, ceil(max_width_pct·n))，下限 min_pool_size。"""
    c = constraints or DEFAULT_CONSTRAINTS
    mw = int(c.get("max_width", DEFAULT_CONSTRAINTS["max_width"]))
    pct = float(c.get("max_width_pct", DEFAULT_CONSTRAINTS["max_width_pct"]))
    lo = int(c.get("min_pool_size", DEFAULT_CONSTRAINTS["min_pool_size"]))
    return max(lo, min(mw, max(1, int(math.ceil(pct * n)))))


def coverage_gate(coverage, n_units, theta_cov, constraints=None):
    """覆盖率前置门。

    coverage  : Space.coverage 同形 dict，必须含 `zero_cover_rate`
    n_units   : 单元总数
    theta_cov : **必填**，无默认（缺即 raise）
    constraints: {max_width, max_width_pct, min_pool_size}（缺省用 DEFAULT_CONSTRAINTS）

    返回 dict：verdict / theta_cov / zero_cover_rate / zero_cover_units /
    covered_units / pools_needed_lower_bound。
    """
    theta = _check_theta(theta_cov)
    if not isinstance(coverage, dict) or "zero_cover_rate" not in coverage:
        raise ValueError("coverage 必须含 zero_cover_rate（缺字段即 bug）")
    zcr = float(coverage["zero_cover_rate"])
    n = int(n_units)
    U = int(round(zcr * n))                       # 未覆盖单元数
    C = max(0, n - U)                             # 已覆盖（至少被 1 个池碰到）
    W = _effective_width(n, constraints)
    lower_bound = int(math.ceil(U / float(W))) if U else 0
    return {
        "verdict": VERDICT_BLOCKED if zcr > theta else VERDICT_PASS,
        "theta_cov": theta,
        "zero_cover_rate": zcr,
        "zero_cover_units": U,
        "covered_units": C,
        "n_units": n,
        "effective_width": W,
        "pools_needed_lower_bound": lower_bound,
    }


def gate_line(g):
    """一行人话结论（供 CLI 与报告首行复用）。"""
    if g["verdict"] == VERDICT_BLOCKED:
        return ("本次审计未覆盖 %.1f%%（%d 个单元），以下结论**不适用于**该部分。"
                % (100.0 * g["zero_cover_rate"], g["zero_cover_units"]))
    return ("本次审计未覆盖 %.1f%%（%d 个单元）。"
            % (100.0 * g["zero_cover_rate"], g["zero_cover_units"]))
