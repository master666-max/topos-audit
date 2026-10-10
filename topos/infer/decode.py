# -*- coding: utf-8 -*-
"""
topos.infer.decode —— 解码器族（W5，B3 批）。

COMP / DD / SCOMP：集合型解码器，输出两档代理 belief（判阳=Se、判阴=1−Sp），
**仅供排序（AUC）**，不得当校准概率引用（PREREG/B3 T-B3-a；A8：只出概率不出二值）。
NB：逐单元独立后验（logit 域证据累加），连续 [0,1]，真概率口径（naive 独立近似）。

算法操作化定义以 PREREG/B3 §0 为准（锁定）。纸面基准：binGroup2 R/ 经核查无解码器实现
（2026-10-10），DD/SCOMP 按架构书 §6.1 口径独立实现，与 Aldridge et al. 2014 标准定义的
偏离（singleton-DD）登记于 PREREG/B3 T-B3-b。
"""
import math

SCHEMA = "topos-belief/1"
DECODERS = ("comp", "dd", "scomp", "nb")


# ---------- 集合型：COMP / DD / SCOMP ----------

def _counts(pools, obs, n):
    """pos_count / neg_count：单元所属阳性/阴性池数。obs 已按 pools 对齐。"""
    pos = [0] * n
    neg = [0] * n
    for (_nm, members), (_n2, y) in zip(pools, obs):
        if y:
            for i in members:
                pos[i] += 1
        else:
            for i in members:
                neg[i] += 1
    return pos, neg


def _two_band(pos_set, n, se, sp):
    """两档代理 belief：判阳=Se、判阴=1−Sp（仅供排序，T-B3-a）。"""
    return {i: (se if i in pos_set else 1.0 - sp) for i in range(n)}


def decode_comp(pools, obs, n, se=0.9, sp=0.95, **_kw):
    """COMP：∈ 阴性池 → 判阴；否则判阳（硬排除基线，§6.1 原文）。"""
    _pos, neg = _counts(pools, obs, n)
    return _two_band({i for i in range(n) if neg[i] == 0}, n, se, sp)


def decode_dd(pools, obs, n, se=0.9, sp=0.95, **_kw):
    """DD：判阳 ⇔ 恰属于 1 个阳性池且不属于任何阴性池（§6.1 singleton 口径 + 不复活条款）。"""
    pos, neg = _counts(pools, obs, n)
    return _two_band({i for i in range(n) if pos[i] == 1 and neg[i] == 0},
                     n, se, sp)


def decode_scomp(pools, obs, n, se=0.9, sp=0.95, **_kw):
    """SCOMP：DD 判阳集起，贪心解释残余阳性池（§6.1 口径）。

    每轮取「出现在最多残余阳性池中的非阴性单元」加入 D（并列取 pos_count 大者，
    再并列取单元序号小者）；残余空或无候选即终止。判阳 = D。
    """
    pos, neg = _counts(pools, obs, n)
    d = {i for i in range(n) if pos[i] == 1 and neg[i] == 0}
    pos_pools = [set(m) for (_nm, m), (_n2, y) in zip(pools, obs) if y]
    guard = len(pos_pools) + 1
    while guard > 0:
        guard -= 1
        residual = [p for p in pos_pools if not (p & d)]
        if not residual:
            break
        best, best_key = None, None
        for i in range(n):
            if neg[i] > 0:
                continue
            hits = sum(1 for p in residual if i in p)
            if hits == 0:
                continue
            key = (hits, pos[i], -i)
            if best_key is None or key > best_key:
                best, best_key = i, key
        if best is None:                       # 候选全被阴性否决（假阳池）
            break
        d.add(best)
    return _two_band(d, n, se, sp)


# ---------- NB：逐单元独立后验 ----------

def decode_nb(pools, obs, n, se=0.9, sp=0.95, prior=None, **_kw):
    """NB 后验：z_i = logit(π) + Σ_{j∋i}[y_j=1: log(Se/(1−Sp)); y_j=0: log((1−Se)/Sp)]。

    naive 独立近似（重叠池证据不独立，故为 naive）；π 为显式先验（T-B3-c），
    缺省取 n 的隐含密度下界 1/n（不假装知道植入数）。
    """
    if prior is None:
        prior = 1.0 / n
    prior = min(max(float(prior), 1e-9), 1.0 - 1e-9)
    lp = math.log(prior / (1.0 - prior))
    lr_pos = math.log(se / (1.0 - sp))
    lr_neg = math.log((1.0 - se) / sp)
    z = [lp] * n
    for (_nm, members), (_n2, y) in zip(pools, obs):
        lr = lr_pos if y else lr_neg
        for i in members:
            z[i] += lr
    # sigmoid —— 逐单元独立后验（近似）
    out = {}
    for i in range(n):
        zi = max(min(z[i], 500.0), -500.0)     # 溢出护栏
        out[i] = 1.0 / (1.0 + math.exp(-zi))
    return out


DISPATCH = {"comp": decode_comp, "dd": decode_dd,
            "scomp": decode_scomp, "nb": decode_nb}


def decode(pools, obs, n, method="nb", se=0.9, sp=0.95, prior=None):
    """统一入口。pools=[(name,set)]，obs=[(name,y)] 与 pools 同序同集。

    返回 {unit_idx: belief∈[0,1]}。method ∈ {comp,dd,scomp,nb}。
    """
    if method not in DECODERS:
        raise ValueError("未知解码器 %r（可选 %s）" % (method, DECODERS))
    names_p = [nm for nm, _m in pools]
    names_o = [nm for nm, _y in obs]
    if set(names_p) != set(names_o) or len(names_p) != len(names_o):
        raise ValueError("obs 与 pools 的池名不一致：%d vs %d"
                         % (len(names_p), len(names_o)))
    align = {nm: k for k, nm in enumerate(names_o)}
    obs_aligned = [(pools[k][0], obs[align[pools[k][0]]][1])
                   for k in range(len(pools))]
    return DISPATCH[method](pools, obs_aligned, n, se=se, sp=sp, prior=prior)


def belief_json(decoder, belief, params, unit_ids=None):
    """topos-belief/1 schema 组装。unit_ids 可选（space.json 回落用）。"""
    n = len(belief)
    for i, b in belief.items():
        if not (0.0 <= b <= 1.0):
            raise ValueError("belief[%d]=%r 越界 [0,1]——违反 A8" % (i, b))
    return {
        "schema": SCHEMA,
        "decoder": decoder,
        "params": params,
        "n_units": n,
        "belief": {"%d" % i: round(b, 6) for i, b in sorted(belief.items())},
        "unit_ids": unit_ids,
    }
