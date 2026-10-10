# -*- coding: utf-8 -*-
"""
topos.core.langjs —— JS 后端（正则级，**[U]**，PREREG/M5 §0 D-A）。
单元发现 / 调用边 / require 边 / seam 规则子集。输出契约与 Python 件对齐
（units dict 形状一致、layers {layer: set[(min,max)]}），使 M0–M4 链零改动复用。

诚实边界（PREREG §1）：动态 require、模板串方法、隐式调用不抓——召回缺口由
D-B Joern 金标对拍读数（E-M5-2），本件只保证"报出的边可指认"（precision 语义）。
T-M5-b：stdlib re 起步，不上 tree-sitter/babel。
"""
import os
import re

_SKIP_DIRS = {"node_modules", ".git", "dist", "build", "coverage", "test",
              "tests", "__pycache__", ".workbuddy"}

#: 函数形态（v0.1）：顶层 function 声明 / const|let|var fn = function|箭头 /
#: Name.prototype.fn = function / class 声明 + 缩进方法（粗口径）
_RE_FUNC = re.compile(
    r"^[ \t]*(?:async[ \t]+)?function[ \t*\n]+([A-Za-z_$][\w$]*)[ \t]*\(",
    re.M)
_RE_ARROW = re.compile(
    r"^[ \t]*(?:const|let|var)[ \t]+([A-Za-z_$][\w$]*)[ \t]*=[ \t]*"
    r"(?:async[ \t]*)?(?:function\b|\([^)]*\)[ \t]*=>|[A-Za-z_$][\w$]*[ \t]*=>)",
    re.M)
_RE_PROTO = re.compile(
    r"^[ \t]*([A-Za-z_$][\w$]*)\.prototype\.([A-Za-z_$][\w$]*)[ \t]*=[ \t]*"
    r"(?:async[ \t]*)?function", re.M)
_RE_CLASS = re.compile(r"^[ \t]*class[ \t]+([A-Za-z_$][\w$]*)", re.M)
_RE_METHOD = re.compile(
    r"^[ \t]{2,}(?:async[ \t]+)?([A-Za-z_$][\w$]*)[ \t]*\([^()]*\)[ \t]*\{",
    re.M)
#: 对象属性匿名函数：res.send = function(…) {（v0.1 缺口修补，express 主形态）
_RE_OBJFN = re.compile(
    r"^[ \t]*[\w$.]+\.\*?([A-Za-z_$][\w$]*)[ \t]*=[ \t]*"
    r"(?:async[ \t]*)?function[ \t]*\(", re.M)
#: 解构导入：const { a, b } = require('./x')
_RE_DESTRUCT = re.compile(
    r"(?:const|let|var)[ \t]*\{([^}]+)\}[ \t]*=[ \t]*require\s*\(\s*"
    r"['\"]([^'\"]+)['\"]\s*\)")
_RE_REQUIRE = re.compile(
    r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")
_RE_IMPORT = re.compile(
    r"^\s*import\s+[^;'\"\n]*['\"]([^'\"]+)['\"]", re.M)
_RE_CALL = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")
_RE_EVAL = re.compile(r"\b(eval|exec)\s*\(")

#: require 解析后缀协议（CommonJS）
_RESOLVE_SUFFIX = (".js", ".json", "")

_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "function",
             "typeof", "new", "super", "delete", "void"}


def _skip(rel_dir):
    return any(seg in _SKIP_DIRS for seg in rel_dir.split("/"))


