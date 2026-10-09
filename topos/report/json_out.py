# -*- coding: utf-8 -*-
"""
topos.report.json_out —— space.json 产物（schema topos-space/1）。
契约：schema 版本号必带；c_min / zero_cover_rate 是必填诊断字段，
缺失即 bug（抛异常），不存在"可选优化"。
"""
import json
import os

SCHEMA = "topos-space/1"
REQUIRED_COVERAGE_KEYS = ("n_pools", "c_min", "c_mean", "zero_cover_rate", "pool_sizes")


def build_report(space):
    s = space.summary()
    report = {
        "schema": SCHEMA,
        "root": space.root,
        "manifest": space.manifest_path,
        "n_units": s["n_units"],
        "elapsed_s": s["elapsed_s"],
        "layer_edges": s["layer_edges"],
        "fused_edges": s["fused_edges"],
        "edges_outside_call": s["edges_outside_call"],
        "embed": {"dims": s["embed_dims"], "lam_residual": s["lam_residual"]},
        "coverage": s["coverage"],
        "fields_nonnull": s["fields_nonnull"],
        "pools": space.pool_overview(),
        "design_warnings": s["design_warnings"],
    }
    cov = report["coverage"]
    for k in REQUIRED_COVERAGE_KEYS:
        if k not in cov:
            raise ValueError("coverage 缺必填诊断字段 %s——缺失即 bug" % k)
    return report


def write(report, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return path
