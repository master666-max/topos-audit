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
    # v0.2（RUN1 首战实测）：opt-in 测试豁免——测试脚手架合法使用危险 API
    #（mock subprocess 等），anchor 语义是生产代码危险直连。exclude_tests=true
    # 时测试单元 anchor 缺失（不假装命中）；默认关闭，旧读数不受扰。
    ex = bool(params.get("exclude_tests"))
    out = {}
    for i, u in enumerate(units):
        if ex and _is_test_unit(u):
            continue
        out[i] = [t for t, pat in pats if pat.search(u["src"])]
    return out


def _is_test_unit(u):
    """测试文件启发：路径段 test(s)/testing/spec(s)/__tests__、conftest.py、
    或文件名 token 化后含 test/tests（dsh_tests.py → [dsh, tests] 命中；
    latest.py → [latest] 不误伤）。"""
    f = (u.get("file") or "").replace("\\", "/").lower()
    segs = f.split("/")
    if segs[-1] == "conftest.py":
        return True
    if any(s in ("tests", "test", "testing", "spec", "specs", "__tests__")
           for s in segs[:-1]):
        return True
    stem = segs[-1][:-3] if segs[-1].endswith(".py") else segs[-1]
    tokens = re.split(r"[_.\-]+", stem)
    return "test" in tokens or "tests" in tokens
