# -*- coding: utf-8 -*-
"""
topos.core.seams —— 接缝抽取 + 符号规则表 v0.1 [U]（PREREG/B5 §B）。

Q3 裁决（2026-10-10）：降标采纳——规则由 E×D×F（pre-research B-topology §3.3）的
L1 槽位分类 + L2 rubric 骨架 + L3.2 实际控制流 + L4 绝对否决项**瘦身导出**（每条规则
在 docstring/PREREG 中标注推导来源，非凭空猜符号）；J6 全量纪律件（双人盲裁 κ≥0.60）
留作升级路径，本表版本化可整体替换。R7：本模块产出为 [U]，不冒充 [M]。

节点 = 模块；z_v = 域声明证词（v0.1 全 +1，PREREG §B）；边 = repo 内跨模块交互；
s_e 由下表规则从 AST 机械事实导出（T-B5-a：每个符号可指认到 AST 事实 + 规则编号）。

规则表 v0.1（PREREG/B5 §B）：
  R1 public_call    → +1    （L1-S1 受控穿越：调用公开符号，明示 conduit）
  R2 private_touch  → −1    （L1-S5 + L3.2：`_` 前缀 = 封装契约声明，实际控制流越过它）
  R3 global_write   → −1    （L1-S3 共享资源汇合：跨模块写模块级可变全局，所有权翻转）
  R4 unsafe_parser  → VETO  （L4 绝对否决：未校验实参直连解析器/执行器，不进 sheaf）
"""
import ast
import os

VETO = "unsafe_parser"

#: R4 危险解析器/执行器（L4 绝对否决项 ①：未校验外部输入直连解释器）
UNSAFE_PARSERS = {
    "eval", "exec", "compile",
    "os.system", "os.popen",
    "pickle.loads", "yaml.load", "yaml.unsafe_load",
}
#: subprocess 家族仅在 shell=True 时否决（PREREG R4 括注）
SUBPROCESS_SHELL = {"subprocess.call", "subprocess.run", "subprocess.Popen",
                    "subprocess.check_call", "subprocess.check_output"}

#: R3 原地变更算符（B.g.<mutator>(…) 视为写）
MUTATORS = {"append", "extend", "insert", "pop", "clear", "update", "add",
            "remove", "setdefault", "appendleft", "popleft", "discard"}

#: 规则 → 符号（方向性契约，selftest c24 对拍）
RULE_SIGN = {"public_call": 1, "private_touch": -1, "global_write": -1,
             VETO: "VETO"}

#: 非字面量实参形态（PREREG R4：NAME / 属性链 / 调用结果 → 存在 untrusted 可达路径）
_NONLITERAL = (ast.Name, ast.Attribute, ast.Call, ast.Subscript,
               ast.BinOp, ast.JoinedStr, ast.Starred)


def _dotted(node):
    """Attribute/Name 链 → 点号串（如 'os.system'）；非链形返回 None。"""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return None


class _ModFacts(object):
    """单模块机械事实（AST 一遍扫出）。"""

    def __init__(self, name, path):
        self.name = name                      # repo 内模块名（点号路径）
        self.path = path
        self.aliases = {}                     # 局部名 → ('mod', 目标模块名) / ('sym', 模块名, 符号)
        self.module_globals = set()           # 模块级赋值目标（含 mutable 判定放宽：全部计）
        self.calls = []                       # (line, func_ast)
        self.stores = []                      # (line, target_ast)  Assign/AnnAssign/AugAssign
        self.has_external_input = False       # 外部入口信号（报告用）


