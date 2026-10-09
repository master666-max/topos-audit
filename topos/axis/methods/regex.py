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
    return {i: [t for t, pat in pats if pat.search(u["src"])]
            for i, u in enumerate(units)}
