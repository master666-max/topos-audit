# -*- coding: utf-8 -*-
"""
topos.core.fuse —— 多层融合图 w = Σ_t α_t · A_t。
清单的 layers 段给 α（默认全 1.0）；同一对单元落在多层时权重叠加。
"""
from collections import defaultdict

from topos.core.layers import LAYER_TYPES


def fuse(layers, alpha=None):
    """{layer: set[edge]} + {layer: weight} → Dict[edge, float]。

    **A3（2026-10-11）**：键一律归一化为 `(min, max)`。
    call 层已改为有向 `(caller, callee)`，若不归一化，同一对单元的
    call 边 `(i,j)` 与 data 边 `(j,i)` 会被当成两条不同的边，多重度被算漏。
    """
    alpha = alpha or {}
    fused = defaultdict(float)
    for t, edges in layers.items():
        a = float(alpha.get(t, 1.0))
        for e in edges:
            u, v = e
            key = (u, v) if u <= v else (v, u)
            fused[key] += a
    return dict(fused)
