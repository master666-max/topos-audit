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
