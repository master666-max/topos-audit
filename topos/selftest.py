# -*- coding: utf-8 -*-
"""
topos.selftest —— 契约自检（工单 B1 出口判据：12 项全绿）。
判据先于实现（工单 WORK-ORDERS 附录 A 映射）：
  c01 单元发现  c02 五类边  c03 融合权重  c04 Lanczos 残差  c05 清单解耦验收
  c06 切片算子  c07 布尔组合  c08 空池/constraints  c09 覆盖诊断  c10 sheaf H⁰（合成版）
  c11 缺 git → None（ADR-A12）  c12 观测退化（Se=Sp=1）
（工单附录 A #11"解码输出契约"归 W5/B3，加入后套件变 13 项。）
全部跑在系统临时目录（不在任何 git 仓内，c11 的降级判定才真实）。
"""
import copy
import json
import os
import shutil
import tempfile
import traceback

from topos.core.units import discover_units
from topos.core.layers import _extract_layers
from topos.core.fuse import fuse
from topos.core.embed import diffusion_embedding
from topos.core import sheaf
from topos.axis.manifest import load_manifest
from topos.pool.slicer import compile_slicer
from topos.pool.pool import eval_expr
from topos.pool.design import build_design, coverage
from topos.infer.observe import SynthOracle
from topos.space import Space
from topos.axis.methods.git_history import git_churn, git_field

# 五类边全覆盖合成仓（对齐 mini-lab space_mini 自检语义）
SYNTH = '''\
G_STATE = 0
SHARED_LIMIT = 10

def probe():
    return G_STATE < SHARED_LIMIT

def gate(x):
    if probe():
        return process(x)
    return None

def process(x):
    data = load(x)
    return finish(data)

def load(x):
    global G_STATE
    return x * SHARED_LIMIT

def finish(d):
    return str(d)

def passthrough(x):
    v = load(x)
    sink(v)
    return v

def sink(v):
    return v + 1

def todo_fn(x):
    y = x + 1  # TODO: fix marker
    return y
'''

TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_synth(workdir):
    d = os.path.join(workdir, "synth")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "app.py"), "w", encoding="utf-8") as f:
        f.write(SYNTH)
    return d


def c01_units(w):
    d = _make_synth(w)
    units = discover_units(d)
    names = [u["name"] for u in units]
    assert len(units) == 8, "单元数 %d != 8" % len(units)
    assert "probe" in names and "todo_fn" in names
    tf = next(u for u in units if u["name"] == "todo_fn")
    assert tf["loc"] == 3, "todo_fn loc=%d != 3" % tf["loc"]


def c02_layers(w):
    d = _make_synth(w)
    units = discover_units(d)
    idx = {u["name"]: i for i, u in enumerate(units)}
    ly = _extract_layers(d, units)
    e = lambda a, b: (min(idx[a], idx[b]), max(idx[a], idx[b]))
    assert e("probe", "gate") in ly["control"], "control 边缺失 probe→gate"
    assert e("gate", "process") in ly["return"] and e("process", "finish") in ly["return"], \
        "return 边缺失"
    for pair in (("process", "load"), ("passthrough", "load")):
        assert e(*pair) in ly["data"], "data 边缺失 %s" % (pair,)
    assert e("finish", "load") in ly["data"], "值穿越 load→finish 缺失"
    assert e("sink", "load") in ly["data"], "值穿越 load→sink 缺失"
    assert ly["vardep"] == {e("probe", "load")}, "vardep 应恰为 probe↔load: %r" % ly["vardep"]
    for pair in (("probe", "gate"), ("gate", "process"), ("process", "load"),
                 ("process", "finish"), ("passthrough", "load"), ("passthrough", "sink")):
        assert e(*pair) in ly["call"]


def c03_fuse(w):
    layers = {"call": {(0, 1)}, "data": {(0, 1)}, "vardep": {(0, 2)}}
    fused = fuse(layers, {"data": 2.0})
    assert abs(fused[(0, 1)] - 3.0) < 1e-12, "w=α_call+α_data 应=3.0"
    assert abs(fused[(0, 2)] - 1.0) < 1e-12


def c04_lanczos(w):
    d = _make_synth(w)
    sp = Space(d)
    assert abs(sp.lam_residual) < 1e-6, "λ₁ 残差 %r ≥ 1e-6" % sp.lam_residual
    assert sp.embed_dims >= 1


