# -*- coding: utf-8 -*-
"""
topos.axis.manifest —— 清单 v3 加载 + schema 校验。
v3 结构：{version, layers, fields[], slicers[], pools[], constraints}
  fields[i]  = {name, layer, method, params}          场：引擎按 method 分派
  slicers[i] = {name, field, op, ...}                 切片：场上算子
  pools[i]   = {name, expr}                           池：切片的布尔嵌套组合（ADR-A10）
  constraints= {max_width, max_pools, min_pool_size}  宽度平衡条款工具化（ADR 见 ARCHITECTURE §4.3）
校验失败抛 ManifestError 并指名问题条目。
"""
import json
import os

VALID_OPS = {"has", "gt", "lt", "ge", "le", "quantile_gt", "quantile_le",
             "between_q", "notnull", "expand"}

REQUIRED_POOL_OPS = {"all", "any", "not"}


class ManifestError(ValueError):
    pass


def load_manifest(path):
    """读清单 + 全量校验。返回 dict。"""
    with open(path, encoding="utf-8") as f:
        mf = json.load(f)
    validate(mf, base_dir=os.path.dirname(os.path.abspath(path)))
    return mf


def validate(mf, base_dir=None):
    if not isinstance(mf, dict):
        raise ManifestError("清单顶层必须是对象")
    if mf.get("version") != 3:
        raise ManifestError("version 必须 = 3（当前: %r）" % mf.get("version"))
    layers = mf.get("layers", {})
    for k in layers:
        if k not in ("call", "data", "control", "return", "vardep"):
            raise ManifestError("layers 含未知层: %s" % k)

    # fields
    from topos.axis import registry
    field_names = set()
    for f in mf.get("fields", []):
        for key in ("name", "method"):
            if key not in f:
                raise ManifestError("field 缺 %s: %r" % (key, f))
        if f["name"] in field_names:
            raise ManifestError("field 重名: %s" % f["name"])
        field_names.add(f["name"])
        if f["method"] not in registry.FIELD_METHODS:
            raise ManifestError("field %r 的 method 未注册: %r（已注册: %s）"
                                % (f["name"], f["method"], sorted(registry.FIELD_METHODS)))
        # patterns_file 相对路径在加载场时解析（相对清单文件目录）

    # slicers
    slicer_names = set()
    for s in mf.get("slicers", []):
        for key in ("name", "field", "op"):
            if key not in s:
                raise ManifestError("slicer 缺 %s: %r" % (key, s))
        if s["name"] in slicer_names:
            raise ManifestError("slicer 重名: %s" % s["name"])
        slicer_names.add(s["name"])
        if s["field"] not in field_names:
            raise ManifestError("slicer %r 引用未定义场: %r" % (s["name"], s["field"]))
        if s["op"] not in VALID_OPS:
            raise ManifestError("slicer %r 的 op 不合法: %r（合法: %s）"
                                % (s["name"], s["op"], sorted(VALID_OPS)))
        if s["op"] == "has" and "value" not in s:
            raise ManifestError("slicer %r 的 op=has 需要 value" % s["name"])
        if s["op"] in ("gt", "lt", "ge", "le") and "value" not in s:
            raise ManifestError("slicer %r 的 op=%s 需要 value" % (s["name"], s["op"]))
        if s["op"] == "quantile_gt" and "q" not in s:
            raise ManifestError("slicer %r 的 op=quantile_gt 需要 q" % s["name"])
        if s["op"] == "quantile_le" and "q" not in s:
            raise ManifestError("slicer %r 的 op=quantile_le 需要 q" % s["name"])
        if s["op"] == "between_q" and ("q_lo" not in s or "q_hi" not in s):
            raise ManifestError("slicer %r 的 op=between_q 需要 q_lo/q_hi" % s["name"])

    # pools（布尔嵌套，叶子=切片名；expand 展开后的名字 anchor:<v> 在运行期解析）
    for p in mf.get("pools", []):
        if "name" not in p or "expr" not in p:
            raise ManifestError("pool 缺 name/expr: %r" % p)
        _check_expr(p["expr"], p["name"])

    # constraints
    c = mf.get("constraints", {})
    for key in ("max_width", "max_pools", "min_pool_size"):
        if key in c and not isinstance(c[key], int):
            raise ManifestError("constraints.%s 必须是整数" % key)
    return True


def _check_expr(expr, pool_name):
    if isinstance(expr, str):
        return
    if isinstance(expr, dict):
        if len(expr) != 1:
            raise ManifestError("pool %r 嵌套节点必须恰含一个键 (all/any/not)" % pool_name)
        op, val = next(iter(expr.items()))
        if op not in REQUIRED_POOL_OPS:
            raise ManifestError("pool %r 的组合算子不合法: %r" % (pool_name, op))
        if op == "not":
            _check_expr(val, pool_name)
        else:
            if not isinstance(val, list) or not val:
                raise ManifestError("pool %r 的 %s 需要非空列表" % (pool_name, op))
            for sub in val:
                _check_expr(sub, pool_name)
        return
    raise ManifestError("pool %r 的 expr 类型不合法: %r" % (pool_name, type(expr).__name__))
