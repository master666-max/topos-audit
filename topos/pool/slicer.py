# -*- coding: utf-8 -*-
"""
topos.pool.slicer —— 切片算子：场(Field) → 单元集合(Set[unit_id])。
op 集（ADR-A11/A12）：
  has          列表场含某值
  gt/lt/ge/le  标量比较（None 排除）
  quantile_gt  > 分位 q（在非缺失值上取位）
  quantile_le  ≤ 分位 q
  between_q    q_lo < v ≤ q_hi
  notnull      非缺失（None/空列表 视为缺失；唯一能捞回缺失单元的算子）
  expand       列表场逐取值展开成片（"anchor:*" → "anchor:eval"...），注册期生成
None 永远不落入任何切片（除 notnull 的补集语义由上层 not 表达）。
"""
from topos.axis.registry import is_missing


def _quantile(sorted_vals, q):
    """离散分位：取第 floor(q*(len-1)) 个（非缺失值上）。"""
    if not sorted_vals:
        return None
    idx = min(int(q * (len(sorted_vals) - 1) + 1e-9), len(sorted_vals) - 1)
    return sorted_vals[idx]


def compile_slicer(spec, fields):
    """slicer 声明 → (name, set[unit_id])。expand 在这里展开。"""
    name, field_name, op = spec["name"], spec["field"], spec["op"]
    field = fields[field_name]
    n = len(field)

    if op == "expand":
        base = name[:-2] if name.endswith(":*") else name
        raw = set()
        for v in field.values():
            if is_missing(v):
                continue
            items = v if isinstance(v, (list, tuple, set)) else [v]
            raw.update(items)
        out = []
        for v in sorted(raw):
            members = {i for i in range(n)
                       if not is_missing(field.get(i)) and v in field[i]}
            out.append(("%s:%s" % (base, v), members))
        return out

    if op == "notnull":
        return [(name, {i for i in range(n) if not is_missing(field.get(i))})]

    if op == "has":
        val = spec["value"]
        return [(name, {i for i in range(n)
                        if not is_missing(field.get(i))
                        and isinstance(field[i], (list, tuple, set))
                        and val in field[i]})]

    # 标量比较族：先排除缺失
    present = {i: field[i] for i in range(n) if not is_missing(field.get(i))
               and not isinstance(field[i], (list, tuple, set))}
    if op == "gt":
        return [(name, {i for i, v in present.items() if v > spec["value"]})]
    if op == "lt":
        return [(name, {i for i, v in present.items() if v < spec["value"]})]
    if op == "ge":
        return [(name, {i for i, v in present.items() if v >= spec["value"]})]
    if op == "le":
        return [(name, {i for i, v in present.items() if v <= spec["value"]})]
    if op == "quantile_gt":
        thr = _quantile(sorted(present.values()), spec["q"])
        return [(name, {i for i, v in present.items() if thr is not None and v > thr})]
    if op == "quantile_le":
        thr = _quantile(sorted(present.values()), spec["q"])
        return [(name, {i for i, v in present.items() if thr is not None and v <= thr})]
    if op == "between_q":
        vals = sorted(present.values())
        lo = _quantile(vals, spec["q_lo"])
        hi = _quantile(vals, spec["q_hi"])
        return [(name, {i for i, v in present.items()
                        if lo is not None and lo < v <= hi})]
    raise ValueError("unknown slicer op: %s" % op)


def compile_all(slicer_specs, fields):
    """全部切片 → 有序 dict{name: set}；expand 产出多个键，并额外注册
    expand 名本身 = 所有展开切片的并集（池表达式可直接引用 "anchor:*"）。"""
    slices = {}
    for spec in slicer_specs:
        produced = compile_slicer(spec, fields)
        union = set()
        for nm, members in produced:
            slices[nm] = members
            union |= members
        if spec["op"] == "expand":
            slices[spec["name"]] = union
    return slices
