# -*- coding: utf-8 -*-
"""
topos.axis.methods.regex —— 锚点正则场。方法注册名 "regex"。
锚点模式可由 params.patterns_file（相对**清单文件目录**解析）或 params.patterns 外置；
默认无模式时返回全缺失场（不假装）。
Field 值 = 命中的 tag 列表（列表场，供 expand 展开）。
"""
import json
import os
import re

from topos.axis.registry import field_method
from topos.core.units import is_test_unit


def _load_patterns(params, base_dir=None):
    if "patterns" in params:
        return [(t, re.compile(rx)) for t, rx in params["patterns"]]
    pf = params.get("patterns_file")
    if pf:
        p = pf if os.path.isabs(pf) else os.path.join(base_dir or os.getcwd(), pf)
        with open(p, encoding="utf-8") as f:
            return [(t, re.compile(rx)) for t, rx in json.load(f)]
    return []


@field_method("regex")
def regex_field(units, params, ctx):
    pats = _load_patterns(params, base_dir=ctx.get("manifest_dir"))
    # v0.2（RUN1 首战实测）：opt-in 测试豁免——测试脚手架合法使用危险 API
    #（mock subprocess 等），anchor 语义是生产代码危险直连。exclude_tests=true
    # 时测试单元 anchor 缺失（不假装命中）；默认关闭，旧读数不受扰。
    ex = bool(params.get("exclude_tests"))
    out = {}
    for i, u in enumerate(units):
        if ex and is_test_unit(u):
            continue
        out[i] = [t for t, pat in pats if pat.search(u["src"])]
    return out


def _is_test_unit(u):
    """兼容别名（单源已上移 topos.core.units.is_test_unit）。"""
    return is_test_unit(u)
