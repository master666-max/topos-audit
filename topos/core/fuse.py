# -*- coding: utf-8 -*-
"""
topos.core.fuse —— 多层融合图 w = Σ_t α_t · A_t。
清单的 layers 段给 α（默认全 1.0）；同一对单元落在多层时权重叠加。
"""
from collections import defaultdict

from topos.core.layers import LAYER_TYPES


def fuse(layers, alpha=None):
    """{layer: set[edge]} + {layer: weight} → Dict[edge, float]。"""
    alpha = alpha or {}
    fused = defaultdict(float)
    for t, edges in layers.items():
        a = float(alpha.get(t, 1.0))
        for e in edges:
            fused[e] += a
    return dict(fused)
