# -*- coding: utf-8 -*-
"""_run1_dsh.py —— RUN1 首战辅助：建空间 + 导出边表 + 生成观测。

按 PREREG/RUN1-dsh.md 口径执行：
  obs = 池内任一单元 anchor 场非空 → 1（bandit 33 tag 正则确定性信号）。
topos 对靶仓只读；产物全部落在 EXP/run1_dsh/。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from topos.space import Space                                        # noqa: E402
from topos.report.json_out import build_report, write                # noqa: E402
from topos.core.fuse import fuse                                     # noqa: E402
from topos.core.layers import to_adj                                 # noqa: E402

TARGET = os.path.join(REPO, "tools", "repos", "dsh-launcher")
OUT = os.path.join(HERE, "run1_dsh")


def main():
    manifest = sys.argv[1] if len(sys.argv) > 1 else None
    tag = sys.argv[2] if len(sys.argv) > 2 else ""
    out_dir = os.path.join(OUT, tag) if tag else OUT
    os.makedirs(out_dir, exist_ok=True)
    sp = Space(TARGET, manifest_path=manifest)
    rep = build_report(sp)
    sj = write(rep, os.path.join(out_dir, "space.json"))
    print("① 空间[%s]：单元 %d ｜ 融合边 %d ｜ 耗时 %ss"
          % (tag or "default", rep["n_units"], rep["fused_edges"],
             rep["elapsed_s"]))
    cov = rep["coverage"]
    print("   覆盖三诊断：n_pools=%s c_min=%s c_mean=%s zero_cover=%s"
          % (cov["n_pools"], cov["c_min"], cov["c_mean"], cov["zero_cover_rate"]))
    print("   场非空率：%s" % rep["fields_nonnull"])
    if rep["design_warnings"]:
        print("   设计告警：%s" % rep["design_warnings"])

    # 边表（图先验用）：融合图 → {u: [v,...]}
    alpha = sp.manifest.get("layers", {})
    fused = fuse(sp.layers, alpha)
    adj = to_adj(fused)
    adj_d = {str(i): sorted(vs) for i, vs in adj.items()}
    with open(os.path.join(out_dir, "adj.json"), "w", encoding="utf-8") as f:
        json.dump(adj_d, f)
    print("② 边表 adj.json：%d 节点" % len(adj_d))

    # 观测：池内任一单元 anchor 非空 → 1（PREREG/RUN1 口径）
    # regex 场返回 {unit_idx: [命中tag]}（axis/methods/regex.py）
    anchor = sp.fields.get("anchor")
    obs, hit_units = {}, 0
    for nm, members in sp.rows:
        y = 0
        for i in members:
            if anchor.get(i):
                y = 1
                hit_units += 1
        obs[nm] = y
    with open(os.path.join(out_dir, "obs.json"), "w", encoding="utf-8") as f:
        json.dump(obs, f)
    print("③ 观测 obs.json：%d 池 → %s" % (len(obs), obs))
    print("   anchor 命中单元（去重计次）：%d" % hit_units)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
