# -*- coding: utf-8 -*-
"""
topos.axis.methods.ast_metrics —— 语法度量场（L 层）。方法注册名 "ast"。
metrics：lines（函数行数，来自 Unit.loc）。
"""
from topos.axis.registry import field_method


@field_method("ast")
def ast_field(units, params, ctx):
    metric = params.get("metric", "lines")
    if metric == "lines":
        return {i: u["loc"] for i, u in enumerate(units)}
    raise ValueError("unknown ast metric: %s" % metric)
