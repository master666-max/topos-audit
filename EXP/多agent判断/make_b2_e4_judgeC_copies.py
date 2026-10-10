# -*- coding: utf-8 -*-
"""EXP/make_b2_e4_judgeC_copies.py —— judgeC 专属副本：把「我的判断」写进我自己名字下的副本。

产出（全部**新增**，不覆盖任何既有文件；共享名 B2-E4-* 一律只读）：
  EXP/B2-E4-workbook-judgeC.md   ← B2-E4-workbook.md 的副本，100 处判定空格填入 judgeC 判定
  EXP/B2-E4-sample-judgeC.csv    ← B2-E4-sample.csv（回写版）的副本，同 16 列 + note

输入（只读）：
  EXP/B2-E4-workbook.md               仪器件，**不改**
  EXP/B2-E4-adjudication.src.jsonl    judgeC 判定源（冻结于 2026-10-10 02:15:20）
  EXP/B2-E4-sample.csv                judgeC 的回写版机器表

纪律：只新增；不删改他人文件；不动 RULE.md / workbook / mixed / 生成器 / gold.py。
"""
import csv
import json
import os
import re
import sys

SECTION = re.compile(r"^## #(\d+) · ")
BLANK = "**判定**：truth = `___`"
ANNOTATOR = "ai:dsh-deepseek-flash"
FROZEN_AT = "2026-10-10 02:15:20"


def main():
    if len(sys.argv) < 2:
        print("用法: make_b2_e4_judgeC_copies.py <repo_root>")
        return 2
    exp = os.path.join(os.path.abspath(sys.argv[1]), "EXP")

    judge = {}
    with open(os.path.join(exp, "B2-E4-adjudication.src.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                o = json.loads(line)
                judge[int(o["seq"])] = o
    if len(judge) != 100:
        raise SystemExit("判定源不是 100 条")

    # ---------- ① 工作簿副本：填 100 处判定空格 ----------
    wb_in = os.path.join(exp, "B2-E4-workbook.md")
    wb_out = os.path.join(exp, "B2-E4-workbook-judgeC.md")
    with open(wb_in, encoding="utf-8") as f:
        lines = f.read().splitlines()

    banner = [
        "",
        "> ⚠️ **本文件是 `B2-E4-workbook.md` 的 judgeC 专属副本**（原仪器件**未被改动**）。",
        "> 100 处 `truth = ___ ｜ defect_type = ___ ｜ 备注 = ___` 空格已按 judgeC 的 **L4-control** 判定填入，",
        "> 并在行尾补 `rule` / `confidence` 两个可回溯字段（`RULE.md` 纪律#5 要求每条判定带规则码）。",
        "> **判定人**：`%s`（机器，非人工金标）｜ **冻结时刻**：%s ｜ **来源树**：目录标签 3.13.12（解释器自报 3.13.14）" % (ANNOTATOR, FROZEN_AT),
        "> **真源**：`EXP/B2-E4-adjudication.src.jsonl`（判定源）／自足版 `EXP/B2-E4-adjudication-judgeC.jsonl`",
        "> **口径**：见 `EXP/B2-E4-adjudication-judgeC.md` §3（P1–P6）；None 率 0% 的成因见其 §2。",
        "> **本副本是「读数」，不是金标**；不得写入 `topos/calib/gold.py`。",
        "",
    ]

    out, filled, cur, seen = [], 0, None, set()
    for line in lines:
        m = SECTION.match(line)
        if m:
            cur = int(m.group(1))
            seen.add(cur)
        if line.startswith(BLANK):
            j = judge[cur]
            dt = j.get("defect_type") or "—"
            out.append(
                "**判定**：truth = `%s`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**）"
                " ｜ defect_type = `%s` ｜ 备注 = %s ｜ rule = `%s` ｜ confidence = `%s`"
                % (j["truth"], dt, j["note"], j["rule"], j.get("confidence", ""))
            )
            filled += 1
            continue
        out.append(line)

    if filled != 100:
        raise SystemExit("填入空格数 = %d，期望 100 —— 中止（不写盘）" % filled)
    if len(seen) != 100:
        raise SystemExit("识别到的小节数 = %d，期望 100 —— 中止（不写盘）" % len(seen))
    if len(out) != len(lines):
        raise SystemExit("行数变了（%d -> %d）—— 中止（不写盘）" % (len(lines), len(out)))

    # 在第 1 行标题后插入横幅
    final = [out[0]] + banner + out[1:]
    with open(wb_out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(final) + "\n")

    # ---------- ② 机器表副本 ----------
    csv_in = os.path.join(exp, "B2-E4-sample.csv")
    csv_out = os.path.join(exp, "B2-E4-sample-judgeC.csv")
    with open(csv_in, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        cols = list(rd.fieldnames)
        rows = list(rd)
    with open(csv_out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print("工作簿副本 -> %s（填入 %d 处判定；原 %d 行 -> 新 %d 行）"
          % (wb_out, filled, len(lines), len(final)))
    print("机器表副本 -> %s（%d 列 / %d 行数据）" % (csv_out, len(cols), len(rows)))
    ones = [j["seq"] for j in judge.values() if j["truth"] == "1"]
    print("副本内分布: 1=%d 0=%d None=%d ｜ 1 的单元: %s"
          % (len(ones),
             sum(1 for j in judge.values() if j["truth"] == "0"),
             sum(1 for j in judge.values() if j["truth"] == "None"),
             ones))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
