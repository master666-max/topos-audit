# -*- coding: utf-8 -*-
"""
topos.axis.methods.random_fields —— 随机对照场。方法注册名 "random"。
v3 哲学下场与切片分离：random 场 = 每单元一个固定种子的均匀随机数；
对照切片由清单里的 quantile 切片定义（不再是 v0.2 里直接撒随机池）。
"""
import random

from topos.axis.registry import field_method


@field_method("random")
def random_field(units, params, ctx):
    seed = int(params.get("seed", 20261009))
    rng = random.Random(seed)
    return {i: rng.random() for i in range(len(units))}
