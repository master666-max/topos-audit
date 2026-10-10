# -*- coding: utf-8 -*-
"""sigma loop 全程推演：--opened 逐步加池，直接打印决策输出。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from topos.cli import main as cli_main                                # noqa: E402

B = os.path.join(HERE, "c")

opened = []
for step in range(6):
    args = ["next", os.path.join(B, "space.json"),
            os.path.join(B, "belief.json"), "--cost0", "0.05"]
    if opened:
        args += ["--opened", ",".join(opened)]
    print("======== step %d opened=%s" % (step + 1, opened or "[]"))
    rc = cli_main(args)
    print("   (rc=%s)" % rc)
    if rc != 0:
        print(">> rc!=0 —— 停止（STOP 语义：无值得开的池了）")
        break
    nxt = input if False else None
    # 按预先算好的 sigma 序开池：anchor -> deep_conf -> big1
    order = ["p_anchor_breadth", "p_deep_conf", "p_big1"]
    remaining = [p for p in order if p not in opened]
    if not remaining:
        print(">> 全部池已开，循环结束")
        break
    opened.append(remaining[0])
print(">> 终态 opened =", opened)
