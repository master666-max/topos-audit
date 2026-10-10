# -*- coding: utf-8 -*-
"""
topos.axis.methods.layer_fields —— **多层可观测量**（L 层 · 逐层进场层）。

**A2（2026-10-11，解冻后第一批 · DEFERRED-REGISTRY 岗位三）**

此前 `Space.layers`（五类耦合边）**只有 `summary()` 里的一个诊断标量与它有关**，
零个场读它 ⇒ `ARCHITECTURE.md` §2「多层图」这个核心命题**没有对应算子**。
本模块把"某单元在第 t 层上是什么角色"变成可被切片、可被池引用的**标量场**。

方法注册名 `"layer"`，参数 `formula`：

| formula | 含义 | 取值 |
|---|---|---|
| `deg:<层名>`（或缺省=`deg:call`） | 该单元在指定层上的度（第 t 层邻居数） | int ≥ 0 |
| `span` | 该单元参与了几类层（0–5） | int 0–5 |
| `gap` | `(deg_data + deg_vardep) − deg_call`：**数据/变量耦合强于调用耦合**的程度 | int（可为负） |

**为什么 `gap` 是岗位三要的那把刀**：正 gap = 这个单元在 call 层是叶子（几乎没人调它），
却在 data / vardep 层上是枢纽（一堆单元通过共享状态与它耦合）。这正是
「跨层失配」的可观测形态，也是 clone 型缺陷（复制粘贴体互不调用）唯一可能在图上
显形的地方。

诚实边界（[U]，按 R7 带证伪判据）：
- 这些场是**描述子**，不是检测器。它们是否真的提升检出，由 B6 的 D-B6-1..5 判定。
- 准入必须过 `topos axis-admit` 三读数（Δcov / 正相关 ρ / Δlogdet）；ρ≥0.3 为硬门（R6）。
- 层名非法 ⇒ 抛 ValueError（不静默退化为全 0——如实降级红线的反面）。
"""
from topos.axis.registry import field_method
from topos.core.layers import LAYER_TYPES

ALL = list(LAYER_TYPES)


def _degrees(layers, n, only=None):
    """{layer: deg[i]}；only 为层名列表时只算这些层。"""
    want = [t for t in (only or ALL)]
    deg = {t: [0] * n for t in want}
    for t in want:
        d = deg[t]
        for (u, v) in layers.get(t, ()):
            if u < n:
                d[u] += 1
            if v < n:
                d[v] += 1
    return deg


@field_method("layer")
def layer_field(units, params, ctx):
    layers = ctx.get("layers") or {}
    n = len(units)
    formula = params.get("formula", "deg:call")

    if formula == "span":
        deg = _degrees(layers, n)
        return {i: sum(1 for t in ALL if deg[t][i] > 0) for i in range(n)}

    if formula == "gap":
        deg = _degrees(layers, n)
        dc = deg.get("call", [0] * n)
        dd = deg.get("data", [0] * n)
        dv = deg.get("vardep", [0] * n)
        return {i: (dd[i] + dv[i]) - dc[i] for i in range(n)}

    # A3：方向可观测量（仅 call 层有方向语义；其余层是无向的）
    if formula in ("out", "in", "net"):
        d_out = [0] * n
        d_in = [0] * n
        for (u, v) in layers.get("call", ()):
            if u < n:
                d_out[u] += 1
            if v < n:
                d_in[v] += 1
        if formula == "out":
            return {i: d_out[i] for i in range(n)}
        if formula == "in":
            return {i: d_in[i] for i in range(n)}
        return {i: d_out[i] - d_in[i] for i in range(n)}

    if formula.startswith("deg:"):
        t = formula.split(":", 1)[1]
        if t not in LAYER_TYPES:
            raise ValueError("未知层名: %s（合法层: %s）" % (t, ", ".join(ALL)))
        return {i: v for i, v in enumerate(_degrees(layers, n, [t])[t])}

    raise ValueError("layer 场未知 formula: %s（合法: deg:<层名> / span / gap）"
                     % formula)
