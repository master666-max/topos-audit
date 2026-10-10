# -*- coding: utf-8 -*-
"""
EXP/make_b2_e4_modelside_stats.py —— 模型侧标注读数 + SHA256 密封

口径出处：PREREG/B2.md 判据锁定附录 v1.5
  · §C  比例 CI 用 **Wilson score**（禁用 Wald）
  · §B2 None 协议：**硬口（剔 None）与全口（None 作第三类）两口都报**；
        任一层 None 率 > 40% → 该层标「可判性不足」
  · §B3 主判读看**层内**；全池只作参考，**禁止用配额（25/25/20/30）加权合成**
        —— 故自然权版另用 framecheck 的真实框构成（stdlib 13203 / site-packages 4995）
  · §A1 序约束 π(anchor) > π(random) > π(zero_cover)，**软判定**：报违反幅度，
        并如实报 Wilson 区间是否重叠（重叠则定向不具证据力，不是"约束满足"）
  · §A5 密封：本脚本对 modelside.jsonl 算 SHA256 + 时间戳，写入 SEAL 段

输入：EXP/B2-E4-modelside.jsonl（模型侧 100 条判定）
      EXP/B2-E4-sample-mixed.csv（分层与 unit_id；**混合框版本**，从 bd3144a 恢复——
          现盘 B2-E4-sample.csv 已被并发会话于 01:47 原地覆盖为纯 stdlib 样本）
      EXP/B2-E4-framecheck.json（真实框构成，用于自然权）
输出：EXP/B2-E4-modelside-stats.json + stdout
不改任何既有产物。
"""
import csv
import hashlib
import json
import math
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
JSONL = os.path.join(HERE, "B2-E4-modelside.jsonl")
SAMPLE = os.path.join(HERE, "B2-E4-sample-mixed.csv")
FRAME = os.path.join(HERE, "B2-E4-framecheck.json")
OUT = os.path.join(HERE, "B2-E4-modelside-stats.json")

Z = 1.959963984540054  # 95%
NONE_RATE_DEADLINE = 0.40
QUOTA = {"zero_cover": 25, "anchor": 25, "confluence": 20, "random": 30}


def wilson(k, n):
    """Wilson score 区间。返回 (center, half_width, lo, hi)。n=0 时全 None。"""
    if n == 0:
        return None, None, None, None
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = (Z / d) * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return c, h, max(0.0, c - h), min(1.0, c + h)


def rates(rows):
    """一行 = 一个单元。返回三态计数与硬/全两口的 1 率 + Wilson。"""
    n_all = len(rows)
    n1 = sum(1 for r in rows if r["truth"] == 1)
    n0 = sum(1 for r in rows if r["truth"] == 0)
    nn = sum(1 for r in rows if r["truth"] is None)
    assert n1 + n0 + nn == n_all, "三态必须互斥且相加等于分母"
    judged = n1 + n0
    hard_c, hard_h, hard_lo, hard_hi = wilson(n1, judged)
    full_c, full_h, full_lo, full_hi = wilson(n1, n_all)
    none_c, none_h, _, _ = wilson(nn, n_all)
    return {
        "n": n_all, "n_defect": n1, "n_clean": n0, "n_none": nn,
        "hard_rate": {"k": n1, "n": judged, "p": hard_c,
                      "wilson_halfwidth": hard_h, "lo": hard_lo, "hi": hard_hi},
        "full_rate": {"k": n1, "n": n_all, "p": full_c,
                      "wilson_halfwidth": full_h, "lo": full_lo, "hi": full_hi},
        "none_rate": {"k": nn, "n": n_all, "p": none_c,
                      "wilson_halfwidth": none_h,
                      "exceeds_40pct": bool(none_c is not None
                                            and none_c > NONE_RATE_DEADLINE)},
    }


