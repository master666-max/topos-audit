# -*- coding: utf-8 -*-
"""
topos.core.layers —— 五类耦合边抽取（call/data/control/return/vardep，SCN 血统）。
搬迁自 mini-lab/space_mini._extract_layers 全家（selftest 10/10 已验证件），逻辑零改动。

如实记录的抽取器天花板（N=65 样本实测）：control=1 / return=2 —— 控制依赖与
返回耦合在函数级+简单名解析近似下严重欠采；M5 引入 Joern 校验前不承诺完备。
"""
import ast
import os
import textwrap
from collections import defaultdict

LAYER_TYPES = ("call", "data", "control", "return", "vardep")


def _resolver(units):
    by_name = defaultdict(list)
    for i, u in enumerate(units):
        by_name[u["name"].split(".")[-1]].append(i)

    def resolve(src_unit_idx, simple):
        cands = by_name.get(simple, [])
        if not cands:
            return None
        f = units[src_unit_idx]["file"]
        same = [j for j in cands if units[j]["file"] == f and j != src_unit_idx]
        if same:
            return same[0]
        cands2 = [j for j in cands if j != src_unit_idx]
        return cands2[0] if cands2 else None
    return resolve


def _walk_calls(node, ctx, out):
    """递归携带上下文收集 Call：(callee_simple, ctx_set)。ctx: call/test/return/assign"""
    if isinstance(node, (ast.If, ast.While)):
        _walk_calls(node.test, ctx | {"test"}, out)
        for sub in list(node.body) + list(getattr(node, "orelse", []) or []):
            _walk_calls(sub, ctx, out)
        return
    if isinstance(node, (ast.For, ast.AsyncFor)):
        _walk_calls(node.iter, ctx | {"test"}, out)
        for sub in list(node.body) + list(getattr(node, "orelse", []) or []):
            _walk_calls(sub, ctx, out)
        return
    if isinstance(node, ast.Return):
        if node.value is not None:
            _walk_calls(node.value, ctx | {"return"}, out)
        return
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        val = node.value
        if val is not None:
            _walk_calls(val, ctx | {"assign"}, out)
        return
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            out.append((node.func.id, frozenset(ctx)))
            for a in node.args:
                _walk_calls(a, ctx, out)
            for kw in node.keywords:
                _walk_calls(kw.value, ctx, out)
            return
        if isinstance(node.func, ast.Attribute):
            out.append((node.func.attr, frozenset(ctx)))
            for a in node.args:
                _walk_calls(a, ctx, out)
            return
    for child in ast.iter_child_nodes(node):
        _walk_calls(child, ctx, out)


def _module_level_names(root):
    """每文件模块级变量名（vardep 候选）。"""
    mod_names = {}
    for dirpath, _d, files in os.walk(root):
        # 同 units.discover_units：只按相对 root 的路径段过滤
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if any(s in (".git", "__pycache__", ".workbuddy")
               for s in rel_dir.split("/")):
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root).replace("\\", "/")
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    tree = ast.parse(f.read())
            except SyntaxError:
                continue
            names = set()
            for node in tree.body:
                tgts = []
                if isinstance(node, ast.Assign):
                    tgts = node.targets
                elif isinstance(node, ast.AnnAssign):
                    tgts = [node.target]
                elif isinstance(node, ast.AugAssign):
                    tgts = [node.target]
                for t in tgts:
                    for x in ast.walk(t):
                        if isinstance(x, ast.Name):
                            names.add(x.id)
            mod_names[rel] = names
    return mod_names


def _extract_layers(root, units):
    """五类耦合边主抽取。返回 {layer_type: set[(min,max)]}。"""
    layers = {k: set() for k in LAYER_TYPES}
    resolve = _resolver(units)
    mod_names = _module_level_names(root)
    for i, u in enumerate(units):
        try:
            tree = ast.parse(u["src"])
        except SyntaxError:
            # E-M5-2 对拍发现（2026-10-10）：类方法切片带缩进，直接 parse 抛
            # IndentationError（SyntaxError 子类）→ 此前整个单元被静默跳过，
            # 类方法全部 call/vardep 边丢失。dedent 兜底修复。
            try:
                tree = ast.parse(textwrap.dedent(u["src"]))
            except SyntaxError:
                continue
        calls = []
        _walk_calls(tree, {"call"}, calls)
        used_globals = set()
        for x in ast.walk(tree):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                used_globals.add(x.id)
        own_global = set()
        for x in ast.walk(tree):
            if isinstance(x, ast.Global):
                own_global.update(x.names)
        shared_mod = (used_globals | own_global) & mod_names.get(u["file"], set())
        for simple, ctx in calls:
            j = resolve(i, simple)
            if j is None:
                continue
            e = (min(i, j), max(i, j))
            layers["call"].add(e)
            if "test" in ctx:
                layers["control"].add(e)
            if "return" in ctx:
                layers["return"].add(e)
            if "assign" in ctx:
                layers["data"].add(e)
        # 值穿越：f 内 val=g(...) 且 h(...,val,...) → g→h data 边（对齐 space_mini._pass_through_data）
        var_callee = _assign_var_callee(units, i, tree)
        if var_callee:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        h = resolve(i, node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        h = resolve(i, node.func.attr)
                    else:
                        continue
                    if h is None or h == i:
                        continue
                    names = {x.id for x in ast.walk(node)
                             if isinstance(x, ast.Name)}
                    for v in names:
                        g = var_callee.get(v)
                        if g is not None and g != h:
                            layers["data"].add((min(g, h), max(g, h)))
        # vardep：同文件共享模块级变量的函数对
        for j in range(len(units)):
            if j == i or units[j]["file"] != u["file"]:
                continue
            try:
                tj = ast.parse(units[j]["src"])
            except SyntaxError:
                continue
            jg = {x.id for x in ast.walk(tj) if isinstance(x, ast.Name)}
            jg |= {gn for x in ast.walk(tj) if isinstance(x, ast.Global)
                   for gn in x.names}
            if shared_mod & jg:
                layers["vardep"].add((min(i, j), max(i, j)))
    return layers


def _assign_var_callee(units, i, tree):
    """单元 i 内：Assign 目标名 → 其 value 中 Call 的被调单元 idx。"""
    resolve = _resolver(units)
    vc = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            tg = {x.id for x in node.targets if isinstance(x, ast.Name)}
            for x in ast.walk(node.value):
                if isinstance(x, ast.Call) and isinstance(x.func, ast.Name):
                    j = resolve(i, x.func.id)
                    if j is not None:
                        for t in tg:
                            vc[t] = j
    return vc


def to_adj(fused_edges):
    """融合边 → 无向邻接表 {i: set(j)}。
    保持 defaultdict 语义：孤立单元（无边）也必须可索引（_matvec_L 依赖）。"""
    adj = defaultdict(set)
    for (u, v) in fused_edges:
        adj[u].add(v)
        adj[v].add(u)
    return adj
