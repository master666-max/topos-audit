# -*- coding: utf-8 -*-
"""B6 端到端检出评测 —— **副靶 L3 SVEN**（368 对，本地可跑）。

主靶 L1（112 缺陷 / 7 项目）需下载 BugsInPy 各项目的历史源码，本批未跑，另开。
本脚本跑的是 `PREREG/B6.md` §2 的**副靶**：可算平衡准确率与 AUC，只作旁证。

冻结纪律（T-B6-c）：清单 = 仓内默认 `axes.json`，**不做任何调整**；
产物写新目录 `EXP/b6_e1/`，不覆盖任何既有件（B6 §3 数据保全）。
"""
import csv
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "b6_e1")
os.makedirs(OUT, exist_ok=True)

SVEN_DIR = os.path.join(REPO, "tools", "repos", "sven_space")
FUNCS = os.path.join(HERE, "l3_sven", "functions.jsonl")
GOLD = os.path.join(REPO, "calib", "gold_l3_sven.csv")
AXES = os.path.join(REPO, "axes.json")

# ---- 清单冻结指纹（T-B6-c 防"把靶的信息喂进设计"）----
with open(AXES, "rb") as f:
    MANIFEST_SHA = hashlib.sha256(f.read()).hexdigest()[:16]
print("manifest_sha =", MANIFEST_SHA, "（默认 axes.json，未做任何调整）")

