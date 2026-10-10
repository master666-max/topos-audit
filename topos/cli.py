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
    sp = Space(args.dir, args.axes, lang=getattr(args, "lang", "py"))
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
    print("该子命令属后续批次（见 WORK-ORDERS.md）：next=B4(W4)。"
          "B1 未实现，拒绝假实现。")
    return 3


def cmd_decode(args):
    """topos decode <space.json> --obs <obs.json> [--decoder nb] → belief.json

    space.json 须含 pool_members/units（topos-space/1，B3 起必带）；
    obs.json = {pool_name: y}。输出 topos-belief/1。
    """
    import os
    from topos.infer.decode import decode, belief_json, DECODERS
    from topos.infer.prior import power_lam_max, adaptive_alpha, diffuse

    if args.decoder not in DECODERS:
        print("未知解码器 %r（可选 %s）" % (args.decoder, DECODERS))
        return 2
    with open(args.space_json, encoding="utf-8") as f:
        sj = json.load(f)
    if sj.get("schema") != "topos-space/1":
        print("schema 不是 topos-space/1：%r" % sj.get("schema"))
        return 2
    if "pool_members" not in sj or "units" not in sj:
        print("space.json 缺 pool_members/units（旧版产物，请用 topos space --json 重出）")
        return 2
    with open(args.obs, encoding="utf-8") as f:
        obs_d = json.load(f)
    n = sj["n_units"]
    pools = [(nm, set(m)) for nm, m in sj["pool_members"]]
    missing = [nm for nm, _m in pools if nm not in obs_d]
    if missing:
        print("obs 缺 %d 个池：%s…" % (len(missing), missing[:3]))
        return 2
    obs = [(nm, int(obs_d[nm])) for nm, _m in pools]

    params = {"se": args.se, "sp": args.sp, "prior": args.prior, "steps": 0,
              "alpha_mode": "none"}
    if args.decoder == "nb" and args.prior_steps > 0:
        adj = [set() for _ in range(n)]
        # space.json 不带边表；图先验可选：需要边表时用 --adj 提供（默认关）
        if args.adj:
            with open(args.adj, encoding="utf-8") as f:
                for u, vs in json.load(f).items():
                    adj[int(u)] = {int(v) for v in vs}
            alphas, meta = adaptive_alpha(pools, adj, n)
            params.update({"steps": args.prior_steps,
                           "alpha_mode": "adaptive(panacity phi)",
                           "lam_max": meta["lam_max"],
                           "phi_med": meta["phi_med"]})
        if params["steps"] == 0:
            print("提示：NB 图先验未启用（--adj 未提供边表），退化为纯 NB。")

    belief = decode(pools, obs, n, method=args.decoder, se=args.se,
                    sp=args.sp, prior=args.prior)
    if params["steps"] > 0:
        import math
        zb = [belief[i] for i in range(n)]
        z = [math.log(max(min(b, 1 - 1e-9), 1e-9) /
                      (1 - max(min(b, 1 - 1e-9), 1e-9))) for b in zb]
        zd = diffuse(z, adj, n, alphas, params["steps"])
        belief = {i: 1.0 / (1.0 + math.exp(-max(min(zd[i], 500.0), -500.0)))
                  for i in range(n)}
    out = belief_json(args.decoder, belief, params,
                      unit_ids=sj.get("units"))
    dest = args.o or os.path.splitext(args.space_json)[0] + ".belief.json"
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    vals = sorted(belief.values())
    print("decode[%s] N=%d 池=%d belief[min=%.4f med=%.4f max=%.4f] → %s"
          % (args.decoder, n, len(pools), vals[0],
             vals[len(vals) // 2], vals[-1], dest))
    return 0


def cmd_next(args):
    """topos next <space_json> <belief_json> [--opened a,b,c] → 下一池或 STOP（B4）。"""
    from topos.stop import weitzman as W
    with open(args.space_json, encoding="utf-8") as f:
        sj = json.load(f)
    if sj.get("schema") != "topos-space/1" or "pool_members" not in sj:
        print("space.json 不合法（需 topos-space/1 + pool_members）")
        return 2
    with open(args.belief_json, encoding="utf-8") as f:
        bj = json.load(f)
    if bj.get("schema") != "topos-belief/1":
        print("belief.json 不合法（需 topos-belief/1）")
        return 2
    belief = {int(k): v for k, v in bj["belief"].items()}
    pools = [(nm, set(m)) for nm, m in sj["pool_members"]]
    opened = set(x for x in (args.opened or "").split(",") if x)
    mus = W.pool_value_mean(pools, belief)
    remaining = [(nm, m) for nm, m in pools if nm not in opened]
    sigmas = {nm: W.sigma_exact([belief.get(i, 0.0) for i in m], args.cost0)
              for nm, m in remaining}
    confirmed = max((mus[nm] for nm in opened), default=0.0)
    print("已开 %d 池，confirmed=%.4f；候选 %d 池" %
          (len(opened), confirmed, len(remaining)))
    if W.stop_decision({k: v for k, v in sigmas.items()
                        if k not in opened}, confirmed):
        print("STOP —— max(剩余σ)=%.4f ≤ confirmed=%.4f"
              % (max(sigmas.values()) if sigmas else 0.0, confirmed))
        return 0
    pick = W.next_pool(remaining, sigmas)
    top = sorted(sigmas.items(), key=lambda kv: -kv[1])[:5]
    for nm, s in top:
        print("  σ=%-8.4f %s" % (s, nm))
    print("NEXT → %s（σ=%.4f）" % (pick[0], sigmas[pick[0]]))
    return 0


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


def cmd_report_md(args):
    """topos report-md <space.json> [--belief belief.json] [-o out.md] → MD 报告

    W5④/W7「MD 报告渲染」落地（B3 欠账 2026-10-10 补做）。只渲染不计算：
    coverage 必填诊断字段缺失即抛异常（与 json_out 同款契约）。
    """
    from topos.report.md_out import render_md
    with open(args.space_json, encoding="utf-8") as f:
        rep = json.load(f)
    if rep.get("schema") != "topos-space/1":
        print("schema 不是 topos-space/1：%r" % rep.get("schema"))
        return 2
    bel = None
    if args.belief:
        with open(args.belief, encoding="utf-8") as f:
            bel = json.load(f)
        if bel.get("schema") != "topos-belief/1":
            print("belief schema 不是 topos-belief/1：%r" % bel.get("schema"))
            return 2
    md = render_md(rep, bel, top_n=args.top)
    out = args.o or (os.path.splitext(args.space_json)[0] + ".md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print("→ %s" % out)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="topos", description="ToposAudit —— "
                                 "在拓扑空间上做统计最优的缺陷检出")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("selftest", help="契约自检 12 项")

    sp = sub.add_parser("space", help="建空间")
    sp.add_argument("dir")
    sp.add_argument("--axes", default=None)
    sp.add_argument("--lang", default="py", choices=["py", "js"],
                    help="语言后端（js=正则级 [U]，PREREG/M5 D-A）")
    sp.add_argument("--json", default=None)
    sp.add_argument("--check", action="store_true",
                    help="覆盖诊断不达标（零覆盖>0）则退出码 2")

    pp = sub.add_parser("pools", help="池概览")
    pp.add_argument("dir")
    pp.add_argument("--axes", default=None)

    fp = sub.add_parser("fields", help="场非空率")
    fp.add_argument("dir")
    fp.add_argument("--axes", default=None)

    dc = sub.add_parser("decode", help="[B3] 解码 → belief（topos-belief/1）")
    dc.add_argument("space_json")
    dc.add_argument("--obs", required=True, help="观测 json：{pool_name: y}")
    dc.add_argument("--decoder", default="nb",
                    choices=["comp", "dd", "scomp", "nb"])
    dc.add_argument("--se", type=float, default=0.9)
    dc.add_argument("--sp", type=float, default=0.95)
    dc.add_argument("--prior", type=float, default=0.04)
    dc.add_argument("--prior-steps", dest="prior_steps", type=int, default=4,
                    help="NB 图先验扩散步数（0=关闭）")
    dc.add_argument("--adj", default=None,
                    help="边表 json（{u:[v,...]}），启用 NB 图先验必需")
    dc.add_argument("-o", default=None, help="输出 belief.json 路径")
    nx_ = sub.add_parser("next", help="[B4] σ 排序 → 下一池或 STOP")
    nx_.add_argument("space_json")
    nx_.add_argument("belief_json")
    nx_.add_argument("--opened", default=None,
                     help="已开池名（逗号分隔）；confirmed 由 belief 重算")
    nx_.add_argument("--cost0", type=float, default=0.05,
                     help="一次池检测动作成本（缺陷价值单位，PREREG/B4 v1.4 默认 0.05）")

    ck = sub.add_parser("crosscheck", help="对拍钩子：Forman/λ₂ vs 参考件")
    ck.add_argument("dir")
    ck.add_argument("--axes", default=None)

    rm = sub.add_parser("report-md",
                        help="[W5④] space/belief → MD 报告（只渲染不计算）")
    rm.add_argument("space_json")
    rm.add_argument("--belief", default=None, help="belief.json（topos-belief/1）")
    rm.add_argument("--top", type=int, default=10, help="后验表行数")
    rm.add_argument("-o", default=None, help="输出 .md 路径（默认与 space.json 同名）")

    args = ap.parse_args(argv)
    return {"selftest": cmd_selftest, "space": cmd_space, "pools": cmd_pools,
            "fields": cmd_fields, "decode": cmd_decode, "next": cmd_next,
            "crosscheck": cmd_crosscheck,
            "report-md": cmd_report_md}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