def c05_decouple(w):
    """解耦验收：仅写临时清单（新增场+切片+组合池），引擎零改动，新池产出。"""
    d = _make_synth(w)
    mf2 = {
        "version": 3,
        "layers": {"call": 1.0},
        "fields": [
            {"name": "todo", "layer": "L", "method": "regex",
             "params": {"patterns": [["todo:marker", "TODO"]]}},
        ],
        "slicers": [
            {"name": "todo:any", "field": "todo", "op": "notnull"},
        ],
        "pools": [
            {"name": "p_todo", "expr": {"any": ["todo:any"]}},
        ],
        "constraints": {"min_pool_size": 1},
    }
    mf_path = os.path.join(w, "manifest2.json")
    with open(mf_path, "w", encoding="utf-8") as f:
        json.dump(mf2, f, ensure_ascii=False)
    sp = Space(d, mf_path)
    names = [nm for nm, _m in sp.rows]
    assert "p_todo" in names, "仅改清单新增的池未产出: %r" % names
    todo_pool = dict(sp.rows)["p_todo"]
    assert len(todo_pool) >= 1 and any(u["name"] == "todo_fn" for u in
                                      [sp.units[i] for i in todo_pool])


def c06_slicers(w):
    f_list = {0: ["eval"], 1: None, 2: ["exec"], 3: []}
    specs = [
        {"name": "x:*", "field": "f", "op": "expand"},
        {"name": "has_a", "field": "f", "op": "has", "value": "eval"},
        {"name": "nn", "field": "f", "op": "notnull"},
    ]
    got = {}
    for spec in specs:
        for nm, members in compile_slicer(spec, {"f": f_list}):
            got[nm] = members
    assert got["x:eval"] == {0} and got["x:exec"] == {2}, got
    assert got["has_a"] == {0}
    assert got["nn"] == {0, 2}
    f_num = {0: 10, 1: 3, 2: 7, 3: None}
    base = {"field": "g"}
    q = {}
    for spec in (dict(base, name="gt5", op="gt", value=5),
                 dict(base, name="qgt", op="quantile_gt", q=0.5),
                 dict(base, name="bq", op="between_q", q_lo=0.33, q_hi=0.67)):
        nm, members = compile_slicer(spec, {"g": f_num})[0]
        q[nm] = members
    assert q["gt5"] == {0, 2}, "gt 5 on {10,3,7} 应为 {0,2}"
    assert q["qgt"] == {0}, "分位 0.5 of [3,7,10]=7 → >7 应只含 10"
    assert q["bq"] == {2}, "between(3,7] 应恰含 7"
    f_none = {i: None for i in range(4)}
    nm, members = compile_slicer({"name": "t", "field": "z", "op": "quantile_gt",
                                  "q": 0.5}, {"z": f_none})[0]
    assert members == set(), "全 None 场切片应为空且不抛"


def c07_bool(w):
    slices = {"a": {0, 1}, "b": {1, 2}, "c": {0}}
    n = 4
    assert eval_expr({"all": ["a", "b"]}, slices, n) == {1}
    assert eval_expr({"any": ["a", "c"]}, slices, n) == {0, 1}
    assert eval_expr({"not": "b"}, slices, n) == {0, 3}
    nested = {"all": [{"any": ["a", "c"]}, {"not": "b"}]}
    assert eval_expr(nested, slices, n) == {0}


def c08_design(w):
    rows, warns = build_design(
        [("empty", set()), ("tiny", {0}), ("wide", set(range(100))), ("ok", {1, 2, 3})],
        100, {"max_width": 60, "max_pools": 64, "min_pool_size": 3})
    assert [nm for nm, _m in rows] == ["ok"], rows
    assert len(warns) == 3, warns
    rows2, warns2 = build_design([("a", {i for i in range(10)})], 10,
                                 {"max_pools": 1})
    assert len(rows2) == 1 and not warns2


def c09_coverage(w):
    cov = coverage([("a", {0, 1}), ("b", {1, 2})], 4)
    assert cov["c_min"] == 0 and cov["zero_cover_rate"] == 0.25
    assert cov["c_mean"] == 1.0 and cov["pool_sizes"] == [2, 2]
    assert cov["n_pools"] == 2


