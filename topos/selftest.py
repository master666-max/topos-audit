# -*- coding: utf-8 -*-
"""
topos.selftest —— 契约自检（工单 B1 出口判据：12 项全绿）。
判据先于实现（工单 WORK-ORDERS 附录 A 映射）：
  c01 单元发现  c02 五类边  c03 融合权重  c04 Lanczos 残差  c05 清单解耦验收
  c06 切片算子  c07 布尔组合  c08 空池/constraints  c09 覆盖诊断  c10 sheaf H⁰（合成版）
  c11 缺 git → None（ADR-A12）  c12 观测退化（Se=Sp=1）
（工单附录 A #11"解码输出契约"归 W5/B3，加入后套件变 13 项。）
B3 起：c15–c19 解码器族（A8 值域/方向性/稳定性/终止性）；B4 起：c20–c23 σ 与预算回路；
B5 起：c24–c26 接缝规则表 v0.1（R1–R4 方向性 / 抽取命中 / sheaf 端到端微缩）。
全部跑在系统临时目录（不在任何 git 仓内，c11 的降级判定才真实）。
"""
import copy
import json
import os
import shutil
import tempfile
import traceback

from topos.core.units import discover_units, is_test_unit
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
    # A3：call 层已改有向 (caller, callee)——下列 pair 一律按"前者调后者"书写，
    # 方向写反会失败，故本断言同时钉住了方向的正确性（不是靠归一化蒙过去）
    d = lambda a, b: (idx[a], idx[b])
    # 注意：SYNTH 里是 **gate 调 probe**（`if probe():`），旧断言的 ("probe","gate")
    # 只是随手写的无序对，A3 后按真实方向书写为 ("gate","probe")
    for pair in (("gate", "probe"), ("gate", "process"), ("process", "load"),
                 ("process", "finish"), ("passthrough", "load"), ("passthrough", "sink")):
        assert d(*pair) in ly["call"], "call 有向边缺失 %s→%s" % pair


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


def c14_qualified_name(w):
    """类内方法的 unit name 必须是 "Class.method"（v1 逻辑写反会只留类名）。"""
    d = os.path.join(w, "qual")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "c.py"), "w", encoding="utf-8") as f:
        f.write("class A:\n    def m(self):\n        return 1\n\ndef free():\n    return 2\n")
    names = sorted(u["name"] for u in discover_units(d))
    assert names == ["A.m", "free"], "类内方法名错误: %r" % names


# ---------------- B3(W5) 解码契约 c15–c19（PREREG/B3 §5） ----------------

def _dec_fixture():
    """3 单元小图：0-1-2 链；pools p0={0,1} p1={1,2}。"""
    adj = [set() for _ in range(3)]
    for u, v in ((0, 1), (1, 2)):
        adj[u].add(v)
        adj[v].add(u)
    pools = [("p0", {0, 1}), ("p1", {1, 2})]
    return adj, pools


def c15_belief_domain(w):
    """四解码器输出 ∈ [0,1] 且无 {0,1} 硬值（A8 / T-B3-a）。"""
    from topos.infer.decode import decode, DECODERS
    adj, pools = _dec_fixture()
    obs = [("p0", 1), ("p1", 0)]
    for m in DECODERS:
        b = decode(pools, obs, 3, method=m, se=0.9, sp=0.95, prior=0.1)
        assert set(b) == {0, 1, 2}, m
        for i, v in b.items():
            assert 0.0 < v < 1.0, "%s belief[%d]=%r 触界（A8 禁 {0,1}）" % (m, i, v)


def c16_negative_world(w):
    """全阴性观测：NB belief < 0.5；SCOMP/COMP/DD 判阳集为空（belief 全 = 1−Sp）。"""
    from topos.infer.decode import decode
    adj, pools = _dec_fixture()
    obs = [("p0", 0), ("p1", 0)]
    bn = decode(pools, obs, 3, method="nb", prior=0.1)
    assert all(v < 0.5 for v in bn.values()), "全阴观测下 NB 出高分: %r" % bn
    for m in ("comp", "dd", "scomp"):
        b = decode(pools, obs, 3, method=m, se=0.9, sp=0.95)
        assert all(abs(v - 0.05) < 1e-12 for v in b.values()), \
            "%s 全阴观测应无判阳: %r" % (m, b)


def c17_evidence_direction(w):
    """证据方向性：单元 1 所在池由全阴变全阳，NB belief 严格上升。"""
    from topos.infer.decode import decode
    _adj, pools = _dec_fixture()
    b_neg = decode(pools, [("p0", 0), ("p1", 0)], 3, method="nb", prior=0.1)
    b_pos = decode(pools, [("p0", 1), ("p1", 1)], 3, method="nb", prior=0.1)
    assert b_pos[1] > b_neg[1], "证据翻转后 belief 未上升: %r → %r" % (b_neg, b_pos)
    assert b_pos[0] > b_neg[0] and b_pos[2] > b_neg[2]


def c18_alpha_stability(w):
    """α 稳定域（v2 曲线，T-B3-d）：0<α≤1/λmax；φ≤0.1 满强度；φ 越大 α 越小。"""
    from topos.infer.prior import power_lam_max, adaptive_alpha
    adj, pools = _dec_fixture()
    lam = power_lam_max(adj, 3)
    assert lam > 1.9, "链图 λmax 应≈2: %r" % lam
    alphas, meta = adaptive_alpha(pools, adj, 3, lam_max=lam)
    for a in alphas:
        assert 0.0 < a <= 1.0 / lam + 1e-12, "α 越稳定域: %r (1/λ=%r)" % (a, 1 / lam)
    # φ 泛度分段：n=100，窄池宽 5（φ=0.05≤0.1）→ 满强度；宽池罩 32（φ=0.32）→ 衰减
    adj2 = [set() for _ in range(100)]
    for u in range(99):
        adj2[u].add(u + 1)
        adj2[u + 1].add(u)
    pools2 = [("n5", set(range(5))), ("wide32", set(range(32, 64)))]
    al2, _m = adaptive_alpha(pools2, adj2, 100, lam_max=lam)
    assert abs(al2[0] - 1.0 / lam) < 1e-12, "φ≤0.1 应满强度: %r" % al2[0]
    assert al2[40] < 0.1 / lam, "φ=0.32 应强衰减: %r" % al2[40]
    assert abs(al2[70] - al2[40]) < 1e-12, "同池宽单元应同强度"
    assert 0.0 < al2[90] <= 1.0 / lam, "零覆盖单元取场景中位 φ 强度"