def _scan_file(path, mod_name):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except SyntaxError:
            return None
    mf = _ModFacts(mod_name, path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mf.aliases[a.asname or a.name.split(".")[0]] = ("mod", a.name)
        elif isinstance(node, ast.ImportFrom):
            base = (node.module or "")
            for a in node.names:
                if a.name == "*":
                    continue
                if base:
                    mf.aliases[a.asname or a.name] = ("sym", base, a.name)
                # from . import x / from .pkg import x：相对导入由 resolve 阶段补全
                else:
                    mf.aliases[a.asname or a.name] = ("relmod", node.level, a.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            pass                                    # 顶层 def/class：R2 靠 `_` 前缀判，
                                                    # 不进 module_globals（R3 仅纯赋值变量）
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if node.col_offset == 0 and isinstance(t, ast.Name):
                    mf.module_globals.add(t.id)
                mf.stores.append((node.lineno, t))
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            if node.col_offset == 0 and isinstance(node.target, ast.Name):
                mf.module_globals.add(node.target.id)
            mf.stores.append((node.lineno, node.target))
        elif isinstance(node, ast.Call):
            mf.calls.append((node.lineno, node))
            if isinstance(node.func, ast.Name) and node.func.id == "input":
                mf.has_external_input = True
        elif isinstance(node, ast.Name) and node.id in ("argv", "stdin") \
                and isinstance(node.ctx, ast.Load):
            mf.has_external_input = True
    return mf


class _Resolver(object):
    """repo 模块名 → 文件 映射 + 相对导入解析。"""

    def __init__(self, repo_dir):
        self.repo_dir = os.path.abspath(repo_dir)
        self.mod2file = {}
        for root, dirs, files in os.walk(self.repo_dir):
            dirs[:] = [d for d in dirs if d not in
                       (".git", "__pycache__", "node_modules", ".workbuddy",
                        "exp-out", "reference")]
            for fn in files:
                if fn.endswith(".py"):
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, self.repo_dir)
                    parts = rel[:-3].split(os.sep)
                    if parts[-1] == "__init__":
                        parts = parts[:-1]
                    self.mod2file[".".join(parts)] = full
        self._facts = {}

    def facts(self, mod_name):
        if mod_name not in self._facts:
            p = self.mod2file.get(mod_name)
            self._facts[mod_name] = _scan_file(p, mod_name) if p else None
        return self._facts[mod_name]

    def resolve_alias(self, mf, local):
        """局部名 → ('mod', 模块名) / ('sym', 模块名, 符号) / None。"""
        ent = mf.aliases.get(local)
        if ent is None:
            return None
        kind = ent[0]
        if kind == "mod":
            target = ent[1]
            if target in self.mod2file:
                return ("mod", target)
            # import a.b.c：绑定名是 a，实际模块 a.b.c 也在 repo → 指向 a.b.c
            if target.split(".")[0] == local and target in self.mod2file:
                return ("mod", target)
            head = target.split(".")[0]
            if head in self.mod2file:
                return ("mod", head)
            return None
        if kind == "sym":
            _k, base, sym = ent
            tgt = self._abs(mf, base, 0)
            if tgt:
                # from PKG import submodule：PKG.NAME 本身是 repo 模块 → 按模块绑定
                if ".".join([tgt, sym]) in self.mod2file:
                    return ("mod", ".".join([tgt, sym]))
                if tgt in self.mod2file:
                    return ("sym", tgt, sym)
            return None
        # relmod：from .[pkg] import name（level≥1）
        _k, level, name = ent
        pkg = mf.name.split(".")
        base_pkg = pkg[: len(pkg) - (level - 1)] if level > 1 else pkg[:]
        tgt = ".".join(base_pkg + ([name] if name else []))
        if tgt in self.mod2file:
            return ("mod", tgt)
        tgt2 = ".".join(base_pkg) + (("." + name) if name else "")
        if tgt2 in self.mod2file:
            return ("mod", tgt2)
        return None

    def _abs(self, mf, base, level):
        """from BASE import … 的绝对化（level=0 即绝对导入）。"""
        if level == 0:
            return base
        pkg = mf.name.split(".")
        base_pkg = pkg[: len(pkg) - (level - 1)] if level > 1 else pkg[:]
        cand = ".".join(base_pkg + ([base] if base else []))
        return cand


def _classify_call(res, mf, call):
    """Call 节点 → (action, target_mod, symbol, extra) 或 None。"""
    func = call.func
    # 形态 B.g.mutator(...) → R3
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Attribute):
        mid = _dotted(func.value)               # 'B.g'
        if mid:
            head, _, g = mid.partition(".")
            r = res.resolve_alias(mf, head)
            if r and r[0] == "mod" and g in _mod_globals(res, r[1]) \
                    and func.attr in MUTATORS:
                return ("global_write", r[1], g, "mutator:%s" % func.attr)
    # 形态 B.mutator 直接调用不会是 R3；常规符号解析
    dotted = _dotted(func)
    if dotted:
        head, _, rest = dotted.partition(".")
        r = res.resolve_alias(mf, head)
        if r is None:
            # 未 import 的名字：builtin/本地定义（同模块不建边）或 stdlib 全路径
            full = dotted
            if full in UNSAFE_PARSERS:
                return _veto_if(call, full)
            if full in SUBPROCESS_SHELL:
                return _veto_if(call, full, need_shell=True)
            return None
        if r[0] == "mod":
            mod, sym = r[1], (rest.split(".")[0] if rest else "")
            if sym and sym not in _mod_globals(res, mod):
                if sym.startswith("_"):
                    return ("private_touch", mod, sym, None)
                if not rest or "." not in rest:
                    return ("public_call", mod, sym, None)
            if sym in _mod_globals(res, mod) and rest:
                meth = rest.split(".")[1] if "." in rest else ""
                if meth in MUTATORS:
                    return ("global_write", mod, sym, "mutator:%s" % meth)
            if not sym:
                return None
            return None
        if r[0] == "sym":
            mod, sym = r[1], r[2]
            full_sym = "%s.%s" % (mod, sym)
            if full_sym in SUBPROCESS_SHELL:
                return _veto_if(call, full_sym, need_shell=True)
            if sym.startswith("_"):
                return ("private_touch", mod, sym, None)
            if sym in UNSAFE_PARSERS or sym in ("system", "popen"):
                cand = sym if sym in UNSAFE_PARSERS else \
                    ("os.system" if sym == "system" else "os.popen")
                return _veto_if(call, cand)
            return ("public_call", mod, sym, None)
    if isinstance(func, ast.Name):
        nm = func.id
        r = res.resolve_alias(mf, nm)
        if r and r[0] == "sym":
            mod, sym = r[1], r[2]
            full = "%s.%s" % (mod, sym)
            if sym in UNSAFE_PARSERS or full in UNSAFE_PARSERS:
                return _veto_if(call, sym if sym in UNSAFE_PARSERS else full)
            if full in SUBPROCESS_SHELL:
                return _veto_if(call, full, need_shell=True)
            if sym.startswith("_"):
                return ("private_touch", mod, sym, None)
            return ("public_call", mod, sym, None)
        if nm in UNSAFE_PARSERS:
            return _veto_if(call, nm)
        if nm in SUBPROCESS_SHELL:
            return _veto_if(call, nm, need_shell=True)
    return None


