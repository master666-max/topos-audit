# -*- coding: utf-8 -*-
"""
EXP/calc_b2_e4_agreement.py —— 按 PREREG/B2 v1.5 计算多裁判一致性。

判据（v1.5 §B，见数据前锁定）：
  B1 主判据 Krippendorff's α（nominal，原生支持 None 缺失）+ Gwet's AC1（抗 prevalence 悖论）
  B2 硬一致（剔 None）与全一致（None 作第三类）两口都报；作废线绑**全 κ/α** 口径
  B3 层内 α 主判读；禁止配额加权合成
  C  α/κ 的 CI = **按层分层 bootstrap**
  退化预案（glm5.3 报告 §4.2 提出、v1.5 采纳）：阳性合并计数 <5 → κ/α 分母趋零退化，
     改报「一致率 + Wilson 区间」，并判「域内缺陷密度低于本设计分辨力」。

用法：python -X utf8 EXP/calc_b2_e4_agreement.py
"""
import csv
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.join(HERE, "多agent判断")
OUT = os.path.join(HERE, "B2-E4-agreement.json")

JUDGES = [
    ("judgeA-hy4", "B2-E4-adjudication-judgeA-hy4-preview.csv"),
    ("judgeB-qwen3.8max", "B2-E4-adjudication-judgeB-qwen-3.8max.csv"),
    ("judgeC", "B2-E4-adjudication-judgeC.csv"),
]
EXTRA = [("glm5.3-pretag", "B2-E4_预标_评估器A_v2_对齐材料_2026-10-10-glm5.3.csv")]
SEED = 20261009
N_BOOT = 1000


def norm(v):
    v = (v or "").strip()
    if v in ("1", "true", "True"):
        return "1"
    if v in ("0", "false", "False"):
        return "0"
    return "None"