def c10_sheaf(w):
    # 干净三角（全 +1）→ H⁰=1；frustrated（一条 −1）→ H⁰=0（X5a 合成版）
    clean = sheaf.sheaf_laplacian(3, [(0, 1, 1), (1, 2, 1), (0, 2, 1)])
    assert sheaf.h0_dimension(clean) == 1
    frustr = sheaf.sheaf_laplacian(3, [(0, 1, 1), (1, 2, 1), (0, 2, -1)])
    assert sheaf.h0_dimension(frustr) == 0
    e_res, r_s = sheaf.residuals(3, [(0, 1, 1), (1, 2, 1), (0, 2, -1)], {0: 1, 1: 1, 2: 1})
    assert e_res[(0, 2)] > 0 and r_s[2] > 0
    r_tv = sheaf.tv_residuals({0: {1, 2}, 1: {0, 2}, 2: {0, 1}}, {0: 1, 1: 1, 2: 1})
    assert all(v == 0 for v in r_tv.values()), "TV 对符号矛盾应结构性看不见（X5c）"


def c11_no_git(w):
    """系统临时目录不在任何 git 仓内 → 演化场全 None（ADR-A12：不填 0）。"""
    d = _make_synth(w)          # w 本身在 %TEMP%，不在 git 仓
    units = discover_units(d)
    assert git_churn(d, [u["file"] for u in units]) is None, \
        "非 git 目录 git_churn 应返回 None"
    f = git_field(units, {"metric": "commits"}, {"root": d})
    assert all(v is None for v in f.values()), "演化场应全 None: %r" % f


def c12_observe_degenerate(w):
    """Se=Sp=1 时观测退化为干净 OR（观测模型正确性底线）。"""
    o = SynthOracle(truth={1}, se=1.0, sp=1.0, seed=7)
    res = o.observe_all([("p1", {0, 1}), ("p2", {2, 3})])
    assert res == [("p1", 1), ("p2", 0)], res


def c13_path_not_skipped(w):
    """回归防护：目标仓位于含 .workbuddy/.git 的**父路径**下时必须仍能发现单元
    （E-B2-4 抽样踩到的 bug：用绝对路径段过滤 → 整仓返回 0 单元）。"""
    base = os.path.join(w, ".workbuddy", "binaries", "python", "proj")
    os.makedirs(base)
    with open(os.path.join(base, "a.py"), "w", encoding="utf-8") as f:
        f.write("def f(x):\n    return x + 1\n")
    units = discover_units(base)
    assert len(units) == 1, "父路径含 .workbuddy 时单元数 %d != 1" % len(units)
    # 仓**内部**的 .git / __pycache__ 仍应被跳过
    os.makedirs(os.path.join(base, "__pycache__"))
    with open(os.path.join(base, "__pycache__", "b.py"), "w", encoding="utf-8") as f:
        f.write("def g(x):\n    return x\n")
    units2 = discover_units(base)
    assert len(units2) == 1, "仓内 __pycache__ 未被跳过: %d" % len(units2)


CHECKS = [
    ("c01 单元发现", c01_units),
    ("c02 五类耦合边", c02_layers),
    ("c03 融合图权重 Σα", c03_fuse),
    ("c04 Lanczos 残差 <1e-6", c04_lanczos),
    ("c05 清单解耦验收（仅改清单）", c05_decouple),
    ("c06 切片算子全集（含全 None 场）", c06_slicers),
    ("c07 布尔嵌套 all/any/not", c07_bool),
    ("c08 空池丢弃 + constraints", c08_design),
    ("c09 覆盖三诊断", c09_coverage),
    ("c10 sheaf H⁰（合成版，真实语义=B5）", c10_sheaf),
    ("c11 缺 git → None（ADR-A12）", c11_no_git),
    ("c12 观测退化 Se=Sp=1", c12_observe_degenerate),
    ("c13 父路径含 .workbuddy 仍可发现单元", c13_path_not_skipped),
]


def run_all(verbose=True):
    workdir = tempfile.mkdtemp(prefix="topos-selftest-")
    ok = 0
    try:
        for name, fn in CHECKS:
            try:
                fn(workdir)
                ok += 1
                if verbose:
                    print("PASS %s" % name)
            except Exception:
                if verbose:
                    print("FAIL %s\n%s" % (name, traceback.format_exc()))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    if verbose:
        print("=" * 56)
        print("selftest %d/%d PASS" % (ok, len(CHECKS)))
    return ok, len(CHECKS)


if __name__ == "__main__":
    ok, total = run_all()
    raise SystemExit(0 if ok == total else 1)
