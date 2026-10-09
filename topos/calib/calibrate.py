# -*- coding: utf-8 -*-
"""
topos.calib.calibrate —— 解码分数的概率校准（温度 / Platt 缩放）+ ECE。
零依赖：温度 T 与 Platt (A,B) 均用**三分搜索**求最小 NLL（目标对参数单峰）。

契约：解码层只出分数/概率，校准把"排序好的分数"变成"能当概率用的数"——
排序指标（AUC）不受影响，校准只修 ECE。

ADR（E-B2-5 实测）：**默认用 Platt（A·z+B），温度仅作对照/消融**。
纯尺度失校准下温度正确（实测 T=3.174≈真值 3，ECE 降 82.9%），但含系统偏移时
温度只能降 1.1% 而 Platt 降 85.2%——现实中纯尺度失校准罕见。
"""
import math


def sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def _nll(logits, labels, scale=1.0, bias=0.0):
    """缩放后的对数损失。"""
    s = 0.0
    for z, y in zip(logits, labels):
        p = sigmoid(z * scale + bias)
        p = min(max(p, 1e-12), 1 - 1e-12)
        s -= (y * math.log(p) + (1 - y) * math.log(1 - p))
    return s / max(len(logits), 1)


def _ternary_search(fn, lo, hi, iters=120):
    """单峰函数最小化（黄金三分）。"""
    for _ in range(iters):
        m1 = lo + (hi - lo) / 3.0
        m2 = hi - (hi - lo) / 3.0
        if fn(m1) < fn(m2):
            hi = m2
        else:
            lo = m1
    return (lo + hi) / 2.0


def fit_temperature(logits, labels, lo=0.01, hi=50.0):
    """单参数温度 T：p = sigmoid(z / T)。返回 T（乘法形式 scale = 1/T）。"""
    if not logits or len(set(labels)) < 2:
        return 1.0

    def f(scale):
        return _nll(logits, labels, scale=scale)
    scale = _ternary_search(f, 1.0 / hi, 1.0 / lo)
    return 1.0 / scale


def fit_platt(logits, labels, rounds=25):
    """双参数 Platt：p = sigmoid(A·z + B)，坐标下降（交替三分搜索）。"""
    if not logits or len(set(labels)) < 2:
        return 1.0, 0.0
    a, b = 1.0, 0.0
    for _ in range(rounds):
        a = _ternary_search(lambda x: _nll(logits, labels, scale=x, bias=b),
                            -20.0, 20.0, iters=60)
        b = _ternary_search(lambda x: _nll(logits, labels, scale=a, bias=x),
                            -20.0, 20.0, iters=60)
    return a, b


def ece(probs, labels, n_bins=10):
    """期望校准误差（等宽分桶，样本数加权）。"""
    n = len(probs)
    if n == 0:
        return 0.0
    bins = [[] for _ in range(n_bins)]
    for p, y in zip(probs, labels):
        k = min(int(p * n_bins), n_bins - 1)
        bins[k].append((p, y))
    s = 0.0
    for b in bins:
        if not b:
            continue
        mp = sum(p for p, _y in b) / len(b)
        my = sum(y for _p, y in b) / len(b)
        s += abs(mp - my) * len(b) / n
    return s


def apply_temperature(logits, T):
    return [sigmoid(z / T) for z in logits]


def apply_platt(logits, a, b):
    return [sigmoid(a * z + b) for z in logits]
