# -*- coding: utf-8 -*-
"""B7 §2 判据实测：D-B7-1 门必须能红 / D-B7-2 门必须能绿 / D-B7-3 反证格。

D-B7-3 的反证格是**最关键**的一条：把 coverage() 的 zero_cover_rate 改成恒 0
（假装全覆盖），若门仍输出 BLOCKED ⇒ 门没真接到覆盖率上，整批判作废。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
PY = sys.executable
ARCH = os.path.join(HERE, "run1_dsh", "c")


def run_next(sp, bel, extra=()):
    r = subprocess.run([PY, "-m", "topos.cli", "next", sp, bel] + list(extra),
                       cwd=REPO, capture_output=True, text=True, timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def verdict_of(out):
    for line in out.splitlines():
        if line.startswith("BLOCKED-COVERAGE"):
            return "BLOCKED-COVERAGE"
        if line.startswith("STOP"):
            return "STOP"
        if line.startswith("NEXT"):
            return "NEXT"
    return "?"


print("=" * 62)
print("D-B7-1 门必须能红：RUN1 归档件 c（zero_cover=0.904）")
rc, out = run_next(os.path.join(ARCH, "space.json"),
                   os.path.join(ARCH, "belief.json"))
v1 = verdict_of(out)
print("  rc=%d  verdict=%s" % (rc, v1))
print("  " + "\n  ".join(out.strip().splitlines()[:3]))
ok1 = (v1 == "BLOCKED-COVERAGE" and rc == 3)
print("  ⇒ %s" % ("✅ 咬合（门能红）" % () if ok1 else "❌ 不咬合"))

print("=" * 62)
print("D-B7-2 门必须能绿：构造全覆盖清单（宽池 loc>=0）重放")
import tempfile  # noqa: E402
from topos.space import Space  # noqa: E402

tmp = tempfile.mkdtemp(prefix="topos-b7-")
root = os.path.join(tmp, "t")
os.makedirs(root)
for k in range(12):
    with open(os.path.join(root, "m%d.py" % k), "w", encoding="utf-8") as f:
        f.write("def f%d():\n    return %d\n" % (k, k))
mf = {"version": 3, "layers": {"call": 1.0},
      "fields": [{"name": "loc", "method": "ast", "params": {"metric": "lines"}}],
      "slicers": [{"name": "all", "field": "loc", "op": "gt", "value": 0}],
      "pools": [{"name": "p_all", "expr": "all"}],
      "constraints": {"max_width": 400, "max_width_pct": 1.0,
                      "max_pools": 64, "min_pool_size": 3}}
mp = os.path.join(tmp, "mf.json")
with open(mp, "w", encoding="utf-8") as f:
    json.dump(mf, f)
sp = Space(root, manifest_path=mp)
sj = os.path.join(tmp, "space.json")
from topos.report import json_out  # noqa: E402
json_out.write(json_out.build_report(sp), sj)
bj = os.path.join(tmp, "belief.json")
from topos.infer.decode import decode_nb  # noqa: E402
bel = decode_nb([(nm, m) for nm, m in sp.rows], [(nm, 0) for nm, _ in sp.rows],
                sp.n, se=0.8, sp_=0.95)
with open(bj, "w", encoding="utf-8") as f:
    json.dump({"schema": "topos-belief/1", "n": sp.n,
               "belief": {str(i): v for i, v in bel.items()},
               "units": [u["id"] for u in sp.units]}, f)
rc2, out2 = run_next(sj, bj)
v2 = verdict_of(out2)
print("  zero_cover_rate=%.3f  rc=%d  verdict=%s"
      % (sp.coverage["zero_cover_rate"], rc2, v2))
ok2 = v2 in ("NEXT", "STOP") and rc2 != 3
print("  ⇒ %s" % ("✅ 咬合（门不是恒红）" if ok2 else "❌ 不咬合（门恒红）"))

print("=" * 62)
print("D-B7-3 反证格：把 zero_cover_rate 假冒为 0，D-B7-1 必须从 BLOCKED 变 NEXT/STOP")
# 直接改 space.json 的 coverage 字段（不改代码），模拟"假装全覆盖"
with open(os.path.join(ARCH, "space.json"), encoding="utf-8") as f:
    sj_arch = json.load(f)
fake = json.loads(json.dumps(sj_arch))
fake["coverage"]["zero_cover_rate"] = 0.0
fake["coverage"]["c_min"] = max(fake["coverage"].get("c_min", 1), 1)
fp = os.path.join(tmp, "fake_space.json")
with open(fp, "w", encoding="utf-8") as f:
    json.dump(fake, f)
rc3, out3 = run_next(fp, os.path.join(ARCH, "belief.json"))
v3 = verdict_of(out3)
print("  假冒 zcr=0 后 rc=%d  verdict=%s" % (rc3, v3))
ok3 = v3 in ("NEXT", "STOP") and v1 == "BLOCKED-COVERAGE"
print("  ⇒ %s" % ("✅ 咬合（门真接到覆盖率上）"
                  if ok3 else "❌ 判据作废，整批重做"))

print("=" * 62)
print("D-B7-1 %s ｜ D-B7-2 %s ｜ D-B7-3 %s"
      % ("PASS" if ok1 else "FAIL", "PASS" if ok2 else "FAIL",
         "PASS" if ok3 else "FAIL"))