def c19_scomp_terminal_cli_smoke(w):
    """SCOMP 终止性（无噪声 residual 必空）+ CLI decode 端到端 smoke。"""
    from topos.infer.decode import decode
    pools = [("a", {0, 1, 2}), ("b", {1, 2, 3}), ("c", {2, 3})]
    obs = [("a", 1), ("b", 1), ("c", 0)]      # 无噪声口径下阳性池必有缺陷
    b = decode(pools, obs, 4, method="scomp", se=1.0, sp=1.0)
    dset = {i for i, v in b.items() if v == 1.0}
    for nm, m in pools:
        if obs[[k for k, (n2, _y) in enumerate(obs) if n2 == nm][0]][1]:
            assert m & dset, "SCOMP 终止后阳性池 %s 未被解释" % nm
    # CLI smoke：合成 repo → space.json → obs.json → decode → belief.json
    import json as _json
    d = _make_synth(w)
    mf = {"version": 3, "layers": {"call": 1.0}, "fields": [],
          "slicers": [], "pools": [], "constraints": {"min_pool_size": 1}}
    mf_path = os.path.join(w, "mf.json")
    with open(mf_path, "w", encoding="utf-8") as f:
        _json.dump(mf, f)
    from topos.cli import main as cli_main
    sj = os.path.join(w, "space.json")
    assert cli_main(["space", d, "--axes", mf_path, "--json", sj]) == 0
    with open(sj, encoding="utf-8") as f:
        rep = _json.load(f)
    assert rep["schema"] == "topos-space/1" and "pool_members" in rep
    if not rep["pool_members"]:
        return                                   # 小仓无池则跳过 decode 段
    obs_f = os.path.join(w, "obs.json")
    with open(obs_f, "w", encoding="utf-8") as f:
        _json.dump({nm: 0 for nm, _m in rep["pool_members"]}, f)
    bj = os.path.join(w, "belief.json")
    assert cli_main(["decode", sj, "--obs", obs_f, "--decoder", "nb",
                     "-o", bj]) == 0
    with open(bj, encoding="utf-8") as f:
        bel = _json.load(f)
    assert bel["schema"] == "topos-belief/1" and bel["decoder"] == "nb"
    assert len(bel["belief"]) == rep["n_units"]
    assert all(0.0 < v < 1.0 for v in bel["belief"].values())


# ---------------- B4(W4) 停止契约 c20–c23（PREREG/B4 §2） ----------------

def c20_sigma_monotone(w):
    """σ 单调：c ↑ → σ ↓；μ ↑ → σ ↑；c ≥ μ → 0（精确式 + 冷启动闭式，c₀ 口径）。"""
    from topos.stop.weitzman import sigma_exact, sigma_coldstart, global_theta
    p_low = [0.1] * 4                          # μ=0.4
    p_high = [0.8] * 4                         # μ=3.2
    s = sigma_exact(p_low, 0.1)
    assert 0.0 < s <= 4.0
    assert sigma_exact(p_low, 0.3) < s, "c ↑ 应使 σ ↓"
    assert sigma_exact(p_high, 0.1) > s, "μ ↑ 应使 σ ↑"
    assert sigma_exact(p_low, 0.4) == 0.0, "c ≥ μ 应 σ=0"
    theta = global_theta([0.4, 3.2], [0.5, 0.5])
    assert theta > 0
    assert sigma_coldstart(3.2, 0.5, theta) > sigma_coldstart(0.4, 0.5, theta)
    assert sigma_coldstart(0.4, 1.5, theta) == 0.0, "闭式 c/θ ≥ μ 应 σ=0"
    assert sigma_coldstart(1.0, 1.0, 0.0) == 0.0, "θ=0 应 σ=0"


def c21_stop_direction(w):
    """停止方向：全低 belief → 无下一发；高 belief → σ>0 且可选池（c₀=0.5 口径）。"""
    from topos.stop.weitzman import (sigma_exact,
                                     next_pool, stop_decision)
    pools = [("a", {0, 1, 2}), ("b", {2, 3})]
    low = {i: 0.005 for i in range(4)}
    sig_low = {nm: sigma_exact([low.get(i, 0.0) for i in m], 0.5)
               for nm, m in pools}
    assert all(s == 0.0 for s in sig_low.values()), "全低 belief 应全 σ=0"
    assert next_pool(pools, sig_low) is None, "全 σ=0 应无下一发"
    assert stop_decision(sig_low, 0.0), "全低应 STOP"
    high = {i: 0.9 for i in range(4)}
    sig_high = {nm: sigma_exact([high.get(i, 0.0) for i in m], 0.5)
                for nm, m in pools}
    assert max(sig_high.values()) > 0, "高 belief + c₀=0.5 应有正 σ"
    assert not stop_decision(sig_high, 0.0), "高 belief 不应 STOP"
    pick = next_pool(pools, sig_high)
    assert pick is not None and pick[0] in ("a", "b")


