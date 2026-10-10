# -*- coding: utf-8 -*-
"""RUN1 后三步：decode → next → report-md → top12 读数（CLI 编程式调用）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from topos.cli import main as cli_main                                # noqa: E402

B = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "b")


def main():
    rc1 = cli_main(["decode",
                    os.path.join(B, "space.json"),
                    "--obs", os.path.join(B, "obs.json"),
                    "--decoder", "nb",
                    "--adj", os.path.join(B, "adj.json"),
                    "-o", os.path.join(B, "belief.json")])
    print("decode rc=%s" % rc1)
    rc2 = cli_main(["next",
                    os.path.join(B, "space.json"),
                    os.path.join(B, "belief.json"),
                    "--cost0", "0.05"])
    print("next rc=%s" % rc2)
    rc3 = cli_main(["report-md",
                    os.path.join(B, "space.json"),
                    "--belief", os.path.join(B, "belief.json"),
                    "-o", os.path.join(B, "report.md")])
    print("report-md rc=%s" % rc3)

    with open(os.path.join(B, "belief.json"), encoding="utf-8") as f:
        d = json.load(f)
    with open(os.path.join(B, "space.json"), encoding="utf-8") as f:
        units = json.load(f)["units"]
    items = sorted((d.get("belief") or {}).items(), key=lambda kv: -kv[1])
    print("=== belief top12 ===")
    for i, (u, p) in enumerate(items[:12], 1):
        uid = units[int(u)] if str(u).isdigit() else u
        print("%2d. %.4f  %s" % (i, p, uid))
    print("schema: %s  decoder: %s" % (d.get("schema"), d.get("decoder")))
    return 0 if (rc1 == 0 and rc2 == 0 and rc3 == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
