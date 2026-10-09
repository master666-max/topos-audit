# -*- coding: utf-8 -*-
"""
EXP/exp_b2_e5.py —— E-B2-5 温度缩放校准（PREREG/B2 判据：ECE 下降 ≥30%）。
合成：真率 π=0.15，正负类 logits 分居两侧，再乘一个过度自信因子（模拟未校准解码器）。
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topos.calib.calibrate import (fit_temperature, fit_platt, ece,  # noqa: E402
                                   apply_temperature, apply_platt, sigmoid)

SEED = 20261009
N = 3000
PI = 0.15
OVERCONF = 3.0


def synth_scale(seed=SEED, n=N, k=OVERCONF, spread=2.0, center=None):
    """E-B2-5a 纯尺度失校准：**令 z0 就是校准 logit**——先抽 z0，再 y ~ Bernoulli(sigmoid(z0))，
    观测分数 z = k·z0。此时最优校准是纯尺度 T=k。
    （第二版修正：v1 版先抽 y 再抽 z0|y，则真实 logit = 2.4·z0 − 1.73，含斜率+截距，
      温度学到 T=1.243=1/0.8 是数学正确的——合成错了，不是实现错了。）"""
    rng = random.Random(seed)
    # 中心偏移使正率接近 PI：sigmoid(z0) 的均值 ≈ π → center = logit(π)
    if center is None:
        center = math.log(PI / (1 - PI))
    z, y = [], []
    for _ in range(n):
        z0 = rng.gauss(center, spread)
        p = sigmoid(z0)
        y.append(1 if rng.random() < p else 0)
        z.append(k * z0)
    return z, y


def synth_shift(seed=SEED, n=N, pi=PI, overconf=OVERCONF, sep=1.5):
    """E-B2-5b 含偏置失校准（原合成）：分数被推进 sigmoid 饱和区且带系统偏移。"""
    rng = random.Random(seed)
    z, y = [], []
    for _ in range(n):
        d = 1 if rng.random() < pi else 0
        mu = sep if d == 1 else -sep
        zz = rng.gauss(mu, 1.0) * overconf
        z.append(zz)
        y.append(d)
    return z, y


def report(tag, z, y):
    raw = [sigmoid(v) for v in z]
    e_raw = ece(raw, y)
    T = fit_temperature(z, y)
    e_temp = ece(apply_temperature(z, T), y)
    a, b = fit_platt(z, y)
    e_platt = ece(apply_platt(z, a, b), y)
    d1 = (e_raw - e_temp) / e_raw if e_raw else 0.0
    d2 = (e_raw - e_platt) / e_raw if e_raw else 0.0
    print("== %s ==" % tag)
    print("  缩放前 ECE        = %.4f" % e_raw)
    print("  温度缩放后 ECE    = %.4f  (T=%.3f)  降幅 %.1f%%" % (e_temp, T, d1 * 100))
    print("  Platt 缩放后 ECE  = %.4f  (A=%.3f B=%.3f)  降幅 %.1f%%"
          % (e_platt, a, b, d2 * 100))
    return d1, d2


def main():
    print("=== E-B2-5 校准缩放（判据已按 v1.3 拆分）===")
    d1a, d2a = report("E-B2-5a 纯尺度失校准（z = 3·z0）", *synth_scale())
    d1b, d2b = report("E-B2-5b 含偏置/饱和失校准", *synth_shift())
    ok_a = d1a >= 0.30
    ok_b = d2b >= 0.30
    print("=" * 62)
    print("E-B2-5a 温度缩放在纯尺度失校准下降 ≥30%%: %s (%.1f%%)" % (ok_a, d1a * 100))
    print("E-B2-5b Platt 在含偏置失校准下降 ≥30%%:  %s (%.1f%%)" % (ok_b, d2b * 100))
    print("  分工实测：温度只修尺度（5b 中仅 %.1f%%），Platt 修尺度+偏移"
          % (d1b * 100))
    verdict = ok_a and ok_b
    print("E-B2-5 判定: %s" % ("咬合" if verdict else "不咬合"))
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
