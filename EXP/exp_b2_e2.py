# -*- coding: utf-8 -*-
"""
EXP/exp_b2_e2.py —— E-B2-2 执行正样本管线（L1）。
判据（PREREG/B2 v1.0）：①≥100 个函数级正样本 ②随机抽 5 patch 手工核对函数定位全对
③执行验证证据（上游 pass/fail 记录）可追溯。
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topos.calib.patch_extract import extract_bug  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "reference", "bugsinpy", "projects")
# 先跑小项目（快）；产出不足再扩
PROJECTS = ["PySnooper", "cookiecutter", "httpie", "tqdm", "sanic", "fastapi", "black"]
SEED = 20261009


def read_project_info(pdir):
    info = {}
    p = os.path.join(pdir, "project.info")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k] = v.strip('"')
    return info


def exec_evidence(pdir, bug_id):
    """上游执行记录：*-pass.txt / *-fail.txt 中含 'bugs/<id>' 的行数。"""
    name = os.path.basename(pdir)
    npass = nfail = 0
    for kind, acc in (("pass", "npass"), ("fail", "nfail")):
        f = os.path.join(pdir, "%s-%s.txt" % (name, kind))
        if not os.path.exists(f):
            continue
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "bugs/%s" % bug_id in line:
                    if kind == "pass":
                        npass += 1
                    else:
                        nfail += 1
    return npass, nfail


def main():
    cache = {}
    samples = []
    fails = []
    proj_stat = {}
    for proj in PROJECTS:
        pdir = os.path.join(ROOT, proj)
        if not os.path.isdir(pdir):
            continue
        info = read_project_info(pdir)
        gh = info.get("github_url", "")
        status = info.get("status", "?")
        bug_ids = sorted([d for d in os.listdir(os.path.join(pdir, "bugs"))
                          if d.isdigit()], key=int)
        n_ok = 0
        for bid in bug_ids:
            r = extract_bug(pdir, int(bid), gh, cache=cache)
            if r is None:
                continue
            for fn in r["functions"]:
                npass, nfail = exec_evidence(pdir, bid)
                fn["project"] = proj
                fn["bug_id"] = bid
                fn["upstream_pass"] = npass
                fn["upstream_fail"] = nfail
                fn["project_status"] = status
                samples.append(fn)
            if r["functions"]:
                n_ok += 1
            fails.extend([{"project": proj, "bug": bid, **x} for x in r["fetch_fail"]])
        proj_stat[proj] = {"bugs": len(bug_ids), "with_funcs": n_ok, "status": status}
    print("=== E-B2-2 执行正样本管线 ===")
    for p, s in proj_stat.items():
        print("  %-12s bug=%d 产出函数级样本=%d  (project status=%s)"
              % (p, s["bugs"], s["with_funcs"], s["status"]))
    uniq = {}
    for s in samples:
        uniq[s["unit_id"]] = s
    uniq = list(uniq.values())
    print("  函数级正样本（去重后）: %d" % len(uniq))
    print("  抓取失败: %d" % len(fails))
    if fails:
        print("    样例: %s" % fails[:2])
    ev_ok = sum(1 for s in uniq if s["upstream_fail"] > 0 or s["upstream_pass"] > 0)
    print("  含上游执行证据的样本: %d / %d" % (ev_ok, len(uniq)))
    rng = random.Random(SEED)
    picks = rng.sample(uniq, min(5, len(uniq)))
    print("=== 手工核对样本（5 个）===")
    for s in picks:
        print("  %s bugs/%s  file=%s func=%s lines=%d-%d  fail=%d pass=%d"
              % (s["project"], s["bug_id"], s["file"], s["name"],
                 s["lineno"], s["end_lineno"], s["upstream_fail"], s["upstream_pass"]))
    ok1 = len(uniq) >= 100
    ok3 = ev_ok > 0
    print("=" * 62)
    print("判据① ≥100 正样本: %s  ③ 执行证据可追溯: %s  （②手工核对见回执）"
          % (ok1, ok3))
    return 0 if (ok1 and ok3) else 1


if __name__ == "__main__":
    raise SystemExit(main())