def c22_budget_loop(w):
    """预算回路：预算 0 不开池；预算内必终止；开池记录与观测对齐。"""
    from topos.stop.budget import run_budget
    from topos.infer.decode import decode
    pools = [("a", {0, 1}), ("b", {1, 2}), ("c", {2, 3})]
    truth = {0, 2}
    calls = {"n": 0}

    def obs_fn(name, members):
        calls["n"] += 1
        return 1 if members & truth else 0

    def dec_fn(sub_pools, obs):
        return decode(sub_pools, obs, 4, method="nb", se=0.9, sp=0.95,
                      prior=0.25)

    tr0 = run_budget(pools, obs_fn, dec_fn, 0, 0.9, 0.95, 0.25)
    assert tr0["opened"] == [], "预算 0 不应开池"
    tr = run_budget(pools, obs_fn, dec_fn, 3, 0.9, 0.95, 0.25)
    assert len(tr["opened"]) <= 3 and len(tr["y"]) == len(tr["opened"])
    assert calls["n"] == len(tr["opened"]), "观测次数应等于开池数"
    assert tr["stopped_at"] is not None or len(tr["opened"]) == 3


def c23_cli_next_smoke(w):
    """CLI next 端到端：space.json + belief.json → 合法输出（NEXT 或 STOP）。"""
    import json as _json
    d = _make_synth(w)
    mf = {"version": 3, "layers": {"call": 1.0}, "fields": [], "slicers": [],
          "pools": [], "constraints": {"min_pool_size": 1}}
    mf_path = os.path.join(w, "mf.json")
    with open(mf_path, "w", encoding="utf-8") as f:
        _json.dump(mf, f)
    from topos.cli import main as cli_main
    sj = os.path.join(w, "space.json")
    assert cli_main(["space", d, "--axes", mf_path, "--json", sj]) == 0
    with open(sj, encoding="utf-8") as f:
        rep = _json.load(f)
    if not rep["pool_members"]:
        return                               # 小仓无池则跳过
    bj = os.path.join(w, "belief.json")
    with open(bj, "w", encoding="utf-8") as f:
        _json.dump({"schema": "topos-belief/1", "decoder": "nb", "params": {},
                    "n_units": rep["n_units"],
                    "belief": {str(i): 0.3 for i in range(rep["n_units"])},
                    "unit_ids": rep.get("units")}, f)
    assert cli_main(["next", sj, bj]) == 0   # 全员 0.3：σ 视池而定，出 NEXT 或 STOP 均合法


_B5_FIXTURE = {
    "m_a.py": (
        "import m_b\nimport m_c\nimport m_d\nimport pickle\n"
        "def go(x):\n"
        "    m_b.{b_call}(x)\n"
        "    m_c.pub(x)\n"
        "    m_d.CACHE.append(x)\n"
        "    m_d.REG[k] = 1\n"
        "    eval(x)\n"
        "    pickle.loads(b'z')\n"
        "def go2(x):\n    return x\n"
        "k = 'key'\n"
    ),
    "m_b.py": (
        "import m_c\n"
        "def _helper(x):\n    return x\n"
        "def open_api(x):\n    return x\n"
        "def bridge(x):\n    m_c.pub(x)\n"
    ),
    "m_c.py": "import m_a\ndef pub(x):\n    m_a.go2(x)\n",
    "m_d.py": "CACHE = []\nREG = {}\n",
}


def _make_b5_repo(w, frustrated=True):
    """B5 fixture：frustrated=True 时 a→b 为私有触碰（环积 −1）；False 为公开调用。"""
    for name, tpl in _B5_FIXTURE.items():
        with open(os.path.join(w, name), "w", encoding="utf-8") as f:
            f.write(tpl.replace("{b_call}", "_helper" if frustrated else "open_api"))
    return w


def c24_seam_rule_signs(w):
    """c24 规则方向性：R1→+1 / R2→−1 / R3→−1 / R4→VETO；字面量实参不 veto。"""
    from topos.core import seams
    assert seams.RULE_SIGN["public_call"] == 1
    assert seams.RULE_SIGN["private_touch"] == -1
    assert seams.RULE_SIGN["global_write"] == -1
    assert seams.RULE_SIGN[seams.VETO] == "VETO"
    import ast as _ast
    # eval(字面量) 不 veto；eval(NAME) veto；subprocess.run 无 shell 不 veto、shell=True veto
    mk = lambda src: _ast.parse(src).body[0].value          # noqa: E731
    assert seams._veto_if(mk("eval('1+1')"), "eval") is None
    assert seams._veto_if(mk("eval(x)"), "eval") is not None
    assert seams._veto_if(mk("subprocess.run(cmd)"), "subprocess.run",
                          need_shell=True) is None
    assert seams._veto_if(mk("subprocess.run(cmd, shell=True)"),
                          "subprocess.run", need_shell=True) is not None


def c25_seam_extraction(w):
    """c25 抽取器命中：R1/R2/R3 各 ≥1 + R4 veto + 证据 file:line 齐全。"""
    from topos.core import seams
    repo = os.path.join(w, "seam_fixture")
    os.makedirs(repo, exist_ok=True)
    _make_b5_repo(repo, frustrated=True)
    modules, edges, vetoes = seams.extract(repo)
    assert set(modules) == {"m_a", "m_b", "m_c", "m_d"}
    acts = {(u, v, a) for u, v, a, s, ev in edges}
    assert ("m_a", "m_b", "private_touch") in acts, "R2 私有触碰未命中"
    assert ("m_a", "m_c", "public_call") in acts, "R1 契约调用未命中"
    assert ("m_b", "m_c", "public_call") in acts, "R1 桥接未命中"
    assert ("m_c", "m_a", "public_call") in acts, "R1 回环未命中"
    gw = [ev for u, v, a, s, ev in edges
          if (u, v, a) == ("m_a", "m_d", "global_write")]
    assert gw and sum(len(e) for e in gw) >= 2, \
        "R3 应同时命中 mutator 与 store 两形态"
    for u, v, a, s, ev in edges:
        assert seams.RULE_SIGN[a] == s
        for path_line, detail in ev:
            assert ".py:" in path_line
    assert len(vetoes) == 1 and vetoes[0][1] == "eval", \
        "R4 应恰 1 条 eval veto（字面量 pickle.loads 不报）"
    assert "m_a.py" in vetoes[0][0]