def main():
    recs = [json.loads(l) for l in open(JSONL, encoding="utf-8") if l.strip()]
    mixed = list(csv.DictReader(open(SAMPLE, encoding="utf-8-sig")))
    frame = json.load(open(FRAME, encoding="utf-8"))

    assert len(recs) == 100, "模型侧必须恰好 100 条，实得 %d" % len(recs)
    assert len(mixed) == 100, "混合框清单必须恰好 100 条，实得 %d" % len(mixed)

    # 按 seq 对齐（seq 是清单与工作簿共用的稳定键），unit_id 做交叉核对
    by_seq = {int(r["seq"]): r for r in mixed}
    assert {r["seq"] for r in recs} == set(by_seq), "seq 集合与清单不一致"
    mism = [(r["seq"], r["unit_id"], by_seq[r["seq"]]["unit_id"])
            for r in recs if r["unit_id"] != by_seq[r["seq"]]["unit_id"]]
    assert not mism, "unit_id 与清单不符（转写错）：%s" % mism[:5]

    for r in recs:
        m = by_seq[r["seq"]]
        r["stratum"] = m["stratum"]
        r["source"] = ("site-packages"
                       if m["file"].replace("\\", "/")
                       .startswith("site-packages/") else "stdlib")

    out = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "annotator": "model-side (AI), 单裁判",
           "protocol": "PREREG/B2.md 判据锁定附录 v1.5 §A1/§A5/§B2/§B3/§C",
           "frame_caveat": "本批 100 单元取自**混合框**（stdlib + site-packages 27.45%）。"
                           "并发会话已于 01:47 用排除 site-packages 的生成器**原地覆盖** "
                           "B2-E4-sample.csv 并在 9273432 提交纯 stdlib 新样本；混合框清单"
                           "已从 bd3144a 恢复为 B2-E4-sample-mixed.csv。新旧样本交集 29，"
                           "⇒ 本读数只对混合框有效，新样本有 72 单元未经模型侧裁判"}

    out["overall"] = rates(recs)

    out["by_stratum"] = {}
    for s in ("anchor", "random", "confluence", "zero_cover"):
        sub = [r for r in recs if r["stratum"] == s]
        d = rates(sub)
        d["quota_expected"] = QUOTA[s]
        d["quota_match"] = (len(sub) == QUOTA[s])
        out["by_stratum"][s] = d

    out["by_source"] = {src: rates([r for r in recs if r["source"] == src])
                        for src in ("stdlib", "site-packages")}

    # §B3：禁止配额加权合成 ⇒ 自然权版用真实框构成
    nat = frame["by_source"]
    tot = nat["stdlib"]["units"] + nat["site-packages"]["units"]
    w = {k: nat[k]["units"] / tot for k in ("stdlib", "site-packages")}
    out["natural_weighted"] = {
        "weights_from_framecheck": w,
        "note": "按真实框单元数加权（非配额加权）；仅作对照，主判读仍看层内",
    }
    for key in ("hard_rate", "full_rate", "none_rate"):
        out["natural_weighted"][key] = sum(
            (out["by_source"][s][key]["p"] or 0.0) * w[s]
            for s in ("stdlib", "site-packages"))

    # §A1 序约束（软判定）
    def p1(s):
        return out["by_stratum"][s]["hard_rate"]["p"] or 0.0
    seq = [("anchor", p1("anchor")), ("random", p1("random")),
           ("zero_cover", p1("zero_cover"))]
    viol = [(seq[i][0], seq[i + 1][0], seq[i][1] - seq[i + 1][1])
            for i in range(len(seq) - 1) if seq[i][1] <= seq[i + 1][1]]
    ov = []
    for a, b in (("anchor", "random"), ("random", "zero_cover")):
        ra, rb = out["by_stratum"][a]["hard_rate"], out["by_stratum"][b]["hard_rate"]
        ov.append({"pair": "%s vs %s" % (a, b),
                   "ci_overlap": bool(ra["hi"] >= rb["lo"] and rb["hi"] >= ra["lo"]),
                   "a_ci": [ra["lo"], ra["hi"]], "b_ci": [rb["lo"], rb["hi"]]})
    out["A1_order_constraint"] = {
        "expected": "pi(anchor) > pi(random) > pi(zero_cover)",
        "observed": {k: v for k, v in seq},
        "violations": viol,
        "satisfied": not viol,
        "ci_overlaps": ov,
        "verdict": ("序约束满足，但所有相邻对的 Wilson 区间重叠 ⇒ 定向由抽样噪声决定，"
                    "不具证据力" if not viol else
                    "序约束被违反，幅度见 violations"),
    }

    # 判定规则与验证方式分布
    from collections import Counter
    out["rule_distribution"] = dict(Counter(r["rule"] for r in recs))
    out["verified_distribution"] = dict(Counter(r["verified"] or "-" for r in recs))
    out["defects"] = [{"seq": r["seq"], "unit_id": r["unit_id"],
                       "defect_type": r["defect_type"], "verified": r["verified"],
                       "note": r["note"]} for r in recs if r["truth"] == 1]
    out["none_units"] = [{"seq": r["seq"], "unit_id": r["unit_id"],
                          "rule": r["rule"], "note": r["note"]}
                         for r in recs if r["truth"] is None]

    # §A5 密封
    blob = open(JSONL, "rb").read()
    out["seal"] = {
        "artifact": "EXP/B2-E4-modelside.jsonl",
        "sha256": hashlib.sha256(blob).hexdigest(),
        "bytes": len(blob),
        "sealed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "clause": "PREREG v1.5 §A5：模型侧读数在仲裁开始前落盘并记 SHA256；"
                  "人工裁定冻结后方可解封比对",
        "single_annotator_limit": "Krippendorff α / Gwet AC1 / Cohen κ 均需 >=2 名标注者；"
                                  "本文件只有模型侧一方 ⇒ α 不可计算，§B 全部判据待人工侧就位后才能起算",
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("defects", "none_units")},
                     ensure_ascii=False, indent=2))
    print("\nSHA256(modelside.jsonl) = %s" % out["seal"]["sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
