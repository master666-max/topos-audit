# -*- coding: utf-8 -*-
"""
topos.axis.methods.graph_fields —— 图上场（G 层）。方法注册名 "graph"。
formula: "forman_unweighted"（Forman 节点曲率，标量场）| "diffusion"（嵌入坐标，列表场）。
formula 缺省时推断为 forman（axes v2 迁移兼容——v0.2 的 diffusion 轴缺 formula 事故教训）。
graph 懒构建（ctx["graph"] 缓存器：{adj, curv, coords, k_used, lam_residual}），
forman 与 diffusion 共享一次构建。
"""
from topos.axis.registry import field_method


@field_method("graph")
def graph_field(units, params, ctx):
    g = ctx["graph"]()
    formula = params.get("formula")
    if formula == "diffusion" or "k" in params:
        k = int(params.get("k", 3))
        return {i: list(g["coords"].get(i, []))[:k] for i in range(len(g["coords"]))}
    # "forman_unweighted" 或缺省 → Forman 曲率
    return dict(g["curv"])
