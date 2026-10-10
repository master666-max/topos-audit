# -*- coding: utf-8 -*-
"""一次性行手术：把 c30/c31 定义块移到 CHECKS 列表之前。"""
p = r"D:\WorkBuddy专用！危险！！！！！！！！\2026-10-09-02-32-12\topos-audit\topos\selftest.py"
with open(p, encoding="utf-8") as f:
    lines = f.read().splitlines()

assert lines[685].startswith("CHECKS = ["), lines[685]
assert lines[717] == "]", lines[717]
assert lines[720].startswith("def c30_owner_attribution"), lines[720]
assert lines[790].startswith("def run_all"), lines[790]

defs = lines[720:790]            # c30/c31 定义块（含尾随空行）
head = lines[:685]               # 到 CHECKS = [ 之前
entries = lines[685:718]         # CHECKS = [ ... ]（含 c30/c31 引用行）
tail = lines[790:]               # run_all 起到文件尾

new = head + defs + ["", ""] + entries + tail
with open(p, "w", encoding="utf-8") as f:
    f.write("\n".join(new) + "\n")
print("surgery done, total lines:", len(new))