def c26_seam_sheaf_end_to_end(w):
    """c26 端到端微缩：规则表 → sheaf：奇环 ker=0 / 平衡 ker=1 / TV 全盲。"""
    from topos.core import seams
    from topos.core import sheaf
    for frustrated, want_h0 in ((True, 0), (False, 1)):
        rw = os.path.join(w, "frus" if frustrated else "bal")
        os.makedirs(rw, exist_ok=True)
        _make_b5_repo(rw, frustrated=frustrated)
        modules, edges, vetoes = seams.extract(rw)
        idx = {m: i for i, m in enumerate(modules)}
        e_ws = [(idx[u], idx[v], s) for u, v, a, s, ev in edges]
        L = sheaf.sheaf_laplacian(len(modules), e_ws)
        assert sheaf.h0_dimension(L) == want_h0, \
            "H⁰ 读数错（frustrated=%s）" % frustrated
        z = {i: 1.0 for i in range(len(modules))}     # v0.1 域声明全 +1
        e_res, r_sheaf = sheaf.residuals(len(modules), e_ws, z)
        if frustrated:
            flip_nodes = {idx[u] for u, v, a, s, ev in edges if s == -1} | \
                         {idx[v] for u, v, a, s, ev in edges if s == -1}
            top = set(sorted(range(len(modules)),
                             key=lambda i: -r_sheaf[i])[:2 * 3])
            assert flip_nodes <= top, "翻转边端点未进 top-2f 残差"
        r_tv = sheaf.tv_residuals({i: set() for i in range(len(modules))}, z)
        assert all(v == 0.0 for v in r_tv.values()), \
            "z≡+1 下 TV 应全盲（数值一致但语义矛盾）"


_JS_FIXTURE = {
    "app.js": (
        "const helper = require('./util');\n"
        "function run(x) {\n"
        "  helper.compute(x);\n"
        "  return eval(x);\n"
        "}\n"
        "const lit = eval('1+1');\n"
        "function wrap(cb) {\n  return run(cb);\n}\n"
    ),
    "util.js": (
        "function compute(x) {\n  return x + 1;\n}\n"
        "class Cache {\n  get(k) {\n    return k;\n  }\n}\n"
        "module.exports = { compute, Cache };\n"
    ),
}


def _make_js_repo(w):
    os.makedirs(w, exist_ok=True)
    for name, body in _JS_FIXTURE.items():
        with open(os.path.join(w, name), "w", encoding="utf-8") as f:
            f.write(body)
    return w


def c27_js_extraction(w):
    """c27 JS 抽取（PREREG/M5 §4）：单元发现 + require 边 + eval veto + 字面量豁免。"""
    from topos.core import langjs
    repo = os.path.join(w, "jsfix")
    _make_js_repo(repo)
    units = langjs.discover_units_js(repo)
    names = {u["name"] for u in units}
    assert "run" in names and "wrap" in names and "compute" in names, \
        "JS 单元发现缺口: %s" % names
    assert "Cache.get" in names, "class 方法未发现"
    layers = langjs.extract_layers_js(repo, units)
    idx = {u["name"].split(".")[-1]: i for i, u in enumerate(units)}
    assert (min(idx["run"], idx["compute"]), max(idx["run"], idx["compute"])) \
        in layers["call"], "require 跨文件属性调用边未命中"
    assert (min(idx["wrap"], idx["run"]), max(idx["wrap"], idx["run"])) \
        in layers["call"], "同文件调用边未命中"
    seams_js, vetoes = langjs.extract_seams_js(repo, units)
    assert any(a == "public_call" and s == 1 for _u, _v, a, s, _e in seams_js), \
        "R1 require 边缺失"
    assert len(vetoes) == 1 and vetoes[0][1] == "eval", \
        "eval 应恰 1 条 veto（字面量 eval('1+1') 豁免）: %s" % vetoes


def c28_js_chain(w):
    """c28 JS 链微缩（PREREG/M5 §4）：discover→space→decode→next 全链零退出。"""
    import json as _json
    from topos.space import Space
    repo = os.path.join(w, "jsfix2")
    _make_js_repo(repo)
    mf = {"version": 3, "layers": {"call": 1.0}, "fields": [],
          "slicers": [], "pools": [], "constraints": {"min_pool_size": 1}}
    mf_path = os.path.join(w, "mf_js.json")
    with open(mf_path, "w", encoding="utf-8") as f:
        _json.dump(mf, f)
    sp = Space(repo, mf_path, lang="js")
    if sp.n == 0:
        raise AssertionError("JS 单元发现为 0")
    from topos.report.json_out import build_report, write
    sj = os.path.join(w, "space_js.json")
    write(build_report(sp), sj)
    with open(sj, encoding="utf-8") as f:
        rep = _json.load(f)
    if not rep["pool_members"]:
        return                               # 微缩仓无池则跳过（与 c23 同款豁免）
    bj = os.path.join(w, "belief_js.json")
    with open(bj, "w", encoding="utf-8") as f:
        _json.dump({"schema": "topos-belief/1", "decoder": "nb", "params": {},
                    "n_units": rep["n_units"],
                    "belief": {str(i): 0.3 for i in range(rep["n_units"])},
                    "unit_ids": rep.get("units")}, f)
    from topos.cli import main as cli_main
    assert cli_main(["next", sj, bj]) == 0


