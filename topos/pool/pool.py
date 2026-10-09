# -*- coding: utf-8 -*-
"""
topos.pool.pool —— 池布尔组合（ADR-A10）：expr = 切片名(str) | {"all":[...]} | {"any":[...]} | {"not": expr}。
leaf 引用 expand 产物（如 "anchor:eval"）时直接查切片表；引用不存在的切片名 → KeyError 指名。
"""
from topos.pool import slicer as _slicer_mod


def eval_expr(expr, slices, n):
    """expr → Set[unit_id]。"""
    if isinstance(expr, str):
        if expr not in slices:
            raise KeyError("池表达式引用了不存在的切片: %r" % expr)
        return set(slices[expr])
    if isinstance(expr, dict):
        if len(expr) != 1:
            raise ValueError("布尔嵌套节点必须恰含一个键 (all/any/not): %r" % expr)
        op, val = next(iter(expr.items()))
        if op == "not":
            return set(range(n)) - eval_expr(val, slices, n)
        if op == "all":
            acc = None
            for sub in val:
                s = eval_expr(sub, slices, n)
                acc = s if acc is None else (acc & s)
            return set(acc) if acc is not None else set()
        if op == "any":
            acc = set()
            for sub in val:
                acc |= eval_expr(sub, slices, n)
            return acc
        raise ValueError("未知组合算子: %r" % op)
    raise ValueError("expr 类型不合法: %r" % type(expr).__name__)


def eval_pools(pool_specs, slicer_specs, fields, n):
    """全部池 → [(name, set)]；并返回切片表（供诊断引用）。"""
    slices = _slicer_mod.compile_all(slicer_specs, fields)
    out = [(p["name"], eval_expr(p["expr"], slices, n)) for p in pool_specs]
    return out, slices
