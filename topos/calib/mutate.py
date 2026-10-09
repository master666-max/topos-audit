# -*- coding: utf-8 -*-
"""
topos.calib.mutate —— L2 变异注入（seeded defects）：给"召回下界"提供已知真值。
五类算子（PREREG/B2 E-B2-3）：常量替换 / 边界偏移 / 条件反转 / 删除调用 / 返回值变换。

诚实条款：
  - mutation score 只报**召回下界**——注入缺陷偏典型，会高估 Se（NASA seeded-defect 血统的已知批评）；
  - 干净版必须零误杀（测试不误报），否则整批作废；
  - 对静态信号源不可见的变异体登记为**盲区算子**，不冒充"已注入=可检测"；
  - **真值域条款**（E-B2-3 实测）：变异注入制造的是**语义型缺陷**，与锚点类信号源的
    能力域（语法模式型缺陷）几乎不重叠（实测 26 个变异体锚点正则命中 0 个）。
    因此 L2 只可用于标定**测试执行型信号源**的召回下界，**不可**用于估计锚点/结构类
    信号源的 Se——后者必须走 L1（执行正样本）或 L4（仲裁）。
"""
import ast
import os
import tempfile

OPS = ("const_replace", "boundary_shift", "cond_invert", "drop_call", "return_transform")

DROP_CALL_WHITELIST = ("validate", "check", "sanitize", "assert_safe", "normalize")


class _ConstReplacer(ast.NodeTransformer):
    def __init__(self, nth=0):
        self.nth = nth
        self.seen = 0
        self.hit = False

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            if self.seen == self.nth:
                node.value = node.value + 1
                self.hit = True
            self.seen += 1
        return node


class _BoundaryShifter(ast.NodeTransformer):
    SHIFT = {ast.LtE: ast.Lt, ast.GtE: ast.Gt, ast.Lt: ast.LtE, ast.Gt: ast.GtE}

    def __init__(self, nth=0):
        self.nth = nth
        self.seen = 0
        self.hit = False

    def visit_Compare(self, node):
        self.generic_visit(node)
        if self.seen == self.nth and node.ops:
            op = node.ops[0]
            if type(op) in self.SHIFT:
                node.ops[0] = self.SHIFT[type(op)]()
                self.hit = True
        self.seen += 1
        return node


class _CondInverter(ast.NodeTransformer):
    def __init__(self, nth=0):
        self.nth = nth
        self.seen = 0
        self.hit = False

    def visit_If(self, node):
        self.generic_visit(node)
        if self.seen == self.nth:
            node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            self.hit = True
        self.seen += 1
        return node


class _CallDropper(ast.NodeTransformer):
    def __init__(self, nth=0):
        self.nth = nth
        self.seen = 0
        self.hit = False

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            fn = node.value.func
            name = getattr(fn, "id", None) or getattr(fn, "attr", None)
            if name in DROP_CALL_WHITELIST:
                if self.seen == self.nth:
                    self.hit = True
                    return None          # 删除该语句
                self.seen += 1
        return node


class _ReturnTransformer(ast.NodeTransformer):
    def __init__(self, nth=0):
        self.nth = nth
        self.seen = 0
        self.hit = False

    def visit_Return(self, node):
        if self.seen == self.nth and node.value is not None:
            node.value = ast.BinOp(left=node.value, op=ast.Add(),
                                   right=ast.Constant(value=1))
            self.hit = True
        self.seen += 1
        return node


TRANSFORMERS = {"const_replace": _ConstReplacer,
                "boundary_shift": _BoundaryShifter,
                "cond_invert": _CondInverter,
                "drop_call": _CallDropper,
                "return_transform": _ReturnTransformer}


def mutant(src, op, nth=0):
    """对源码注入第 nth 个位点的一类变异 → (新源码, 是否命中位点)。"""
    if op not in TRANSFORMERS:
        raise ValueError("unknown mutation op: %s" % op)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None, False
    tr = TRANSFORMERS[op](nth=nth)
    tree = tr.visit(tree)
    ast.fix_missing_locations(tree)
    if not tr.hit:
        return None, False
    try:
        return ast.unparse(tree), True
    except Exception:
        return None, False


def count_sites(src):
    """各算子在该源码上的可变异位点数。"""
    out = {}
    for op in OPS:
        n = 0
        i = 0
        while i < 64:
            _s, hit = mutant(src, op, nth=i)
            if not hit:
                break
            n += 1
            i += 1
        out[op] = n
    return out


def run_tests(module_src, tests, workdir=None):
    """把源码落盘导入 → 跑 [(fn_name, args, expected)] → 返回 (通过数, 失败详情)。
    异常/断言失败都算测试失败（= 变异体被杀）。"""
    tmp = workdir or tempfile.mkdtemp(prefix="topos-mut-")
    path = os.path.join(tmp, "_mut_target.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(module_src)
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("_mut_target_%d" % id(module_src), path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        return 0, ["导入失败: %s" % e]
    fails = []
    for name, args, expected in tests:
        fn = getattr(mod, name, None)
        if fn is None:
            fails.append("%s 不存在" % name)
            continue
        try:
            got = fn(*args)
        except Exception as e:
            fails.append("%s%r 抛异常 %s" % (name, args, type(e).__name__))
            continue
        if got != expected:
            fails.append("%s%r = %r != %r" % (name, args, got, expected))
    return len(tests) - len(fails), fails
