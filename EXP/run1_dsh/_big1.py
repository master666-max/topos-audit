# -*- coding: utf-8 -*-
"""p_big1 三个最大函数速览（span/调用点/结构概要）。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(REPO, "tools", "repos", "dsh-launcher")

with open(os.path.join(HERE, "c", "space.json"), encoding="utf-8") as f:
    d = json.load(f)
units = d["units"]
big = [u for nm, m in d["pool_members"] if nm == "p_big1"
       for u in [units[int(i)]] for i in [int(i)]] if False else None
for nm, members in d["pool_members"]:
    if nm != "p_big1":
        continue
    for m in members:
        uid = units[int(m)]
        prefix, ln0 = uid.rsplit(":", 1)
        fname = prefix.split("::")[0]
        lines = open(os.path.join(SRC, fname), encoding="utf-8",
                     errors="replace").read().splitlines()
        start = int(ln0)
        # 从单元列表找回 end：空间里没有 end，就扫到下一个同级 def 或文件尾
        end = len(lines)
        depth0 = len(lines[start - 1]) - len(lines[start - 1].lstrip())
        for j in range(start, len(lines)):
            s = lines[j]
            if j + 1 > start and s.strip() and not s.startswith(" " * (depth0 + 1)) \
                    and (s.strip().startswith("def ") or s.strip().startswith("class ")):
                end = j
                break
        body = lines[start - 1:end]
        n = len(body)
        calls = sum(1 for x in body if "(" in x)
        branches = sum(1 for x in body if x.strip().startswith(("if ", "elif ", "try", "except", "for ", "while ")))
        print("== %s  span≈%d 行  调用行≈%d  分支≈%d" % (uid, n, calls, branches))
        for x in body[:12]:
            print("   |", x[:88])
        if n > 12:
            print("   | …(共 %d 行)" % n)
