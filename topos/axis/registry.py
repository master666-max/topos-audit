# -*- coding: utf-8 -*-
"""
topos.axis.registry —— 方法学注册表。引擎只认 method 字符串，不认场名（红线：清单单源）。
继承 mini-lab/coord_mini.axis_method 模式（解耦验收 11/11 已验证），函数统一 _field 后缀
（ADR：防 v0.2 `def random(...)` 遮蔽 random 模块事故重演）。

Field 契约：dict[unit_id -> value | None]；None = 该场在此单元上无定义（合法值，禁止填 0）。
列表场（如 anchor 的 tag 列表）：[] 视为缺失。
"""

# name(method 字符串) -> callable(units, params, ctx) -> Field
FIELD_METHODS = {}


def field_method(name):
    """注册装饰器：@field_method("regex")。重名注册直接抛错（机制唯一红线）。"""
    def deco(fn):
        if name in FIELD_METHODS:
            raise ValueError("field method 已注册: %s" % name)
        FIELD_METHODS[name] = fn
        return fn
    return deco


def is_listy(v):
    return isinstance(v, (list, tuple, set))


def is_missing(v):
    """缺失判定：None、空列表/元组/集合。0 与 False 是合法值不是缺失（如实降级红线的反面）。"""
    if v is None:
        return True
    if is_listy(v):
        return len(v) == 0
    return False