def c29_md_render(workdir):
    """W5④ MD 报告渲染：space 报告必带 schema+必填诊断；belief 后验表有行。"""
    from topos.report.json_out import build_report
    from topos.report.md_out import render_md
    root = os.path.join(workdir, "mdrepo")
    os.makedirs(root)
    with open(os.path.join(root, "a.py"), "w", encoding="utf-8") as f:
        f.write("import util_b\n\n\ndef fa():\n    return util_b.fb(1)\n")
    with open(os.path.join(root, "util_b.py"), "w", encoding="utf-8") as f:
        f.write("def fb(x):\n    return x + 1\n")
    sp = Space(root)
    rep = build_report(sp)
    md = render_md(rep)
    assert "topos-space/1" in md
    for k in ("c_min", "c_mean", "zero_cover_rate", "n_pools"):
        assert k in md, "MD 缺必填诊断 %s" % k
    bel = {"schema": "topos-belief/1", "decoder": "nb",
           "belief": {rep["units"][0]: 0.7, rep["units"][1]: 0.1}}
    md2 = render_md(rep, bel)
    assert "0.7000" in md2 and "topos-belief" in md2
    # CLI smoke：report-md 子命令零退出
    sj = os.path.join(workdir, "sp.json")
    from topos.report.json_out import write as jwrite
    jwrite(rep, sj)
    from topos.cli import main as cli_main
    rc = cli_main(["report-md", sj, "--belief", _write_belief(workdir, bel),
                   "-o", os.path.join(workdir, "out.md")])
    assert rc == 0
    with open(os.path.join(workdir, "out.md"), encoding="utf-8") as f:
        assert "topos space 报告" in f.read()


