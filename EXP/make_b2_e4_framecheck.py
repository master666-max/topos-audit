# -*- coding: utf-8 -*-
"""
EXP/make_b2_e4_framecheck.py —— 抽样框构成核查（E-B2-4 附带读数）

起因：`make_b2_e4_sample.py:23` 的扫描根是 Python 3.13.12 安装件的 `Lib`，
其中**包含 `Lib/site-packages`**（pip 自身 + pip vendored 的第三方库）；
而 `:156` 写死的工作簿标题宣称「靶仓：Python 标准库」。本脚本现量真实构成，
判断分层配额与「零覆盖 97.8%」这两个读数是标准库读数还是混合读数。

产出：EXP/B2-E4-framecheck.json（机器可读）+ stdout（人读）
不改抽样、不改清单、不覆盖任何既有产物。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topos.space import Space  # noqa: E402

TARGET = r"C:\Users\26672\.workbuddy\binaries\python\versions\3.13.12\Lib"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "B2-E4-framecheck.json")


def is_sp(u):
    return u["file"].replace("\\", "/").startswith("site-packages/")


def main():
    sp = Space(TARGET)
    n = sp.n
    units = sp.units

    covered = set()
    for _name, members in sp.rows:
        covered.update(members)

    anchor_field = sp.fields.get("anchor", {})
    curv = sp.fields.get("forman", {})
    cv = sorted(v for v in curv.values() if v is not None)
    thr = cv[len(cv) // 3] if cv else None

    groups = {"site-packages": [], "stdlib": []}
    for i, u in enumerate(units):
        groups["site-packages" if is_sp(u) else "stdlib"].append(i)

    out = {"target": TARGET, "n_total": n, "forman_threshold": thr,
           "pools": len(sp.rows), "by_source": {}}

    for gname, idxs in groups.items():
        s = set(idxs)
        zero = [i for i in idxs if i not in covered]
        anch = [i for i in idxs if anchor_field.get(i)]
        conf = [i for i in idxs
                if curv.get(i) is not None and thr is not None and curv[i] <= thr]
        out["by_source"][gname] = {
            "units": len(idxs),
            "share_of_frame_pct": round(100.0 * len(idxs) / max(n, 1), 2),
            "zero_cover": len(zero),
            "zero_cover_pct_within_group": round(100.0 * len(zero) / max(len(idxs), 1), 2),
            "anchor_hit": len(anch),
            "confluence": len(conf),
        }

    allzero = [i for i in range(n) if i not in covered]
    out["zero_cover_all"] = len(allzero)
    out["zero_cover_all_pct"] = round(100.0 * len(allzero) / max(n, 1), 2)

    # 第三方 vendored 库细分（site-packages 内部再分：pip 自身 vs pip/_vendor）
    vend = {}
    for i in groups["site-packages"]:
        parts = units[i]["file"].replace("\\", "/").split("/")
        key = "/".join(parts[:3]) if len(parts) >= 3 else "/".join(parts[:2])
        vend[key] = vend.get(key, 0) + 1
    out["site_packages_top_dirs"] = dict(
        sorted(vend.items(), key=lambda kv: -kv[1])[:25])

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
