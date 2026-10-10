# -*- coding: utf-8 -*-
"""A1/A2 证据（解冻后第一批）：α 是否真的活了 + 新场是否过准入硬门。

对照 `EXP/_b6_s1_alpha_inert.py`（解冻前的"死旋钮"实证）——本脚本跑同一套 α 配置，
但走带 min_weight 的新 to_adj，看边集是否终于不同。
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from topos.core import units as units_mod                              # noqa: E402
from topos.core.layers import _extract_layers, to_adj                  # noqa: E402
from topos.core.fuse import fuse                                       # noqa: E402
from topos.core.embed import forman_curvature                          # noqa: E402
from topos.axis.admission import admit                                 # noqa: E402

TARGET = os.path.join(REPO, "tools", "repos", "dsh-launcher")

us = [u for u in units_mod.discover_units(TARGET)
      if not units_mod.is_test_unit(u)]
L = _extract_layers(TARGET, us)
n = len(us)
print("n_units", n, "layer_edges", {t: len(L.get(t, ())) for t in L})


def eset(adj):
    return {frozenset((u, v)) for u in adj for v in adj[u]}


def curv_sum(adj):
    curv, _ = forman_curvature(adj, n)
    return sum(v for v in curv.values() if v is not None)


# ---------- A1：α 三档 × 阈值 ----------
cfgs = [
    ("全 1.0",        {"call": 1.0, "data": 1.0, "control": 1.0, "return": 1.0, "vardep": 1.0}),
    ("全 0.0",        {"call": 0.0, "data": 0.0, "control": 0.0, "return": 0.0, "vardep": 0.0}),
    ("call=1 余=100", {"call": 1.0, "data": 100.0, "control": 100.0, "return": 100.0, "vardep": 100.0}),
]
print("\n=== A1：α 是否活了（同一 α 配置，min_weight 生效后）===")
print("%-16s %-9s %6s %10s" % ("α 配置", "min_w", "边数", "曲率和"))
for nm, a in cfgs:
    f = fuse(L, a)
    for mw in (None, 2.0):
        adj = to_adj(f, mw)
        print("%-16s %-9s %6d %10d" % (nm, "None" if mw is None else mw,
                                       len(eset(adj)), curv_sum(adj)))

print("\n--- 解冻前（旧 to_adj 语义：只取键、忽略权重）---")
for nm, a in cfgs:
    adj = to_adj(fuse(L, a))
    print("%-16s 边数 %6d 曲率和 %10d  ← 三档全同即为死旋钮"
          % (nm, len(eset(adj)), curv_sum(adj)))

# ---------- A2：逐层场分布 + 准入硬门 ----------
from topos.axis.methods.layer_fields import layer_field   # noqa: E402
span = layer_field(us, {"formula": "span"}, {"layers": L})
gap = layer_field(us, {"formula": "gap"}, {"layers": L})
print("\n=== A2：逐层可观测量分布（dsh %d 单元）===" % n)
print("layer_span 分布:", dict(sorted(Counter(span.values()).items())))
gc = Counter((">0" if v > 0 else ("=0" if v == 0 else "<0")) for v in gap.values())
print("layer_gap 分布:", dict(gc))
print("layer_gap 最大 5 个:", sorted(gap.values(), reverse=True)[:5])

print("\n=== A2 准入硬门（R6：ρ≥0.3 不许准入）===")
def pool_from(field, hi=True, q=0.33):
    """按场值取前 q 分位（或后 q）作为候选池。"""
    vals = sorted((v, i) for i, v in field.items())
    k = max(3, int(len(vals) * q))
    idx = [i for _, i in (vals[-k:] if hi else vals[:k])]
    return idx

existing = [("forman_deep", pool_from(
    {i: (span[i] * -1) for i in range(n)}, hi=True)), ]  # 占位，下面用真实 forman
from topos.core.embed import forman_curvature as _fc     # noqa: E402
adj_all = to_adj(fuse(L, {"call": 1.0, "data": 1.0, "control": 1.0,
                          "return": 1.0, "vardep": 1.0}))
curv, _ = _fc(adj_all, n)
fmap = {i: (curv[i] if curv[i] is not None else 0) for i in range(n)}
base = [("forman_deep", pool_from(fmap, hi=False))]
for nm, cand in (("layer_span_hi", pool_from(span, hi=True)),
                 ("layer_gap_hi", pool_from(gap, hi=True))):
    r = admit(base, (nm, cand), None, 0.8, 0.95)
    print("%-14s dcov=%.3f max_rho=%+.3f rho_pos=%+.3f dlogdet=%s  ⇒ %s"
          % (nm, r["dcov"], r["max_rho"], r["max_rho_pos"],
             ("%.3f" % r["dlogdet"]) if r["dlogdet"] is not None else "None",
             "✅ 准入" if r["max_rho_pos"] < 0.3 else "❌ ρ≥0.3 硬门不许准入"))