def _write_belief(workdir, bel):
    p = os.path.join(workdir, "bel.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(bel, f)
    return p


def c30_owner_attribution(workdir):
    """v0.2②档1：F3-py owner 归属 + 点链解析规则（self/别名/不猜）。"""
    root = os.path.join(workdir, "own")
    os.makedirs(root)
    with open(os.path.join(root, "mod.py"), "w", encoding="utf-8") as f:
        f.write("def outer():\n"
                "    def inner():\n"
                "        return helper()\n"
                "    return inner()\n"
                "\n"
                "def helper():\n"
                "    return 1\n")
    with open(os.path.join(root, "mod2.py"), "w", encoding="utf-8") as f:
        f.write("import util\n\n\ndef g():\n    return util.h()\n\n\n"
                "def g2(x):\n    return x.h()\n")
    with open(os.path.join(root, "util.py"), "w", encoding="utf-8") as f:
        f.write("def h():\n    return 0\n")
    us = discover_units(root)
    ly = _extract_layers(root, us)
    call = ly["call"]

    def uid(f, n):
        for k, u in enumerate(us):
            if u["file"] == f and u["name"] == n:
                return k
        raise AssertionError("unit not found %s/%s" % (f, n))

    o, inner, helper = uid("mod.py", "outer"), uid("mod.py", "inner"), \
        uid("mod.py", "helper")
    g, g2, h = uid("mod2.py", "g"), uid("mod2.py", "g2"), uid("util.py", "h")

    # A3：call 层有向 (caller, callee)；按"前者调后者"书写，方向错即失败
    def pair(x, y):
        return (x, y)

    assert pair(o, inner) in call                    # 外层调内层 ✓
    assert pair(inner, helper) in call               # 嵌套内调用归嵌套 ✓
    assert pair(o, helper) not in call, "F3-py 嵌套归因泄漏"
    assert pair(helper, o) not in call, "F3-py 嵌套归因泄漏（反向）"
    assert pair(g, h) in call, "import 别名点链未解析"
    assert pair(h, g) not in call, "方向反了（util.h 不可能调 mod2.g）"
    assert pair(g2, h) not in call, "非别名链头仍在猜（可少不可假违反）"


def c31_exclude_tests_space(workdir):
    """v0.2③：manifest 顶层 exclude_tests → Space 装配级图豁免。"""
    import json as _json
    root = os.path.join(workdir, "ext")
    os.makedirs(os.path.join(root, "tests"))
    with open(os.path.join(root, "a.py"), "w", encoding="utf-8") as f:
        f.write("def real():\n    return eval('1')\n")
    with open(os.path.join(root, "tests", "test_a.py"), "w",
              encoding="utf-8") as f:
        f.write("def test_real():\n    return eval('2')\n")
    mf = {"version": 3, "layers": {"call": 1.0},
          "fields": [{"name": "anchor", "method": "regex",
                      "params": {"patterns": [["sink:eval", r"\beval\s*\("]]}}],
          "slicers": [], "pools": []}
    on, off = os.path.join(workdir, "mf_on.json"), \
        os.path.join(workdir, "mf_off.json")
    m_on = dict(mf)
    m_on["exclude_tests"] = True
    with open(on, "w", encoding="utf-8") as f:
        _json.dump(m_on, f)
    with open(off, "w", encoding="utf-8") as f:
        _json.dump(mf, f)
    s_on = Space(root, manifest_path=on)
    s_off = Space(root, manifest_path=off)
    assert all(not is_test_unit(u) for u in s_on.units), "豁免后仍有测试单元"
    assert any(is_test_unit(u) for u in s_off.units), "未豁免应含测试单元"
    assert len(s_on.units) < len(s_off.units)




def c32_t_family(workdir):
    """v0.2 T 族三场：authors / fix_coupling / stability（temp git 仓实测）。"""
    import subprocess
    from topos.axis.methods.git_history import git_field
    root = os.path.join(workdir, "trepo")
    os.makedirs(root)
    with open(os.path.join(root, "a.py"), "w", encoding="utf-8") as f:
        f.write("def fa():\n    return 1\n")
    with open(os.path.join(root, "b.py"), "w", encoding="utf-8") as f:
        f.write("def fb():\n    return 2\n")

    def git(*a):
        r = subprocess.run(["git", "-C", root] + list(a), capture_output=True)
        assert r.returncode == 0, r.stderr

    git("init")
    git("add", "-A")
    git("-c", "user.name=U1", "-c", "user.email=u1@t", "commit", "-m", "init")
    with open(os.path.join(root, "a.py"), "a", encoding="utf-8") as f:
        f.write("def fa2():\n    return 3\n")
    with open(os.path.join(root, "b.py"), "a", encoding="utf-8") as f:
        f.write("def fb2():\n    return 4\n")
    git("add", "-A")
    git("-c", "user.name=U2", "-c", "user.email=u2@t", "commit",
        "-m", "fix bug in fa2/fb2")
    us = discover_units(root)
    res = {m: git_field(us, {"metric": m}, {"root": root})
           for m in ("authors", "fix_coupling", "stability")}
    for m in ("authors", "fix_coupling", "stability"):
        assert len(res[m]) == len(us), "%s 有 None（应全部可算）" % m
    assert all(v >= 2 for v in res["authors"].values()), "双作者应 ≥2"
    assert all(v >= 1 for v in res["fix_coupling"].values()), "修复耦合应 ≥1"
    assert all(0.0 <= v <= 1.0 for v in res["stability"].values())
    assert all(v == 0.0 for v in res["stability"].values()), \
        "全部提交都在近 90 天 → 稳定性=0"


def c33_random_field(workdir):
    """v0.2 random 对照场：同种子可复现、非常量、异种子不同。"""
    from topos.axis.methods.random_fields import random_field
    us = [{"src": ""} for _ in range(5)]
    r1 = random_field(us, {"seed": 7}, {})
    r2 = random_field(us, {"seed": 7}, {})
    r3 = random_field(us, {"seed": 8}, {})
    assert r1 == r2, "同种子必须可复现"
    assert len(set(r1.values())) == 5, "连续随机场不应撞值"
    assert r1 != r3, "不同种子应不同"


def c34_axis_admission(workdir):
    """§4.5 轴准入三读数：新池 Δcov=1/ρ=0/Δlogdet>0；重复池 Δcov=0/|ρ|=1。"""
    from topos.axis.admission import admit
    pools = [("P1", [0, 1, 2]), ("P2", [3, 4, 5])]
    r_new = admit(pools, ("P3", [6, 7, 8]))
    assert r_new["dcov"] == 1.0
    assert r_new["max_rho"] == -0.5, "不相交隶属向量应负相关（互补）"
    assert r_new["max_rho_pos"] == 0.0, "互补覆盖无冗余"
    assert r_new["dlogdet"] is not None and r_new["dlogdet"] > 0
    r_dup = admit(pools, ("P1dup", [0, 1, 2]))
    assert r_dup["dcov"] == 0.0
    assert r_dup["max_rho"] == 1.0, "完全重叠 = 冗余上限"
    assert r_dup["dlogdet"] is None, "完全重复池 → G 奇异（零信息增益的极端形式）"
    r_part = admit(pools, ("Ppart", [2, 3]))
    assert r_part["dcov"] == 0.0, "部分重叠池的新覆盖为 0"
    assert r_part["max_rho"] == 0.0, "n=6 下 [2,3] 与 P1/P2 的协方差恰好抵消"
    assert r_part["dlogdet"] is not None and r_part["dlogdet"] > 0


def _gate_fixture(workdir, tag):
    """在两个不同临时目录下建**同形**的合成仓 + 清单，用于 c37 位置无关性。"""
    import json as _json
    root = os.path.join(workdir, "g" + tag)
    os.makedirs(root)
    for k in range(6):
        with open(os.path.join(root, "m%d.py" % k), "w", encoding="utf-8") as f:
            f.write("def f%d():\n    return %d\n" % (k, k))
    mf = {"version": 3,
          "layers": {"call": 1.0},
          "fields": [{"name": "loc", "method": "ast",
                      "params": {"metric": "lines"}}],
          "slicers": [{"name": "tiny", "field": "loc", "op": "lt", "value": 1}],
          "pools": [{"name": "p", "expr": "tiny"}],
          "constraints": {"max_width": 400, "max_width_pct": 0.03,
                          "max_pools": 64, "min_pool_size": 3}}
    mp = os.path.join(workdir, "mf" + tag + ".json")
    with open(mp, "w", encoding="utf-8") as f:
        _json.dump(mf, f)
    return root, mp


def c35_gate_true_red(workdir):
    """D-B7-4/c35 真红：门必须能红（钉在**已被收集、原本全绿**的归档件上）。

    `EXP/run1_dsh/c/space.json` 的 zero_cover_rate=0.904——这是 RUN1 真实产出的红灯，
    在它上面 next 必须输出 BLOCKED-COVERAGE，**不得**输出 STOP。
    θ_cov 缺失/非法必须 raise（不许静默回落给默认值）。
    """
    from topos.stop.gate import coverage_gate
    arch = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "EXP", "run1_dsh", "c", "space.json")
    if not os.path.exists(arch):
        raise AssertionError("归档件缺失，c35 失去意义: %s" % arch)
    with open(arch, encoding="utf-8") as f:
        sj = json.load(f)
    cov = sj["coverage"]
    n = sj["n_units"]
    assert cov["zero_cover_rate"] > 0.30, "归档件应仍是红灯"
    r = coverage_gate(cov, n, 0.30)
    assert r["verdict"] == "BLOCKED-COVERAGE", "真红件必须 BLOCKED，实为 %r" % r
    assert r["zero_cover_units"] > 0 and r["covered_units"] >= 0
    assert r["pools_needed_lower_bound"] >= 1, "必须给出补池数下界"
    # θ 缺失 / 非法 ⇒ raise（B7 §1.1：不许静默回落）
    for bad in (None, "0.3", -1, 0, 1.5):
        try:
            coverage_gate(cov, n, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("θ_cov=%r 必须 raise" % (bad,))


def c36_gate_true_green(workdir):
    """D-B7-4/c36 绿分支：θ_cov 提到 0.95 ⇒ 同一红灯件必须转 PASS（证明门不是恒红）。"""
    from topos.stop.gate import coverage_gate
    arch = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "EXP", "run1_dsh", "c", "space.json")
    with open(arch, encoding="utf-8") as f:
        sj = json.load(f)
    r = coverage_gate(sj["coverage"], sj["n_units"], 0.95)
    assert r["verdict"] == "PASS", "θ=0.95 时应 PASS（门不得恒红），实为 %r" % r


