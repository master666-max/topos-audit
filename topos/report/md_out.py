# -*- coding: utf-8 -*-
"""
topos.report.md_out —— MD 报告渲染（W5④/W7「解锁美化」，B3 欠账 2026-10-10 补做）。
输入 = json_out.build_report 产物（topos-space/1）+ 可选 belief（topos-belief/1）。
契约：coverage 必填诊断字段缺失即抛异常（与 json_out 同款）；只渲染不计算，
任何数字都来自上游 JSON——本模块不得自产数字（防双源漂移）。
"""
REQUIRED_COVERAGE_KEYS = ("n_pools", "c_min", "c_mean", "zero_cover_rate",
                          "pool_sizes")


def _check_coverage(rep):
    cov = rep.get("coverage", {})
    for k in REQUIRED_COVERAGE_KEYS:
        if k not in cov:
            raise ValueError("coverage 缺必填诊断字段 %s——缺失即 bug" % k)
    return cov


def render_space_md(rep):
    """topos-space/1 → MD。缺必填诊断字段即抛异常（缺失=bug 不是可选）。"""
    cov = _check_coverage(rep)
    L = []
    L.append("# topos space 报告")
    L.append("")
    L.append("- schema: `%s`" % rep.get("schema", "?"))
    L.append("- root: `%s`" % rep.get("root", "?"))
    L.append("- manifest: `%s`" % rep.get("manifest", "?"))
    L.append("- 单元数: %d ｜ 耗时: %ss" % (rep.get("n_units", 0),
                                           rep.get("elapsed_s", "?")))
    L.append("")
    L.append("## 分层耦合边")
    L.append("")
    L.append("| 层 | 边数 |")
    L.append("|---|---|")
    for k in sorted(rep.get("layer_edges", {})):
        L.append("| %s | %d |" % (k, rep["layer_edges"][k]))
    L.append("| **融合** | **%d** |" % rep.get("fused_edges", 0))
    if rep.get("edges_outside_call"):
        L.append("")
        L.append("> 非 call 层边 %d 条——按「如实降级」口径计入融合，不作召回承诺。"
                 % rep["edges_outside_call"])
    L.append("")
    L.append("## 覆盖诊断（必填三诊断）")
    L.append("")
    L.append("| 指标 | 值 |")
    L.append("|---|---|")
    L.append("| 池数 n_pools | %s |" % cov["n_pools"])
    L.append("| 最小池覆盖 c_min | %s |" % cov["c_min"])
    L.append("| 平均池覆盖 c_mean | %s |" % cov["c_mean"])
    L.append("| 零覆盖率 zero_cover_rate | %s |" % cov["zero_cover_rate"])
    L.append("")
    L.append("池大小分布：`%s`" % (cov["pool_sizes"],))
    fnn = rep.get("fields_nonnull", {})
    if fnn:
        L.append("")
        L.append("## 场非空率")
        L.append("")
        L.append("| 场 | 非空率 |")
        L.append("|---|---|")
        for k in sorted(fnn):
            L.append("| %s | %s |" % (k, fnn[k]))
    if rep.get("design_warnings"):
        L.append("")
        L.append("## 设计矩阵告警")
        L.append("")
        for w in rep["design_warnings"]:
            L.append("- %s" % w)
    if rep.get("pools"):
        L.append("")
        L.append("## 池概览")
        L.append("")
        L.append("```json")
        L.append(json_dumps(rep["pools"]))
        L.append("```")
    return "\n".join(L) + "\n"


def render_belief_md(bel, top_n=10):
    """topos-belief/1 → MD（top-N 后验表）。"""
    L = []
    L.append("## 解码后验（topos-belief/%s）" % str(
        bel.get("schema", "?").split("/")[-1]))
    L.append("")
    L.append("- decoder: `%s`" % bel.get("decoder", "?"))
    items = sorted((bel.get("belief") or {}).items(), key=lambda kv: -kv[1])
    L.append("")
    L.append("| # | 单元 | 后验 |")
    L.append("|---|---|---|")
    for i, (uid, p) in enumerate(items[:top_n], 1):
        L.append("| %d | `%s` | %.4f |" % (i, uid, p))
    if len(items) > top_n:
        L.append("")
        L.append("> 其余 %d 单元后验低于第 %d 名，从略。" % (len(items) - top_n,
                                                          top_n))
    return "\n".join(L) + "\n"


def render_md(rep, belief=None, top_n=10):
    """space 报告（+ 可选 belief）→ 完整 MD。"""
    md = render_space_md(rep)
    if belief is not None:
        md += "\n" + render_belief_md(belief, top_n=top_n)
    return md


def json_dumps(obj):
    import json
    return json.dumps(obj, ensure_ascii=False, indent=1)