def _brace_end(lines, start):
    """从 start 行起做花括号配平，返回结束行号（1-based）；配平失败退 start。"""
    bal = 0
    opened = False
    for i in range(start - 1, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                bal += 1
                opened = True
            elif ch == "}":
                bal -= 1
        if opened and bal <= 0:
            return i + 1
        if not opened and i > start - 1:
            return i + 1                      # 单表达式箭头：下一行止
    return len(lines)


def discover_units_js(root):
    """walk 目录 → JS 函数级 Unit（与 units.discover_units 同 dict 形状）。"""
    units = []
    for dirpath, dirs, files in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if rel_dir != ".":
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        if _skip(rel_dir if rel_dir != "." else ""):
            continue
        for fn in sorted(files):
            if not fn.endswith(".js") or fn.endswith(".min.js"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root).replace("\\", "/")
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    src = f.read()
            except OSError:
                continue
            lines = src.splitlines()
            cls_spans = []                        # (name, start, end) class 体范围
            for m in _RE_CLASS.finditer(src):
                ln = src[: m.start()].count("\n") + 1
                cls_spans.append((m.group(1), ln, _brace_end(lines, ln)))

            def _cls_of(ln):
                hit = None
                for cn, a, b in cls_spans:
                    if a <= ln <= b:
                        hit = cn                  # 命中最内层（后匹配者覆盖）
                return hit

            spans = []                            # (name, start, kind)
            taken = []                            # 已占用行段，防重叠
            for m in _RE_FUNC.finditer(src):
                ln = src[: m.start()].count("\n") + 1
                spans.append((m.group(1), ln, "function"))
            for m in _RE_ARROW.finditer(src):
                ln = src[: m.start()].count("\n") + 1
                spans.append((m.group(1), ln, "arrow"))
            for m in _RE_PROTO.finditer(src):
                ln = src[: m.start()].count("\n") + 1
                spans.append(("%s.prototype.%s" % (m.group(1), m.group(2)),
                              ln, "proto"))
            for m in _RE_OBJFN.finditer(src):
                ln = src[: m.start()].count("\n") + 1
                spans.append((m.group(1), ln, "objfn"))
            spans = [(nm, ln, k) for nm, ln, k in spans
                     if not any(a <= ln <= b for a, b, _ in taken)]
            for nm, ln, kind in spans:
                end = _brace_end(lines, ln)
                taken.append((ln, end, kind))
                qual = ("%s.%s" % (_cls_of(ln), nm) if _cls_of(ln) else nm)
                units.append({
                    "id": "%s::%s:%d" % (rel, qual, ln),
                    "file": rel, "name": qual,
                    "lineno": ln, "end_lineno": end,
                    "loc": end - ln + 1,
                    "src": "\n".join(lines[ln - 1: end]),
                })
            # class 缩进方法（顶层 function/箭头未占用的行段内）
            for m in _RE_METHOD.finditer(src):
                ln = src[: m.start()].count("\n") + 1
                # E-M5-2 对拍发现（2026-10-10）：switch/if/for/while 等
                # 控制流语句形态同构于方法声明 → 垃圾单元污染单元宇宙，滤除
                if m.group(1) in _KEYWORDS:
                    continue
                if any(a <= ln <= b for a, b, _ in taken):
                    continue
                end = _brace_end(lines, ln)
                taken.append((ln, end, "method"))
                qual = ("%s.%s" % (_cls_of(ln), m.group(1))
                        if _cls_of(ln) else m.group(1))
                units.append({
                    "id": "%s::%s:%d" % (rel, qual, ln),
                    "file": rel, "name": qual,
                    "lineno": ln, "end_lineno": end,
                    "loc": end - ln + 1,
                    "src": "\n".join(lines[ln - 1: end]),
                })
    return units


def nm_of(m):
    return m.group(1)


def _resolve_require(root, cur_file, spec):
    """CommonJS 相对/裸 spec → 仓内文件 relpath 或 None。"""
    if not spec.startswith("."):
        return None                        # 裸模块（node 内建/第三方）不建边
    base = os.path.dirname(os.path.join(root, cur_file))
    cand = os.path.normpath(os.path.join(base, spec))
    for suf in _RESOLVE_SUFFIX:
        p = cand + suf
        if os.path.isfile(p):
            return os.path.relpath(p, root).replace("\\", "/")
        p_idx = os.path.join(cand, "index.js")
        if suf == "" and os.path.isfile(p_idx):
            return os.path.relpath(p_idx, root).replace("\\", "/")
    return None


def _file_units(units):
    byfile = {}
    for i, u in enumerate(units):
        byfile.setdefault(u["file"], []).append(i)
    return byfile


def extract_layers_js(root, units):
    """调用边（call 层）：同文件名调用 + require 别名跨文件属性调用。
    返回 {layer: set[(min,max)]}，与 layers._extract_layers 同形状。
    require 扫描在**文件级**做（require 通常在顶层、不在函数 span 内），
    单元 span 内只扫调用点。"""
    byfile = _file_units(units)
    names = {}
    for i, u in enumerate(units):
        names.setdefault(u["file"], {})[u["name"].split(".")[-1]] = i
    # 文件级 require alias 表 + 裸模块外部名清单
    aliases = {}                          # file → {alias: target_file}
    external = {}                         # file → set(绑定到裸模块的绑定名)
    for f in sorted(byfile):
        p = os.path.join(root, f)
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                fsrc = fh.read()
        except OSError:
            continue
        amap = {}
        ext = set()
        for rm in _RE_REQUIRE.finditer(fsrc):
            tgt = _resolve_require(root, f, rm.group(1))
            head = fsrc[: rm.start()]
            am = re.search(
                r"(?:const|let|var)[ \t]+([A-Za-z_$][\w$]*)[ \t]*=[ \t]*$",
                head.split("\n")[-1])
            if tgt is None:
                # v0.2（E-M5-2 对拍发现）：裸模块绑定名记入外部名清单——
                # npm 包名（如 accepts）与同文件方法名撞名时，简单名解析
                # 不得把外部绑定解析成同文件单元（accepts×3 假边根因）
                if am:
                    ext.add(am.group(1))
                continue
            if am:
                amap[am.group(1)] = tgt
        for dm in _RE_DESTRUCT.finditer(fsrc):
            tgt = _resolve_require(root, f, dm.group(2))
            if tgt is None:
                continue
            for nm in dm.group(1).split(","):
                nm = nm.strip().split(":")[-1].strip()
                if nm:
                    amap[nm] = tgt
        aliases[f] = amap
        external[f] = ext
    layers = {"call": set()}
    # E-M5-2 对拍发现（2026-10-10）：单元 src 切片含嵌套函数体，嵌套内调用
    # 被同时归因到每一层外层单元（sendfile→onX 假边家族）。修复：调用点
    # 归属"最小包含单元"，只有 owner==i 才计入 i 的出边。
    spans = {}
    for i, u in enumerate(units):
        spans.setdefault(u["file"], []).append(
            (u["lineno"], u["end_lineno"], i))
    for f in spans:
        spans[f].sort(key=lambda x: (x[1] - x[0], x[0]))

    _RE_CHAIN_CALL = re.compile(
        r"\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(")

    def _own_calls(i, u):
        """span 内归属 i 自己（最小包含= i）的调用点 [(点链, 绝对行)]。"""
        base = u["lineno"]
        out = []
        for m in _RE_CHAIN_CALL.finditer(u["src"]):
            abs_ln = base + u["src"][: m.start()].count("\n")
            owner = None
            for a, b, k in spans.get(u["file"], []):
                if a <= abs_ln <= b:
                    owner = k
                    break
            if owner == i:
                out.append((m.group(1), abs_ln))
        return out

    for i, u in enumerate(units):
        # 同文件直接调用：取链尾名（仅归属 i 自己的调用点）
        for chain, _ln in _own_calls(i, u):
            _head, _sep, last = chain.rpartition(".")
            if _sep == "" and last in _KEYWORDS:
                continue
            if chain.split(".")[0] in external.get(u["file"], set()):
                continue                     # v0.2：外部绑定名不作同文件解析
            j = names.get(u["file"], {}).get(last)
            if j is not None and j != i:
                layers["call"].add((min(i, j), max(i, j)))
        # require 别名 → 跨文件调用（属性形态 alias.fn( + 裸名形态 alias(）
        for alias, tgt in aliases.get(u["file"], {}).items():
            for chain, _ln in _own_calls(i, u):
                if chain == alias:
                    j = names.get(tgt, {}).get(alias)
                    if j is not None and j != i:
                        layers["call"].add((min(i, j), max(i, j)))
                elif chain.startswith(alias + "."):
                    fnm = chain[len(alias) + 1:]
                    j = names.get(tgt, {}).get(fnm)
                    if j is not None:
                        layers["call"].add((min(i, j), max(i, j)))
    return {k: layers.get(k, set()) for k in ("call",)}


def extract_seams_js(root, units):
    """JS seam 规则子集 v0.1 [U]（PREREG/M5 §1 D-M5-1c）：
    R1 require 相对模块边 → +1（明示 conduit，文件级扫描）；
    R4 eval/exec 非字面量 → VETO（字面量豁免，文件级扫描、按行去重）。
    R2/R3 JS 等价物无机械信号 → v0.2 留白（诚实边界）。
    返回 (edges, vetoes)：edges=[(u_file, v_file, action, sign, evidence)]。
    """
    edges, vetoes = [], []
    seen_req, seen_veto = set(), set()
    files = sorted({u["file"] for u in units})
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                fsrc = fh.read()
        except OSError:
            continue
        flines = fsrc.splitlines()
        for m in _RE_REQUIRE.finditer(fsrc):
            tgt = _resolve_require(root, f, m.group(1))
            if tgt is None or (f, tgt) in seen_req:
                continue
            seen_req.add((f, tgt))
            ln = fsrc[: m.start()].count("\n") + 1
            edges.append((f, tgt, "public_call", 1,
                          [("%s:%d" % (f, ln),
                            "require(%s)" % m.group(1))]))
        for em in _RE_EVAL.finditer(fsrc):
            tail = fsrc[em.end(): em.end() + 60]
            if re.match(r"\s*['\"]", tail):
                continue                      # 字面量首参 → 豁免
            ln = fsrc[: em.end()].count("\n") + 1
            key = (f, ln, em.group(1))
            if key in seen_veto:
                continue
            seen_veto.add(key)
            vetoes.append(("%s:%d" % (f, ln), em.group(1), "non-literal arg"))
    return edges, vetoes