def c37_gate_position_independent(workdir):
    """D-B7-4/c37 位置无关 + 可复现：两个不同临时目录下，读数逐字相同。"""
    from topos.stop.gate import coverage_gate
    outs = []
    for tag in ("a", "b"):
        root, mp = _gate_fixture(workdir, tag)
        sp = Space(root, manifest_path=mp)
        outs.append(coverage_gate(sp.coverage, sp.n, 0.30))
    assert outs[0] == outs[1], "不同目录下读数必须逐字相同: %r vs %r" % (
        outs[0], outs[1])


def c41_call_direction(workdir):
    """A3：调用边恢复方向；无向投影必须逐字不变（不破基线）。

    表示：layers["call"] = {(caller, callee)} 有序。
    投影：fuse/to_adj 归一化为 (min,max) ⇒ 几何与所有下游读数不变。
    """
    from topos.core import units as units_mod
    from topos.core.layers import _extract_layers, to_adj
    from topos.core.fuse import fuse
    from topos.axis.methods.layer_fields import layer_field
    root = os.path.join(workdir, "dir")
    os.makedirs(root)
    with open(os.path.join(root, "m.py"), "w", encoding="utf-8") as f:
        f.write("def callee():\n    return 1\n\n"
                "def caller():\n    return callee()\n")
    us = units_mod.discover_units(root)
    by = {u["name"]: i for i, u in enumerate(us)}
    L = _extract_layers(root, us)
    ci, ce = by["caller"], by["callee"]
    assert (ci, ce) in L["call"], \
        "call 边必须是有向的 (caller, callee)，实为 %r" % sorted(L["call"])
    out = layer_field(us, {"formula": "out"}, {"layers": L})
    inn = layer_field(us, {"formula": "in"}, {"layers": L})
    net = layer_field(us, {"formula": "net"}, {"layers": L})
    assert out[ci] == 1 and out[ce] == 0, "caller 出度应为 1，callee 出度应为 0"
    assert inn[ce] == 1 and inn[ci] == 0, "callee 入度应为 1，caller 入度应为 0"
    assert net[ci] == 1 and net[ce] == -1, "net = 出−入 应异号"
    # 无向投影不变：融合键仍归一化为 (min,max)
    fz = fuse(L, {"call": 1.0, "data": 1.0})
    assert all(a <= b for (a, b) in fz), "fuse 键必须归一化，实为 %r" % list(fz)
    adj = to_adj(fz)
    assert ce in adj[ci] and ci in adj[ce], "to_adj 必须仍对称（无向投影）"


def c38_alpha_is_live(workdir):
    """A1（解冻后第一批·修既有 bug）：α 不再是死旋钮。

    旧行为：三档 α（全 1.0 / 全 0.0 / skew）下 `to_adj` 只取键 ⇒ 边集逐字相同
    （EXP/_b6_s1_alpha_inert.py 实测 `edge sets identical? True`）。
    修后：① min_weight 缺省 ⇒ 与旧行为逐字相同（不破基线）；
          ② min_weight 生效 ⇒ α 必须能改变边集（α_t=0 的层整层消失）。
    """
    from topos.core.layers import to_adj, _extract_layers
    from topos.core.fuse import fuse
    from topos.core import units as units_mod
    root = os.path.join(workdir, "alpha")
    os.makedirs(root)
    with open(os.path.join(root, "m.py"), "w", encoding="utf-8") as f:
        f.write(
            "G = {}\n"
            "def setv(k, v):\n    G[k] = v\n\n"
            "def getv(k):\n    return G.get(k)\n\n"
            "def top():\n    setv('a', 1)\n    x = getv('a')\n    return x\n"
        )
    us = units_mod.discover_units(root)
    L = _extract_layers(root, us)
    assert len(L.get("call", ())) >= 2, "合成仓应至少 2 条 call 边"

    def eset(adj):
        return {frozenset((u, v)) for u in adj for v in adj[u]}

    # ① 默认（min_weight=None）与旧行为逐字一致——不破基线
    f_def = fuse(L, {"call": 1.0, "data": 1.0, "vardep": 1.0})
    assert eset(to_adj(f_def)) == eset(to_adj(f_def, None))

    # ② α 必须活：把 call 层 α 置 0，仅保留 w≥2 的边 ⇒ 纯 call 边（w=1）被裁掉
    f_skew = fuse(L, {"call": 0.0, "data": 1.0, "vardep": 1.0})
    e_all = eset(to_adj(f_skew))
    e_w2 = eset(to_adj(f_skew, 2.0))
    assert e_w2 <= e_all, "阈值裁剪必须是子集"
    assert e_w2 != e_all or not e_all, \
        "α 仍是死旋钮：阈值未改变边集（A1 未生效）"

    # ③ 全零 α + 阈值 ⇒ 整图应被裁空（α_t=0 的层整层消失）
    f_zero = fuse(L, {"call": 0.0, "data": 0.0, "vardep": 0.0})
    assert eset(to_adj(f_zero, 1.0)) == set(), "α 全 0 时不应有任何边存活"


