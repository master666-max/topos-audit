# -*- coding: utf-8 -*-
"""
topos.core.layers —— 五类耦合边抽取（call/data/control/return/vardep，SCN 血统）。
搬迁自 mini-lab/space_mini._extract_layers 全家（selftest 已验证件）。

v0.2 演进（E-M5-2 对拍 + RUN1 首战实测驱动，2026-10-10）：
  F1 dedent 兜底（类方法缩进切片 IndentationError 静默丢单元）；
  F3-py 最小包含 owner 归属（嵌套函数调用不再重复记到外层单元）；
  点链解析器：bare Name 沿用简单名解析（import 绑定名优先精确解析）；
  X.y 链式调用仅当链头 self（同对象方法）或 import 别名（已知模块）才解析，
  其余链头（局部变量/内建）不猜——可少不可假（argparse/from_dict 撞名 FP 根因）。

如实记录的抽取器天花板（N=65 样本实测）：control=1 / return=2 —— 控制依赖与
返回耦合在函数级+简单名解析近似下严重欠采；M5 引入 Joern 校验前不承诺完备。
"""
import ast
import os
import textwrap
from collections import defaultdict

LAYER_TYPES = ("call", "data", "control", "return", "vardep")


def _module2file(root):
    """仓内 .py 文件 → 模块点路径（a/b/c.py→a.b.c；a/b/__init__.py→a.b）。"""
    m2f = {}
    for dirpath, _d, files in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if any(s in (".git", "__pycache__", ".workbuddy")
               for s in rel_dir.split("/")):
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn),
                                  root).replace("\\", "/")
            mod = rel[:-3].replace("/", ".")
            if mod.endswith(".__init__"):
                mod = mod[:-9]
            m2f[mod] = rel
    return m2f


def _file_imports(root, files):
    """每文件 import 绑定表：{file: {binding: (kind, target_module)}}。

    kind='import'：import a.b.c → 绑定名 a，解析时用链前缀即模块路径；
    kind='from'  ：from M import x → 绑定名 x，target = M.x（相对导入按
    文件所在包折算）。解析失败/越顶的相对导入不登记（不猜）。"""
    out = {}
    for rel in files:
        path = os.path.join(root, rel)
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read())
        except (OSError, SyntaxError):
            continue
        pkg_parts = rel[:-3].replace("/", ".").split(".")
        pkg_parts = pkg_parts[:-1]                       # 文件所在包
        binds = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    binds[a.asname or a.name.split(".")[0]] = \
                        ("import", a.name)
            elif isinstance(node, ast.ImportFrom):
                level = node.level or 0
                base = pkg_parts[: len(pkg_parts) - (level - 1)] \
                    if level > 1 else pkg_parts[:]
                if level > 1 and len(pkg_parts) < level - 1:
                    continue                             # 越顶相对导入，不猜
                tgt = ".".join(base)
                if node.module:
                    tgt = (tgt + "." + node.module) if tgt else node.module
                for a in node.names:
                    if a.name == "*":
                        continue
                    binds[a.asname or a.name] = \
                        ("from", (tgt + "." + a.name) if tgt else a.name)
        if binds:
            out[rel] = binds
    return out


def _make_resolver(units, imports, m2f):
    """点链解析器。返回 resolve(i, chain) -> unit_idx | None。

    规则（可少不可假）：
      bare Name：import 绑定名（from M import x）→ 精确解析到 M 的同名单元；
                 否则简单名解析（同文件优先，跨文件兜底）。
      self.x   ：同文件尾名（同对象方法）。
      别名.x.y ：别名目标模块 + 中间段下钻，尾名在该模块文件内解析。
      其余链头：None（不猜——局部变量/内建的成员调用静态不可判定）。
    """
    by_name = defaultdict(list)
    by_file = defaultdict(lambda: defaultdict(list))
    for i, u in enumerate(units):
        tail = u["name"].split(".")[-1]
        by_name[tail].append(i)
        by_file[u["file"]][tail].append(i)

    def resolve(i, chain):
        if not chain:
            return None
        f = units[i]["file"]
        head, sep, rest = chain.partition(".")
        if not sep:
            ent = imports.get(f, {}).get(chain)
            if ent and ent[0] == "from":
                tail = ent[1].rsplit(".", 1)[-1]
                mf = m2f.get(ent[1].rsplit(".", 1)[0])
                for j in by_file.get(mf, {}).get(tail, []):
                    if j != i:
                        return j
                return None
            cands = by_name.get(chain, [])
            same = [j for j in cands if units[j]["file"] == f and j != i]
            if same:
                return same[0]
            cands2 = [j for j in cands if j != i]
            return cands2[0] if cands2 else None
        if head == "self":
            tail = rest.split(".")[0]
            for j in by_file.get(f, {}).get(tail, []):
                if j != i:
                    return j
            return None
        ent = imports.get(f, {}).get(head)
        if ent:
            if ent[0] == "import":
                # import a.b(.c)：链去尾 = 模块路径（import util_b 同式）
                cur = chain.rpartition(".")[0]
                tail = rest.rsplit(".", 1)[-1]
            else:                                    # from M import x
                cur = ent[1]
                segs = rest.split(".")
                for s in segs[:-1]:
                    cur += "." + s
                tail = segs[-1]
            mf = m2f.get(cur)
            for j in by_file.get(mf, {}).get(tail, []):
                if j != i:
                    return j
            return None
        return None
    return resolve