# ---- 真值：unit_id -> truth ----
truth = {}
with open(GOLD, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        truth[row["unit_id"]] = int(row["truth"])
print("gold 行数 =", len(truth), " 阳性 =", sum(truth.values()))

# ---- 文件 → unit_id 映射（与 _l3_check.py 同序：u%05d.py）----
order = []
with open(FUNCS, encoding="utf-8") as f:
    for ln in f:
        if ln.strip():
            order.append(json.loads(ln)["unit_id"])
file2gold = {}
for i, uid in enumerate(order):
    file2gold["u%05d.py" % i] = uid

# ---- 建空间 ----
from topos.space import Space            # noqa: E402
sp = Space(SVEN_DIR, manifest_path=AXES)
print("n_units =", sp.n, " 池数 =", len(sp.rows),
      " zero_cover = %.4f" % sp.coverage["zero_cover_rate"])

# ---- 单元 → 真值对齐（B6 §1.3：按 id 精确对齐，禁模糊匹配）----
uid_of = [u["id"] if isinstance(u, dict) else str(u) for u in sp.units]
gold_of, hit_gold = {}, set()
for i, sid in enumerate(uid_of):
    fn = sid.split("::", 1)[0]
    g = file2gold.get(fn)
    if g is not None and g in truth:
        gold_of[i] = truth[g]
        hit_gold.add(g)
pos = [i for i, t in gold_of.items() if t == 1]
neg = [i for i, t in gold_of.items() if t == 0]
print("对齐：真值侧命中 %d / %d；检出侧对齐单元 %d（阳 %d 阴 %d）"
      % (len(hit_gold), len(truth), len(gold_of), len(pos), len(neg)))

# ---- A 臂观测：anchor 正则（确定性信号）----
anchor = sp.fields.get("anchor", {})


def anchor_hit(i):
    v = anchor.get(i)
    if v is None:
        return False
    return bool(v) if not isinstance(v, (list, tuple, set)) else len(v) > 0


pools = [(nm, set(m)) for nm, m in sp.rows]
obs = [(nm, 1 if any(anchor_hit(i) for i in m) else 0) for nm, m in pools]
print("A 臂观测：阳性池 %d / %d" % (sum(y for _, y in obs), len(obs)))

# ---- 解码 ----
from topos.infer.decode import decode_nb        # noqa: E402
from topos.stop import weitzman as W            # noqa: E402
belief = decode_nb(pools, obs, sp.n, se=0.9, sp_=0.95, prior=1.0 / 250)

# ---- 8 池预算：按 σ 降序开（B6 §1.5 固定 8 次开池）----
BUDGET = 8
mus = {nm: W.pool_value_mean([(nm, m)], belief)[nm] for nm, m in pools}
sigmas = {}
for nm, m in pools:
    if not m:
        sigmas[nm] = 0.0
        continue
    sigmas[nm] = W.sigma_exact([belief.get(i, 0.0) for i in m], 0.05)
opened = [nm for nm, _ in sorted(sigmas.items(), key=lambda kv: -kv[1])][:BUDGET]
reviewed = set()
for nm, m in pools:
    if nm in opened:
        reviewed |= m
print("已开池 %d 个：%s" % (len(opened), ", ".join(opened)))
print("人工核验单元数（并集）= %d（占 %.1f%%）"
      % (len(reviewed), 100.0 * len(reviewed) / max(sp.n, 1)))

# ---- D-B6-1 检出 k/n ----
k = sum(1 for i in reviewed if gold_of.get(i) == 1)
n_pos = len(pos)
print("\nD-B6-1 检出：k=%d / n=%d  ⇒ recall=%.4f" % (k, n_pos, k / max(n_pos, 1)))

# ---- D-B6-3 覆盖（守门读数）----
cov_pos = sum(1 for i in pos if any(i in m for _nm, m in pools))
print("D-B6-3 覆盖：已知阳性中被至少一池覆盖 %d / %d = %.4f  （门 ≥0.50）"
      % (cov_pos, n_pos, cov_pos / max(n_pos, 1)))

# ---- D-B6-2 误报：已核验单元里判为"命中"的阴性 ----
hits = [i for i in reviewed if anchor_hit(i)]
fp = sum(1 for i in hits if gold_of.get(i) == 0)
tp = sum(1 for i in hits if gold_of.get(i) == 1)
print("D-B6-2 误报：命中 %d 条（真阳 %d / 误报 %d）⇒ 误报率 %.4f"
      % (len(hits), tp, fp, fp / max(len(hits), 1)))

# ---- 平衡准确率 / AUC（副靶专有，因有阴有阳）----
scored = sorted(gold_of, key=lambda i: -belief.get(i, 0.0))
ys = [gold_of[i] for i in scored]
P, N = sum(ys), len(ys) - sum(ys)
rank_sum = sum(r + 1 for r, y in enumerate(ys) if y == 1)
auc = (rank_sum - P * (P + 1) / 2.0) / (P * N) if (P and N) else None
# 平衡准确率：取阈值使预测阳性数 = 已核验数
cut = max(1, len(reviewed))
pred = set(scored[:cut])
sens = sum(1 for i in pos if i in pred) / max(len(pos), 1)
spec = sum(1 for i in neg if i not in pred) / max(len(neg), 1)
print("副靶附加：AUC=%.4f  平衡准确率=%.4f（sens=%.4f spec=%.4f）"
      % (auc or float("nan"), (sens + spec) / 2, sens, spec))

# ---- D-B6-5 grep 对照臂 ----
DANGER = re.compile(r"\b(subprocess|os\.system|eval\s*\(|exec\s*\(|pickle\.loads"
                    r"|yaml\.load\s*\(|shell\s*=\s*True|os\.popen)\b")
grep_files = set()
for fn in os.listdir(SVEN_DIR):
    if not fn.endswith(".py"):
        continue
    with open(os.path.join(SVEN_DIR, fn), encoding="utf-8", errors="ignore") as f:
        if DANGER.search(f.read()):
            grep_files.add(fn)
grep_idx = sorted(i for i, sid in enumerate(uid_of)
                  if sid.split("::", 1)[0] in grep_files)
grep_review = set(grep_idx[:len(reviewed)])       # 同人工核验预算
k_grep = sum(1 for i in grep_review if gold_of.get(i) == 1)
print("\nD-B6-5 grep 对照臂：命中文件 %d，同预算核验 %d 单元 ⇒ k_grep=%d"
      % (len(grep_files), len(grep_review), k_grep))
print("流水线 k=%d vs grep k=%d ⇒ %s"
      % (k, k_grep,
         "✅ 流水线 > grep" if k > k_grep else
         ("＝ 持平" if k == k_grep else "❌ 流水线 < grep（按 T-B6 如实报）")))

res = {
    "target": "L3-SVEN（副靶，只作旁证）",
    "manifest_sha": MANIFEST_SHA,
    "n_units": sp.n,
    "n_pools": len(sp.rows),
    "zero_cover_rate": sp.coverage["zero_cover_rate"],
    "gold_rows": len(truth), "gold_pos": sum(truth.values()),
    "aligned_gold": len(hit_gold), "aligned_units": len(gold_of),
    "pos_n": n_pos, "neg_n": len(neg),
    "opened_pools": opened,
    "reviewed_units": len(reviewed),
    "D-B6-1_k": k, "D-B6-1_recall": k / max(n_pos, 1),
    "D-B6-2_hits": len(hits), "D-B6-2_fp": fp,
    "D-B6-2_fp_rate": fp / max(len(hits), 1),
    "D-B6-3_coverage": cov_pos / max(n_pos, 1),
    "D-B6-4_k_per_pool": k / float(BUDGET),
    "D-B6-5_k_grep": k_grep,
    "auc": auc, "balanced_acc": (sens + spec) / 2,
}
with open(os.path.join(OUT, "b6_e1_l3.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("\n→ " + os.path.join(OUT, "b6_e1_l3.json"))
