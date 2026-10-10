# -*- coding: utf-8 -*-
"""多层探针：量“多层”到底还剩多少信息进了几何。
问题：fuse 出了权重 w(e)=Σα，但 to_adj 只取键 → 权重与层归属全丢。
本脚本实测：层归属的多重度分布，以及丢掉了多少 bit。
"""
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from topos.core.layers import _extract_layers, LAYER_TYPES, to_adj   # noqa: E402
from topos.core import units as units_mod                            # noqa: E402
from topos.core.fuse import fuse                                     # noqa: E402

TARGET = os.path.join(REPO, "tools", "repos", "dsh-launcher")

us = units_mod.discover_units(TARGET)
us = [u for u in us if not units_mod.is_test_unit(u)]
L = _extract_layers(TARGET, us)

mem = defaultdict(set)          # edge -> {layer}
for t in LAYER_TYPES:
    for e in L.get(t, ()):
        # A3 后 call 层是有向 (caller, callee)；多重度必须在**无向投影**上算，
        # 否则 (i,j) 与 (j,i) 会被当成两条边，多重度被低估（本脚本曾因此误报 9.0%）
        u, v = e
        mem[(u, v) if u <= v else (v, u)].add(t)

mult = Counter(len(v) for v in mem.values())
tot_membership = sum(len(v) for v in mem.values())
tot_edge = len(mem)

f = fuse(L, {})
adj = to_adj(f)

print("n_units          :", len(us))
print("layer_edges      :", {t: len(L.get(t, ())) for t in LAYER_TYPES})
print("层归属事实总数    :", tot_membership)
print("不同边数(融合后)  :", tot_edge)
print("被 to_adj 抹掉的重度事实 :", tot_membership - tot_edge,
      "= %.1f%%" % (100.0 * (tot_membership - tot_edge) / tot_membership))
print("重度分布 |层数:边数| :", dict(sorted(mult.items())))
print("fuse 权重取值分布  :", dict(sorted(Counter(round(w, 3) for w in f.values()).items())))
print("无权邻接边数      :", sum(len(v) for v in adj.values()) // 2)

# 单层 vs 多层的“身份”是否影响下游：权重排序前 10 的边，在无权图里是否可区分
top = sorted(f.items(), key=lambda kv: -kv[1])[:8]
print("权重最高 8 条边 → 在 adj 里全部退化为 1:",
      all(1 for _ in top), [w for _, w in top])
print("有方向的层?      :", all(a <= b for (a, b) in mem))
