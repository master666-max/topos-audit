# -*- coding: utf-8 -*-
"""B8 补覆盖批 —— 副靶 L3 SVEN 三臂（`PREREG/B8.md` §1.2，判据先于实现）。

三臂共用同一个 Space（单元/场/图完全一致），**只换池预算与宽度上限**：

| 臂 | 预算 | 宽度上限 | 回答什么 |
|---|---|---|---|
| a | 8 池 | 3%（原约束） | 原约束下能不能及格（预期：不能，上限 24%） |
| b | 8 池 | n/16 ≈ 6.2% | 放宽宽度能否及格；代价=池变宽、图先验衰减 |
| c | 全开 | 3% | **覆盖满后 AUC 还是不是 0.5**（D-B8-4 归因判据） |

产物写新目录 `EXP/b8_e1/`，不覆盖 `EXP/b6_e1/`（B6 §3 数据保全）。
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "b8_e1")
os.makedirs(OUT, exist_ok=True)

SVEN_DIR = os.path.join(REPO, "tools", "repos", "sven_space")
FUNCS = os.path.join(HERE, "l3_sven", "functions.jsonl")
GOLD = os.path.join(REPO, "calib", "gold_l3_sven.csv")
AXES = os.path.join(REPO, "axes.json")

truth = {}
with open(GOLD, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        truth[row["unit_id"]] = int(row["truth"])
order = []
with open(FUNCS, encoding="utf-8") as f:
    for ln in f:
        if ln.strip():
            order.append(json.loads(ln)["unit_id"])
file2gold = {"u%05d.py" % i: uid for i, uid in enumerate(order)}

from topos.space import Space                      # noqa: E402
from topos.pool.design import coverage_fill, coverage  # noqa: E402
from topos.infer.decode import decode_nb           # noqa: E402
from topos.stop import weitzman as W               # noqa: E402

sp = Space(SVEN_DIR, manifest_path=AXES)
base_rows = [(nm, set(m)) for nm, m in sp.rows]
n = sp.n
print("Space: n=%d  基础池=%d  零覆盖=%.4f"
      % (n, len(base_rows), sp.coverage["zero_cover_rate"]))

uid_of = [u["id"] if isinstance(u, dict) else str(u) for u in sp.units]
gold_of = {}
for i, sid in enumerate(uid_of):
    g = file2gold.get(sid.split("::", 1)[0])
    if g in truth:
        gold_of[i] = truth[g]
pos = [i for i, t in gold_of.items() if t == 1]
neg = [i for i, t in gold_of.items() if t == 0]
print("对齐：阳 %d / 阴 %d" % (len(pos), len(neg)))

anchor = sp.fields.get("anchor", {})


def hit(i):
    v = anchor.get(i)
    if v is None:
        return False
    return bool(v) if not isinstance(v, (list, tuple, set)) else len(v) > 0


DANGER = re.compile(r"\b(subprocess|os\.system|eval\s*\(|exec\s*\(|pickle\.loads"
                    r"|yaml\.load\s*\(|shell\s*=\s*True|os\.popen)\b")
grep_files = set()
for fn in os.listdir(SVEN_DIR):
    if fn.endswith(".py"):
        with open(os.path.join(SVEN_DIR, fn), encoding="utf-8",
                  errors="ignore") as f:
            if DANGER.search(f.read()):
                grep_files.add(fn)
grep_idx = [i for i, sid in enumerate(uid_of)
            if sid.split("::", 1)[0] in grep_files]


def evaluate(arm, rows, budget):
    pools = [(nm, set(m)) for nm, m in rows]
    obs = [(nm, 1 if any(hit(i) for i in m) else 0) for nm, m in pools]
    sig = {}
    for nm, m in pools:
        sig[nm] = (W.sigma_exact([1.0 / 250] * len(m), 0.05)
                   if m else 0.0)
    opened = [nm for nm, _ in sorted(sig.items(), key=lambda kv: -kv[1])][:budget]
    # 冷启动：先按先验 belief 排序开池（同 B6 处理）
    prior = {i: 1.0 / 250 for i in range(n)}
    mus = {nm: W.pool_value_mean([(nm, m)], prior)[nm] for nm, m in pools}
    opened = [nm for nm, _ in sorted(mus.items(), key=lambda kv: -kv[1])][:budget]
    sub = [(nm, m) for nm, m in pools if nm in opened]
    obs_sub = [(nm, 1 if any(hit(i) for i in m) else 0) for nm, m in sub]
    belief = decode_nb(sub, obs_sub, n, se=0.9, sp_=0.95, prior=1.0 / 250)

    reviewed = set()
    for nm, m in sub:
        reviewed |= m
    k = sum(1 for i in reviewed if gold_of.get(i) == 1)
    cov_pos = sum(1 for i in pos
                  if any(i in m for _nm, m in pools))
    scored = sorted(gold_of, key=lambda i: -belief.get(i, 0.0))
    ys = [gold_of[i] for i in scored]
    P, N = sum(ys), len(ys) - sum(ys)
    rank_sum = sum(r + 1 for r, y in enumerate(ys) if y == 1)
    auc = (rank_sum - P * (P + 1) / 2.0) / (P * N) if (P and N) else None
    cut = max(1, len(reviewed))
    pred = set(scored[:cut])
    sens = sum(1 for i in pos if i in pred) / max(len(pos), 1)
    spec = sum(1 for i in neg if i not in pred) / max(len(neg), 1)
    gr = set(grep_idx[:len(reviewed)])
    k_grep = sum(1 for i in gr if gold_of.get(i) == 1)
    return {"arm": arm, "budget": budget, "pools_total": len(pools),
            "pools_opened": len(opened),
            "zero_cover_after_fill": coverage(pools, n)["zero_cover_rate"],
            "reviewed_units": len(reviewed),
            "reviewed_pct": round(100.0 * len(reviewed) / n, 2),
            "D-B6-1_k": k, "D-B6-1_recall": round(k / max(len(pos), 1), 4),
            "D-B6-3_coverage_pos": round(cov_pos / max(len(pos), 1), 4),
            "predicted_coverage_cap": round(min(1.0, budget * (max(
                len(m) for _nm, m in pools) / float(n))), 4),
            "auc": round(auc, 4) if auc is not None else None,
            "balanced_acc": round((sens + spec) / 2, 4),
            "D-B6-5_k_grep": k_grep,
            "max_pool_width": max(len(m) for _nm, m in pools)}


CONST_BASE = {"max_width": 400, "max_width_pct": 0.03, "max_pools": 64,
              "min_pool_size": 3}
CONST_B = dict(CONST_BASE)
CONST_B["max_width_pct"] = 1.0 / 16          # n/16 ≈ 6.2%
CONST_B["max_width"] = int(n / 16) + 1

rows_a = base_rows + coverage_fill(base_rows, n, CONST_BASE)
rows_b = base_rows + coverage_fill(base_rows, n, CONST_B)
rows_c = rows_a                               # 同宽度，全开

res = []
for arm, rows, budget in (("a", rows_a, 8), ("b", rows_b, 8),
                          ("c", rows_c, len(rows_c))):
    r = evaluate(arm, rows, budget)
    res.append(r)
    print("\n=== 臂 %s（预算 %d 池，最大宽 %d）===" % (arm, budget, r["max_pool_width"]))
    print("  池总数 %d，开 %d；核验 %d 单元（%.2f%%）"
          % (r["pools_total"], r["pools_opened"], r["reviewed_units"],
             r["reviewed_pct"]))
    print("  D-B8-1 补后零覆盖 = %.4f" % r["zero_cover_after_fill"])
    print("  D-B6-1 k=%d recall=%.4f ｜ D-B6-3 阳性覆盖=%.4f"
          % (r["D-B6-1_k"], r["D-B6-1_recall"], r["D-B6-3_coverage_pos"]))
    print("  AUC=%.4f  平衡准确率=%.4f" % (r["auc"] or 0, r["balanced_acc"]))
    print("  D-B6-5 grep k=%d（流水线 %d）" % (r["D-B6-5_k_grep"], r["D-B6-1_k"]))

with open(os.path.join(OUT, "b8_e1_l3.json"), "w", encoding="utf-8") as f:
    json.dump({"target": "L3-SVEN（副靶）", "pos_n": len(pos), "neg_n": len(neg),
               "arms": res}, f, ensure_ascii=False, indent=1)
print("\n→ " + os.path.join(OUT, "b8_e1_l3.json"))
