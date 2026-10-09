# -*- coding: utf-8 -*-
"""
EXP/exp_b2_e1.py —— E-B2-1 Hui–Walter 合成验证（PREREG/B2 判据逐条对照）。
判据：①点估计 |err|<0.05 ②真值落 95% CI ③ρ=0.4 对照下偏离（仪器对假共识敏感）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topos.calib.hui_walter import synth_two_sources, hui_walter, bootstrap_ci  # noqa: E402

SEED = 20261009
TRUE = {"pi1": 0.05, "pi2": 0.20, "se1": 0.80, "sp1": 0.95, "se2": 0.90, "sp2": 0.85}
PARAM_MAP = [("pi", 1, "pi1"), ("pi", 2, "pi2"),
             ("se", 0, "se1"), ("sp", 0, "sp1"), ("se", 1, "se2"), ("sp", 1, "sp2")]


def run_case(tag, rho):
    tables = synth_two_sources(2000, 2000, TRUE["pi1"], TRUE["pi2"],
                               TRUE["se1"], TRUE["sp1"], TRUE["se2"], TRUE["sp2"],
                               rho_fp=rho, seed=SEED + int(rho * 100))
    est = hui_walter(tables, seed=SEED)
    print("== %s (rho_fp=%.2f) ==" % (tag, rho))
    print("  观测表: g1=%s g2=%s" % (dict(tables[1]), dict(tables[2])))
    errs = {}
    ci = None
    for kind, key, name in PARAM_MAP:
        e = est[kind][key]
        t = TRUE[name]
        errs[name] = abs(e - t)
        print("  %-4s est=%.4f true=%.2f |err|=%.4f" % (name, e, t, errs[name]))
    ok1 = all(v < 0.05 for v in errs.values())
    if rho == 0.0:
        ci = bootstrap_ci(tables, n_boot=1000, seed=SEED + 5)
        ok2 = True
        for kind, key, name in PARAM_MAP:
            lo, hi = ci[kind][key]
            inside = lo <= TRUE[name] <= hi
            ok2 &= inside
            print("  %-4s CI=[%.3f, %.3f] 含真值: %s" % (name, lo, hi, inside))
    else:
        ok2 = None
    ok3 = any(v >= 0.05 for v in errs.values())
    print("  判据① |err|<0.05 全部: %s  ② CI 含真值: %s  ③ 偏离(对照要求): %s"
          % (ok1, ok2, ok3))
    return {"tag": tag, "errs": errs, "ok1": ok1, "ok2": ok2, "ok3": ok3}


def main():
    r0 = run_case("主实验（独立源）", 0.0)
    r1 = run_case("假共识对照", 0.4)
    # 判据① v1.1：20 次重复合成的平均 |err|<0.05（估计器无偏性，消单次抽样噪声）
    import statistics
    errs = {k: [] for k in TRUE}
    for rep in range(20):
        t = synth_two_sources(2000, 2000, TRUE["pi1"], TRUE["pi2"],
                              TRUE["se1"], TRUE["sp1"], TRUE["se2"], TRUE["sp2"],
                              seed=SEED + rep)
        est = hui_walter(t, seed=SEED + rep)
        for kind, key, name in PARAM_MAP:
            errs[name].append(abs(est[kind][key] - TRUE[name]))
    ok1v11 = all(statistics.mean(v) < 0.05 for v in errs.values())
    print("== 判据① v1.1（20 次重复平均 |err|<0.05）==")
    for name, v in errs.items():
        print("  %-4s mean=%.4f max=%.4f" % (name, statistics.mean(v), max(v)))
    print("  → %s" % ok1v11)
    print("=" * 62)
    verdict = ok1v11 and r0["ok2"] and r1["ok3"]
    print("E-B2-1 判定: %s" % ("咬合" if verdict else "不咬合"))
    print("  ①v1.1 20 次平均全过: %s  ② CI 全含真值: %s  ③ 对照确认敏感: %s"
          % (ok1v11, r0["ok2"], r1["ok3"]))
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
