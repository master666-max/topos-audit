# -*- coding: utf-8 -*-
"""
EXP/make_b2_e4_sample.py —— 生成 E-B2-4 的 100 个仲裁单元抽样清单。
抽样规则（PREREG/B2 E-B2-4）：按池分层，**零覆盖单元强制入样**（E-X1 教训：
盲区里的缺陷不可检出，若不入样，标定出的 Se/Sp 只在"池选中区域"有效）。
输出 CSV，truth/defect_type/annotator/date 列留空给人填。
"""
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topos.space import Space  # noqa: E402

TARGET = r"C:\Users\26672\.workbuddy\binaries\python\versions\3.13.12\Lib"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "B2-E4-sample.csv")
SEED = 20261009
QUOTA = {"zero_cover": 25, "anchor": 25, "confluence": 20, "random": 30}


def main():
    if not os.path.isdir(TARGET):
        print("目标目录不存在: %s" % TARGET)
        return 1
    sp = Space(TARGET)
    n = sp.n
    if n == 0:
        print("目标仓 0 单元——中止（不产出空清单）")
        return 1
    print("目标仓单元 N=%d  池=%d  覆盖=%s" % (n, len(sp.rows), sp.coverage))
    covered = set()
    pool_of = {}
    for name, members in sp.rows:
        for i in members:
            covered.add(i)
            pool_of.setdefault(i, []).append(name)
    zero = [i for i in range(n) if i not in covered]
    print("  零覆盖单元 %d 个（%.1f%%）" % (len(zero), 100.0 * len(zero) / max(n, 1)))

    anchor_field = sp.fields.get("anchor", {})
    anchor_hit = [i for i in range(n) if anchor_field.get(i)]
    curv = sp.fields.get("forman", {})
    curv_vals = sorted(v for v in curv.values() if v is not None)
    thr = curv_vals[len(curv_vals) // 3] if curv_vals else None
    confluence = [i for i in range(n)
                  if curv.get(i) is not None and thr is not None and curv[i] <= thr]

    rng = random.Random(SEED)
    picked = {}
    for i in rng.sample(zero, min(QUOTA["zero_cover"], len(zero))):
        picked[i] = "zero_cover"
    for i in rng.sample(anchor_hit, min(QUOTA["anchor"], len(anchor_hit))):
        picked.setdefault(i, "anchor")
    for i in rng.sample(confluence, min(QUOTA["confluence"], len(confluence))):
        picked.setdefault(i, "confluence")
    rest = [i for i in range(n) if i not in picked]
    need = 100 - len(picked)
    for i in rng.sample(rest, min(need, len(rest))):
        picked.setdefault(i, "random")
    if len(picked) < 100:                       # 诚实补足记录
        for i in range(n):
            if len(picked) >= 100:
                break
            picked.setdefault(i, "fill")
        print("  [如实] 候选不足，补入 %d 个 fill 层单元" % (100 - len(picked)))

    rows = []
    for i, stratum in sorted(picked.items()):
        u = sp.units[i]
        tags = anchor_field.get(i) or []
        hint = ("零覆盖：不在任何池内，盲区核查" if stratum == "zero_cover"
                else "锚点命中 %s" % (",".join(tags) if tags else "-")
                if stratum == "anchor"
                else "曲率汇合点 forman=%s" % curv.get(i) if stratum == "confluence"
                else "随机层")
        rows.append({
            "unit_id": u["id"], "file": u["file"], "name": u["name"],
            "loc": u["loc"], "stratum": stratum,
            "in_pools": "|".join(pool_of.get(i, [])),
            "anchor_tags": "|".join(tags), "forman": curv.get(i),
            "evidence_hint": hint,
            "truth": "", "defect_type": "", "annotator": "", "date": "",
            "source_layer": "L4-arbitration",
        })
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("  分层分布: %s" % dict(Counter(r["stratum"] for r in rows)))
    print("  已写出: %s (%d 行)" % (OUT, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