def _mod_globals(res, mod):
    mf = res.facts(mod)
    return mf.module_globals if mf else set()


def _veto_if(call, name, need_shell=False):
    if need_shell:
        shell = any(kw.arg == "shell" and _truthy(kw.value)
                    for kw in call.keywords)
        if not shell:
            return None
    args = [a for a in call.args if not isinstance(a, ast.Starred)]
    if args and isinstance(args[0], ast.Constant):
        return None                               # 字面量实参：无 untrusted 路径
    if args and isinstance(args[0], _NONLITERAL):
        return (VETO, None, name, "arg=%s" % type(args[0]).__name__)
    return None


def _truthy(v):
    return isinstance(v, ast.Constant) and bool(v.value)


def _classify_store(res, mf, line, target):
    """赋值目标 → R3（B.g = … / B.g[…] = …）。"""
    if isinstance(target, ast.Subscript):
        target = target.value
    if not isinstance(target, ast.Attribute):
        return None
    mid = _dotted(target)
    if not mid or "." not in mid:
        return None
    head, _, g = mid.partition(".")
    r = res.resolve_alias(mf, head)
    if r and r[0] == "mod" and g in _mod_globals(res, r[1]):
        return ("global_write", r[1], g, "store")
    return None


def extract(repo_dir):
    """全仓抽取。返回：
    modules  : [模块名]（排序）
    edges    : [(u, v, action, sign, evidence)]  u≠v，evidence=[(file:line, detail)]
    vetoes   : [(file:line, symbol, detail)]
    """
    res = _Resolver(repo_dir)
    modules = sorted(res.mod2file)
    idx = {m: i for i, m in enumerate(modules)}
    acc = {}                                       # (u,v,action) → [evidence]
    vetoes = []
    for u in modules:
        mf = res.facts(u)
        if mf is None:
            continue
        for line, call in mf.calls:
            c = _classify_call(res, mf, call)
            if c is None:
                continue
            action, tgt, sym, extra = c
            ev = ("%s:%d" % (os.path.relpath(mf.path, res.repo_dir).replace(
                "\\", "/"), line), "%s%s" % (sym, (" · " + extra) if extra else ""))
            if action == VETO:
                vetoes.append((ev[0], sym, extra or ""))
                continue
            if tgt is None or tgt == u or tgt not in idx:
                continue
            acc.setdefault((u, tgt, action), []).append(ev)
        for line, target in mf.stores:
            c = _classify_store(res, mf, line, target)
            if c is None:
                continue
            action, tgt, sym, extra = c
            if tgt == u or tgt not in idx:
                continue
            ev = ("%s:%d" % (os.path.relpath(mf.path, res.repo_dir).replace(
                "\\", "/"), line), "%s · %s" % (sym, extra))
            acc.setdefault((u, tgt, action), []).append(ev)
    edges = []
    for (u, v, action) in sorted(acc):
        edges.append((u, v, action, RULE_SIGN[action], acc[(u, v, action)]))
    return modules, edges, vetoes
