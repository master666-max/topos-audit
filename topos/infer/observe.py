# -*- coding: utf-8 -*-
"""
topos.infer.observe —— 带噪 OR 观测模型（群验层核心）。
P(y_j = 1 | D) = 1 − Sp + (Se + Sp − 1) · OR_{i∈pool_j}(d_i)   [T] 带噪 OR 标准模型
SynthOracle = 已知真值 + Se/Sp 撒噪（B1 模拟用；真实信号源适配 B2 起）。
搬迁自 mini-lab/decode_mini.run_case 观测行（真仓 8.8× 实验的采样口径）。
"""
import random


def or_prob(pool_members, truth, se, sp):
    """理论 P(y=1)：pool 内有真值单元 → Se；全阴性 → 1−Sp。"""
    hit = any(i in truth for i in pool_members)
    return se if hit else (1.0 - sp)


def sample_observation(pool_members, truth, se, sp, rng):
    """单次带噪观测 ∈ {0,1}。"""
    p = or_prob(pool_members, truth, se, sp)
    return 1 if rng.random() < p else 0


class SynthOracle:
    """模拟观测器：给定真值集与 Se/Sp，逐池采样。"""

    def __init__(self, truth, se=0.9, sp=0.95, seed=20261009):
        self.truth = set(truth)
        self.se, self.sp = float(se), float(sp)
        self.rng = random.Random(seed)

    def observe(self, pool_members):
        return sample_observation(pool_members, self.truth,
                                  self.se, self.sp, self.rng)

    def observe_all(self, pools):
        """[(name, set)] → [(name, y)]。"""
        return [(name, self.observe(members)) for name, members in pools]
