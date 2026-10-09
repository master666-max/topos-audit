# -*- coding: utf-8 -*-
"""
topos.cli —— 命令行表面（ARCHITECTURE §9.5）。
B1 实现：selftest / space / pools / fields；decode / next 为 stub（B3/B4）。
"""
import argparse
import json
import sys

from topos.selftest import run_all
from topos.space import Space
from topos.report.json_out import build_report, write


def cmd_selftest(_args):
    ok, total = run_all()
    return 0 if ok == total else 1


def cmd_space(args):
    sp = Space(args.dir, args.axes)
    s = sp.summary()
    print("space 报告 —— %s" % args.dir)
    print("  单元 N=%d  耗时=%.2fs  嵌入维=%d  λ1残差=%.1e"
          % (s["n_units"], s["elapsed_s"], s["embed_dims"],
             s["lam_residual"] if s["lam_residual"] is not None else float("nan")))
    print("  五类耦合边: %s" % s["layer_edges"])
    print("  融合图边=%d（call 之外 +%d 条 = 多维增量）"
          % (s["fused_edges"], s["edges_outside_call"]))
    print("  场非空率: %s" % s["fields_nonnull"])
    print("  设计矩阵: %s" % s["coverage"])
    for w in s["design_warnings"]:
        print("  [告警] %s" % w)
    if args.json:
        p = write(build_report(sp), args.json)
        print("  → %s" % p)
    rc = 0
    if args.check:
        cov = s["coverage"]
        if cov["zero_cover_rate"] > 0:
            print("  --check FAIL: zero_cover_rate=%.3f > 0（覆盖均衡法则，E-X1）"
                  % cov["zero_cover_rate"])
            rc = 2
        else:
            print("  --check OK: 零覆盖 0%%, c_min=%d" % cov["c_min"])
    return rc


def cmd_pools(args):
    sp = Space(args.dir, args.axes)
    for row in sp.pool_overview():
        print("  %-28s width=%d" % (row["name"], row["width"]))
    print("  共 %d 池（空/超限池已丢 %d 条告警）"
          % (len(sp.rows), len(sp.design_warnings)))
    return 0


def cmd_fields(args):
    sp = Space(args.dir, args.axes)
    for name, rate in sp.fields_nonnull().items():
        print("  %-16s 非空率 %.3f" % (name, rate))
    return 0


def cmd_stub(args):
    print("该子命令属后续批次（见 WORK-ORDERS.md）：decode=B3(W5) / next=B4(W4)。"
          "B1 未实现，拒绝假实现。")
    return 3


def cmd_crosscheck(args):
    from topos.crosscheck import crosscheck_dir
    results = crosscheck_dir(args.dir, args.axes)
    ok_n = 0
    for name, ok, detail in results:
        if ok is None:
            print("SKIP %s  |  %s" % (name, detail))
        else:
            ok_n += 1 if ok else 0
            print("%s %s  |  %s" % ("PASS " if ok else "FAIL ", name, detail))
    judged = sum(1 for _, ok, _ in results if ok is not None)
    print("=" * 56)
    print("crosscheck %d/%d PASS" % (ok_n, judged))
    return 0 if ok_n == judged else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="topos", description="ToposAudit —— "
                                 "在拓扑空间上做统计最优的缺陷检出")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("selftest", help="契约自检 12 项")

    sp = sub.add_parser("space", help="建空间")
    sp.add_argument("dir")
    sp.add_argument("--axes", default=None)
    sp.add_argument("--json", default=None)
    sp.add_argument("--check", action="store_true",
                    help="覆盖诊断不达标（零覆盖>0）则退出码 2")

    pp = sub.add_parser("pools", help="池概览")
    pp.add_argument("dir")
    pp.add_argument("--axes", default=None)

    fp = sub.add_parser("fields", help="场非空率")
    fp.add_argument("dir")
    fp.add_argument("--axes", default=None)

    dc = sub.add_parser("decode", help="[B3] 解码 → belief")
    dc.add_argument("space_json")
    nx_ = sub.add_parser("next", help="[B4] σ 排序 → 下一池或 STOP")
    nx_.add_argument("space_json")
    nx_.add_argument("belief_json")

    ck = sub.add_parser("crosscheck", help="对拍钩子：Forman/λ₂ vs 参考件")
    ck.add_argument("dir")
    ck.add_argument("--axes", default=None)

    args = ap.parse_args(argv)
    return {"selftest": cmd_selftest, "space": cmd_space, "pools": cmd_pools,
            "fields": cmd_fields, "decode": cmd_stub, "next": cmd_stub,
            "crosscheck": cmd_crosscheck}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
