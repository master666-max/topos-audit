# -*- coding: utf-8 -*-
"""
topos.axis.methods.git_history —— 演化场（T 层）。方法注册名 "git"。
metrics（v0.2 T 族补齐，设计 §4.5「时间是一族场」）：
  commits       提交次数（E-T3 咬合件：8/1 commits 精确恢复，--follow 语义不变）
  age_days      首末提交跨度天
  authors       作者分散度：触达该文件的 distinct 作者数（§4.5 作者分散度）
  fix_coupling  缺陷修复耦合：消息含 fix/bug/修复 的 commit 触达本文件
                且同 commit 触达 ≥2 文件的次数（§4.5 缺陷修复耦合）
  stability     演化稳定性：1 − 近 90 天提交占比（值越高越稳）
git CLI 缺失或目标非 git 仓 → 全 None（如实降级，禁止填 0——ADR-A12）。
"""
import re
import subprocess
import shutil
import time

from topos.axis.registry import field_method

_FIX_RE = re.compile(r"fix|bug|修复", re.I)


def _git_ok(root):
    if shutil.which("git") is None:
        return False
    try:
        inside = subprocess.run(
            ["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        inside = "false"
    return inside == "true"


def git_churn(root, files):
    """{rel_path: {commits, age_days}}；非 git 环境/无历史 → None。
    语义保持 E-T3 咬合件原样（--follow）。"""
    if not _git_ok(root):
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


def _all_commits(root):
    """单次全仓 log 解析：[(ts, author, subject, [files])]；失败 → None。"""
    try:
        r = subprocess.run(
            ["git", "-C", root, "log", "--pretty=%at|%an|%s", "--name-only"],
            capture_output=True, text=True, timeout=60)
    except Exception:
        return None
    commits, cur = [], None
    for ln in r.stdout.splitlines():
        if not ln.strip():
            continue
        head = ln.split("|", 2)
        if len(head) == 3 and head[0].strip().isdigit():
            cur = (int(head[0]), head[1], head[2], [])
            commits.append(cur)
        elif cur is not None:
            cur[3].append(ln.replace("\\", "/"))
    return [c for c in commits if c[3]]


def _t_layer_extra(root, files):
    """{rel: {authors, fix_coupling, stability}}；非 git → None。"""
    commits = _all_commits(root)
    if commits is None:
        return None
    now = int(time.time())
    fset = set(files)
    stat = {f: {"authors": set(), "total": 0, "recent": 0, "fix_c": 0}
            for f in files}
    for ts, author, subject, fs in commits:
        touched = [f for f in fs if f in fset]
        is_fix = bool(_FIX_RE.search(subject or ""))
        for f in touched:
            st = stat[f]
            st["authors"].add(author)
            st["total"] += 1
            if now - ts <= 90 * 86400:
                st["recent"] += 1
            if is_fix and len(fs) >= 2:
                st["fix_c"] += 1
    out = {}
    for f in files:
        st = stat[f]
        if st["total"] == 0:
            continue
        out[f] = {"authors": len(st["authors"]),
                  "fix_coupling": st["fix_c"],
                  "stability": round(1.0 - st["recent"] / st["total"], 4)}
    return out


@field_method("git")
def git_field(units, params, ctx):
    metric = params.get("metric", "commits")
    known = ("commits", "age_days", "authors", "fix_coupling", "stability")
    if metric not in known:
        raise ValueError("unknown git metric: %s" % metric)
    files = sorted({u["file"] for u in units})
    if metric in ("commits", "age_days"):
        ch = git_churn(ctx["root"], files)
        out = {}
        for i, u in enumerate(units):
            c = (ch or {}).get(u["file"])
            out[i] = None if c is None else c[metric]
        return out
    ex = _t_layer_extra(ctx["root"], files)
    out = {}
    for i, u in enumerate(units):
        c = (ex or {}).get(u["file"])
        out[i] = None if c is None else c[metric]
    return out