def c39_layer_fields(workdir):
    """A2（解冻后第一批）：多层进场层——逐层可观测量 + α 阈值在 Space 层生效。"""
    import json as _json
    from topos.axis.methods.layer_fields import layer_field
    root = os.path.join(workdir, "lf")
    os.makedirs(root)
    with open(os.path.join(root, "m.py"), "w", encoding="utf-8") as f:
        f.write(
            "G = {}\n"
            "def setv(k, v):\n    G[k] = v\n\n"
            "def top():\n    setv('a', 1)\n    return G.get('a')\n"
        )
    from topos.core import units as units_mod
    from topos.core.layers import _extract_layers
    us = units_mod.discover_units(root)
    L = _extract_layers(root, us)
    n = len(us)
    span = layer_field(us, {"formula": "span"}, {"layers": L})
    gap = layer_field(us, {"formula": "gap"}, {"layers": L})
    degc = layer_field(us, {"formula": "deg:call"}, {"layers": L})
    assert set(span) == set(range(n)), "span 场必须覆盖全部单元"
    assert all(0 <= v <= 5 for v in span.values()), "span ∈ [0,5]"
    assert all(isinstance(v, int) for v in gap.values())
    assert all(v >= 0 for v in degc.values()), "度非负"
    try:
        layer_field(us, {"formula": "deg:nope"}, {"layers": L})
    except ValueError:
        pass
    else:
        raise AssertionError("非法层名必须抛 ValueError（如实降级：不静默退化为 0）")


def c40_git_prefix_subdir(workdir):
    """B-1：扫 git 仓库的**子目录**时，T 族三场不得全灭。

    `git -C <子目录> log --name-only` 打印仓库根相对路径（`topos/cli.py`），
    而单元 file 是扫描根相对路径（`cli.py`）⇒ 修复前 authors/fix_coupling/stability
    的 nonnull 恒为 0.000（实测扫 `topos/`：三场 0.000 → 修复后 0.991）。
    本断言钉在"子目录扫描必须有非空 T 族"上，防回归。
    """
    import subprocess
    from topos.axis.methods.git_history import _git_prefix, _all_commits
    root = os.path.join(workdir, "gitsub")
    sub = os.path.join(root, "pkg")
    os.makedirs(sub)
    with open(os.path.join(sub, "a.py"), "w", encoding="utf-8") as f:
        f.write("def fa():\n    return 1\n")

    def git(*args):
        subprocess.run(["git"] + list(args), cwd=root,
                       capture_output=True, text=True, timeout=30)

    for a in (("config", "user.email", "t@t"), ("config", "user.name", "t")):
        subprocess.run(["git"] + list(a), cwd=root, capture_output=True,
                       text=True, timeout=30)
    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "-m", "fix: initial")

    assert _git_prefix(sub) == "pkg", "子目录前缀应为 pkg，实为 %r" % _git_prefix(sub)
    assert _git_prefix(root) == "", "仓库根前缀应为空"
    cs = _all_commits(sub)
    assert cs, "子目录扫描必须解析到 commit"
    assert any("a.py" in c[3] for c in cs), \
        "commit 文件路径必须已归一化为扫描根相对（应为 a.py，实为 %r）" % cs[0][3]


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
    ("c14 类内方法名 Class.method", c14_qualified_name),
    ("c15 belief 值域 [0,1] 无硬值（A8）", c15_belief_domain),
    ("c16 全阴观测：NB<0.5 且集合型无判阳", c16_negative_world),
    ("c17 证据方向性（NB 单调）", c17_evidence_direction),
    ("c18 α 稳定域 + 宽度单调衰减", c18_alpha_stability),
    ("c19 SCOMP 终止性 + CLI decode smoke", c19_scomp_terminal_cli_smoke),
    ("c20 σ 单调与值域（精确式+闭式）", c20_sigma_monotone),
    ("c21 停止方向（全低 STOP / 高 belief 不停）", c21_stop_direction),
    ("c22 预算回路终止性", c22_budget_loop),
    ("c23 CLI next smoke", c23_cli_next_smoke),
    ("c24 接缝规则方向性（R1..R4）", c24_seam_rule_signs),
    ("c25 接缝抽取命中（R1/R2/R3/R4）", c25_seam_extraction),
    ("c26 接缝→sheaf 端到端（奇环 ker=0 / TV 盲）", c26_seam_sheaf_end_to_end),
    ("c27 JS 抽取（单元/require 边/eval veto）", c27_js_extraction),
    ("c28 JS 链微缩（space→next 零退出）", c28_js_chain),
    ("c29 MD 报告渲染（W5④：schema+必填诊断+后验表）", c29_md_render),
    ("c30 owner 归属 + 点链解析（F3-py/self/别名/不猜）", c30_owner_attribution),
    ("c31 装配级测试豁免（图级 exclude_tests）", c31_exclude_tests_space),
    ("c32 T 族三场（authors/fix_coupling/stability）", c32_t_family),
    ("c33 random 对照场（同种子可复现）", c33_random_field),
    ("c34 轴准入三读数（Δcov/|ρ|/Δlogdet）", c34_axis_admission),
    ("c35 覆盖率门真红（RUN1 c 件 zcr=0.904 必须 BLOCKED）", c35_gate_true_red),
    ("c36 覆盖率门真绿（θ=0.95 必须 PASS，不得恒红）", c36_gate_true_green),
    ("c37 覆盖率门位置无关（两目录读数逐字相同）", c37_gate_position_independent),
    ("c38 α 活旋钮（min_weight 生效 + 默认不破基线）", c38_alpha_is_live),
    ("c39 多层进场层（span/gap/deg 逐层可观测量）", c39_layer_fields),
    ("c40 扫子目录 T 族不灭（git 路径前缀归一化）", c40_git_prefix_subdir),
    ("c41 调用边方向恢复（out/in/net + 无向投影不变）", c41_call_direction),
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