def _walk_calls(node, ctx, out, base_line):
    """递归携带上下文收集 Call：(点链, ctx_set, 相对行)。

    点链 = Name.id 或 Attribute 全链（X.y.z）；链头非 Name/Attribute
    （如 foo().bar()）→ None（静态不可判定）。ctx: call/test/return/assign"""
    if isinstance(node, (ast.If, ast.While)):
        _walk_calls(node.test, ctx | {"test"}, out, base_line)
        for sub in list(node.body) + list(getattr(node, "orelse", []) or []):
            _walk_calls(sub, ctx, out, base_line)
        return
    if isinstance(node, (ast.For, ast.AsyncFor)):
        _walk_calls(node.iter, ctx | {"test"}, out, base_line)
        for sub in list(node.body) + list(getattr(node, "orelse", []) or []):
            _walk_calls(sub, ctx, out, base_line)
        return
    if isinstance(node, ast.Return):
        if node.value is not None:
            _walk_calls(node.value, ctx | {"return"}, out, base_line)
        return
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        val = node.value
        if val is not None:
            _walk_calls(val, ctx | {"assign"}, out, base_line)
        return
    if isinstance(node, ast.Call):
        chain = None
        if isinstance(node.func, ast.Name):
            chain = node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            cur = node.func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
                chain = ".".join(reversed(parts))
        if chain is not None:
            out.append((chain, frozenset(ctx), node.lineno))
        for a in node.args:
            _walk_calls(a, ctx, out, base_line)
        for kw in node.keywords:
            _walk_calls(kw.value, ctx, out, base_line)
        return
    for child in ast.iter_child_nodes(node):
        _walk_calls(child, ctx, out, base_line)


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
    """五类耦合边主抽取。返回 {layer_type: set[(min,max)]}。

    v0.2：owner 归属（调用点归最小包含单元）+ 点链解析器（self/别名才解析）。"""
    layers = {k: set() for k in LAYER_TYPES}
    mod_names = _module_level_names(root)
    files = sorted({u["file"] for u in units})
    imports = _file_imports(root, files)
    m2f = _module2file(root)
    resolve = _make_resolver(units, imports, m2f)

    # owner 归属：每文件单元 span（按跨度升序 → 首个包含即最小）
    spans = defaultdict(list)
    for i, u in enumerate(units):
        spans[u["file"]].append((u["lineno"], u["end_lineno"], i))
    for f in spans:
        spans[f].sort(key=lambda x: (x[1] - x[0], x[0]))

    def owner_of(fname, abs_line):
        for a, b, i in spans.get(fname, []):
            if a <= abs_line <= b:
                return i
        return None

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
        _walk_calls(tree, {"call"}, calls, u["lineno"])
        used_globals = set()
        for x in ast.walk(tree):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                used_globals.add(x.id)
        own_global = set()
        for x in ast.walk(tree):
            if isinstance(x, ast.Global):
                own_global.update(x.names)
        shared_mod = (used_globals | own_global) & mod_names.get(u["file"], set())
        for chain, ctx, rel_ln in calls:
            # F3-py（RUN1/对拍实测）：调用点归最小包含单元，嵌套内调用
            # 不再重复记到外层单元（sendfile→onX / checks→check_ast_node 根因）
            abs_ln = u["lineno"] + rel_ln - 1
            if owner_of(u["file"], abs_ln) != i:
                continue
            j = resolve(i, chain)
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
        var_callee = _assign_var_callee(resolve, i, tree)
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


def _assign_var_callee(resolve, i, tree):
    """单元 i 内：Assign 目标名 → 其 value 中 Call 的被调单元 idx。"""
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