def load(path, key_fields=("seq", "unit_id", "unit")):
    """读裁判 CSV → {key: truth}, {key: stratum}"""
    if not os.path.exists(path):
        return None, None
    out, strat = {}, {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            k = None
            for kf in key_fields:
                if kf in row and row[kf]:
                    k = row[kf]
                    break
            if k is None:
                continue
            out[k] = norm(row.get("truth", row.get("pred", "")))
            if "stratum" in row:
                strat[k] = row["stratum"]
    return out, strat


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def krippendorff_alpha(rows):
    """rows: [[v1, v2, ...], ...]，v ∈ {'0','1','None'}，'None' 视为缺失（不参与）。
    nominal α（δ²=1 for c≠k）。返回 (alpha, n_units_used, n_pairs)。"""
    cats = ["0", "1"]
    o = defaultdict(float)      # coincidence matrix
    tot_pairs = 0.0
    used = 0
    for vals in rows:
        vs = [v for v in vals if v in cats]
        m = len(vs)
        if m < 2:
            continue
        used += 1
        w = 1.0 / (m - 1.0)
        for i in range(m):
            for j in range(m):
                if i == j:
                    continue
                o[(vs[i], vs[j])] += w
        tot_pairs += m
    if tot_pairs < 2:
        return None, used, tot_pairs
    n = sum(o.values())
    if n == 0:
        return None, used, tot_pairs
    do = sum(v for (c, k), v in o.items() if c != k) / n
    nc = {c: sum(v for (cc, kk), v in o.items() if cc == c) for c in cats}
    de_num = sum(nc[c] * (n - nc[c]) for c in cats)
    de = de_num / (n * (n - 1)) if n > 1 else 0.0
    if de == 0:
        return None, used, tot_pairs     # 退化
    return 1.0 - do / de, used, tot_pairs


def gwet_ac1(rows):
    """两类 Gwet's AC1（对 prevalence 稳健）。None 视为缺失（该单元不参与）。"""
    pa_hits = tot = 0
    marg = Counter()
    mcount = 0
    for vals in rows:
        vs = [v for v in vals if v in ("0", "1")]
        if len(vs) < 2:
            continue
        tot += 1
        # 成对一致率（多裁判：一致对数 / 总对数）
        pairs = 0
        agree = 0
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                pairs += 1
                agree += 1 if vs[i] == vs[j] else 0
        pa_hits += agree / pairs
        for v in vs:
            marg[v] += 1
            mcount += 1
    if tot == 0 or mcount == 0:
        return None
    pa = pa_hits / tot
    pi = marg["1"] / mcount
    pe = 2 * pi * (1 - pi)          # r=2: Σ π_c(1−π_c)
    if abs(1 - pe) < 1e-12:
        return None
    return (pa - pe) / (1 - pe)


def main():
    judges = []
    for name, fn in JUDGES:
        d, st = load(os.path.join(SUB, fn))
        if d is None:
            print("缺失: %s" % fn)
            continue
        judges.append((name, d, st))
    extras = []
    for name, fn in EXTRA:
        d, st = load(os.path.join(SUB, fn))
        if d is not None:
            extras.append((name, d, st))

    keys = sorted(set.intersection(*[set(d) for _n, d, _s in judges]))
    print("对齐单元: %d（三裁判交集）" % len(keys))
    strat = {}
    for _n, d, st in judges:
        for k in keys:
            if k in st:
                strat[k] = st[k]

    res = {"n_units": len(keys), "judges": {}, "pairwise": {},
           "alpha": {}, "ac1": {}, "degenerate": None}

    for name, d, _s in judges + extras:
        c = Counter(d[k] for k in keys) if all(k in d for k in keys) else Counter()
        if not c:
            continue
        pos = c["1"]
        res["judges"][name] = {
            "one": pos, "zero": c["0"], "none": c["None"],
            "one_rate_wilson": [round(x, 4) for x in wilson(pos, len(keys))],
        }

    # 两两：硬一致 / 全一致 / 阳性集交集
    for i in range(len(judges)):
        for j in range(i + 1, len(judges)):
            (na, da, _), (nb, db, _) = judges[i], judges[j]
            hard = [k for k in keys if da[k] != "None" and db[k] != "None"]
            h_agree = sum(1 for k in hard if da[k] == db[k])
            f_agree = sum(1 for k in keys if da[k] == db[k])
            pa = {k for k in keys if da[k] == "1"}
            pb = {k for k in keys if db[k] == "1"}
            res["pairwise"]["%s|%s" % (na, nb)] = {
                "hard": "%d/%d" % (h_agree, len(hard)),
                "hard_rate": round(h_agree / max(len(hard), 1), 4),
                "full": "%d/%d" % (f_agree, len(keys)),
                "full_rate": round(f_agree / max(len(keys), 1), 4),
                "pos_intersection": sorted(pa & pb),
                "pos_union": len(pa | pb),
            }

    # 三裁判：阳性集交集/并集
    pos_sets = [{k for k in keys if d[k] == "1"} for _n, d, _s in judges]
    res["positive"] = {
        "intersection_all": sorted(set.intersection(*pos_sets)),
        "union_all": sorted(set.union(*pos_sets)),
        "union_size": len(set.union(*pos_sets)),
    }

    # α / AC1（三裁判）
    rows = [[d[k] for _n, d, _s in judges] for k in keys]
    alpha, used, tp = krippendorff_alpha(rows)
    ac1 = gwet_ac1(rows)
    pos_total = sum(1 for r in rows for v in r if v == "1")
    res["alpha"]["all"] = alpha
    res["ac1"]["all"] = ac1
    res["alpha"]["units_used"] = used
    res["positive"]["total_positive_labels"] = pos_total
    degenerate = pos_total < 5
    res["degenerate"] = {
        "triggered": degenerate,
        "rule": "阳性合并计数 <5 → α/κ 分母趋零退化，改报一致率+Wilson，并判「域内缺陷密度低于本设计分辨力」",
        "total_positive_labels": pos_total,
    }

    # 分层 bootstrap CI（层为设计变量，层内重抽）
    by_layer = defaultdict(list)
    for k in keys:
        by_layer[strat.get(k, "?")].append(k)
    rng = random.Random(SEED)
    boot_alpha = []
    for _b in range(N_BOOT):
        sample = []
        for _L, ks in by_layer.items():
            sample.extend(rng.choice(ks) for _ in range(len(ks)))
        a, _u, _t = krippendorff_alpha([[d[k] for _n, d, _s in judges] for k in sample])
        if a is not None:
            boot_alpha.append(a)
    ci = None
    if boot_alpha:
        s = sorted(boot_alpha)
        ci = (round(s[int(0.025 * len(s))], 4), round(s[min(int(0.975 * len(s)), len(s) - 1)], 4))
    res["alpha"]["ci95_stratified_bootstrap"] = ci
    res["alpha"]["bootstrap_reps"] = len(boot_alpha)

    # 层内 α + None 率
    for L, ks in sorted(by_layer.items()):
        r = [[d[k] for _n, d, _s in judges] for k in ks]
        aL, uL, _t = krippendorff_alpha(r)
        none_rate = sum(1 for row in r for v in row if v == "None") / max(len(r) * 3, 1)
        res.setdefault("by_layer", {})[L] = {
            "n": len(ks), "alpha": aL,
            "none_rate": round(none_rate, 4),
            "none_gt_40pct": none_rate > 0.40,
        }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    print(json.dumps(res, ensure_ascii=False, indent=1))
    print("\n产物: %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
