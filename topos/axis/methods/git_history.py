# -*- coding: utf-8 -*-
"""
topos.axis.methods.git_history —— 演化场（T 层）。方法注册名 "git"。
metrics：commits（提交次数）/ age_days（首末提交跨度天）。
git CLI 缺失或目标非 git 仓 → 全 None（如实降级，禁止填 0——ADR-A12）。
搬迁自 mini-lab/coord_mini.git_churn + git_axis（E-T3 咬合件：8/1 commits 精确恢复）。
"""
import subprocess
import shutil

from topos.axis.registry import field_method


def git_churn(root, files):
    """{rel_path: {commits, age_days}}；非 git 环境/无历史 → None。"""
    if shutil.which("git") is None:
        return None
    try:
        inside = subprocess.run(
            ["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        inside = "false"
    if inside != "true":
        return None
    out = {}
    for rel in files:
        try:
            r = subprocess.run(
                ["git", "-C", root, "log", "--follow", "--pretty=%at", "--", rel],
                capture_output=True, text=True, timeout=15)
            ts = sorted(int(x) for x in r.stdout.split() if x.strip().isdigit())
            if ts:
                out[rel] = {"commits": len(ts),
                            "age_days": (ts[-1] - ts[0]) // 86400}
        except Exception:
            out[rel] = None
    return out


@field_method("git")
def git_field(units, params, ctx):
    metric = params.get("metric", "commits")
    if metric not in ("commits", "age_days"):
        raise ValueError("unknown git metric: %s" % metric)
    ch = git_churn(ctx["root"], sorted({u["file"] for u in units}))
    out = {}
    for i, u in enumerate(units):
        c = (ch or {}).get(u["file"])
        if c is None:
            out[i] = None
        else:
            out[i] = c[metric]
    return out
