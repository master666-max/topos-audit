# -*- coding: utf-8 -*-
"""EXP/_restore_judgeA_names.py —— 把 judgeC 占用的通用名交还 judgeA。

做三件（其中两件是**重建**，逐条带 provenance 标记；一件是**墓碑**，不伪造他人回执）：

  ① EXP/B2-E4-sample.csv          ← 原始 16 列 schema；truth/defect_type/annotator/date
                                     取自 judgeA 尚未被触碰的 B2-E4-adjudication.csv
  ② EXP/B2-E4-adjudication.jsonl  ← 100 条逐单元记录（同源重建），每条带
                                     reconstructed_from / reconstructed_by / original_overwritten
  ③ EXP/B2-E4-adjudication.md     ← 覆盖事故墓碑 + 数据去向（**不**冒充 judgeA 的回执）

安全联锁（不满足即中止、不写盘）：
  - 必须先确认 judgeC 自己的副本已存在且与将被覆盖的三件**逐字相同**（SHA256），
    否则 judgeC 的内容会丢。
  - judgeA 的 B2-E4-adjudication.csv 必须存在且为 100 行。

明确不做：不改 RULE.md / workbook / mixed / 生成器 / gold.py / judgeB 任何文件 / judgeA 的 CSV。
"""
import csv
import hashlib
import json
import os
import sys

TOUCHED = ("B2-E4-sample.csv", "B2-E4-adjudication.jsonl", "B2-E4-adjudication.md")
BACKUP = {
    "B2-E4-sample.csv": "B2-E4-sample-judgeC.csv",
    "B2-E4-adjudication.jsonl": "B2-E4-adjudication-judgeC.jsonl",
    "B2-E4-adjudication.md": "B2-E4-adjudication-judgeC.md",
}
JUDGED = ("truth", "defect_type", "annotator", "date")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        print("用法: _restore_judgeA_names.py <repo_root>")
        return 2
    exp = os.path.join(os.path.abspath(sys.argv[1]), "EXP")

    # ---------- 安全联锁：judgeC 副本必须完整且相同 ----------
    for t in TOUCHED:
        tp, bp = os.path.join(exp, t), os.path.join(exp, BACKUP[t])
        if not os.path.exists(tp) or not os.path.exists(bp):
            raise SystemExit("缺少 %s 或 %s —— 中止（不写盘）" % (t, BACKUP[t]))
        if sha(tp) != sha(bp):
            raise SystemExit("%s 与 %s 不一致 —— 中止（不写盘）" % (t, BACKUP[t]))
    print("[联锁] judgeC 三件副本齐备且逐字相同 ✓")

    ja_csv = os.path.join(exp, "B2-E4-adjudication.csv")
    with open(ja_csv, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        ja = list(rd)
        ja_cols = list(rd.fieldnames)
    if len(ja) != 100:
        raise SystemExit("judgeA 的 CSV 不是 100 行 —— 中止（不写盘）")
    ja_by = {int(r["seq"]): r for r in ja}
    print("[输入] judgeA CSV: %d 行，列 = %s" % (len(ja), ja_cols))

    # ---------- ① 还原 B2-E4-sample.csv（原始 16 列 schema） ----------
    sample = os.path.join(exp, "B2-E4-sample.csv")
    with open(sample, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        s_cols = [c for c in rd.fieldnames if c != "note"]     # 去掉 judgeC 追加的 note 列
        s_rows = list(rd)
    if len(s_cols) != 16:
        raise SystemExit("原始列数不是 16（得到 %d）—— 中止" % len(s_cols))
    for r in s_rows:
        j = ja_by[int(r["seq"])]
        for k in JUDGED:
            r[k] = j[k]

    # ---------- ② 重建 B2-E4-adjudication.jsonl（先算，不写） ----------
    lines = []
    for r in s_rows:
        j = ja_by[int(r["seq"])]
        rec = {k: j.get(k, "") for k in ja_cols}
        rec["reconstructed_from"] = "EXP/B2-E4-adjudication.csv"
        rec["reconstructed_by"] = "judgeC(ai:deepseek-v4.1-flash)"
        rec["original_overwritten"] = True
        lines.append(json.dumps(rec, ensure_ascii=False))

    # ---------- ③ 墓碑（先算，不写） ----------
    import collections
    dd = collections.Counter(("None" if (j["truth"] in ("", "None")) else j["truth"]) for j in ja)
    md = """# B2-E4-adjudication.md —— 覆盖事故墓碑与内容去向（judgeC 留）

> **本文件原为 judgeA 的 L4-control 回执**（NTFS `CreationTime` = 2026-10-10 02:12:58，
> 原大小 **6116 字节**），于 **2026-10-10 08:52:37** 被 judgeC 的派生脚本
> `make_b2_e4_adjudication.py` 就地截断覆盖。judgeA 的原件**不可逐字恢复**
> （judgeC 未保存副本；该文件在 git 中未被跟踪，`??` 状态）。
> **judgeC 在此不伪造 judgeA 的回执**——只把数据去向写清楚。

## judgeA 的数据在哪

| 内容 | 位置 | 状态 |
|---|---|---|
| judgeA 的完整判定（100 行） | `EXP/B2-E4-adjudication.csv` | **未被触碰**（33927 字节，02:15:33；列 = %s） |
| 逐单元 jsonl（**同源重建**） | `EXP/B2-E4-adjudication.jsonl` | 由 judgeC 从上一行 CSV 重建；每条带 `reconstructed_from` / `reconstructed_by` / `original_overwritten` |
| 机器表填版（**同源重建**） | `EXP/B2-E4-sample.csv` | 原始 16 列 schema；`truth`/`defect_type`/`annotator`/`date` 取自 judgeA 的 CSV |
| judgeA 的 `rule` 与 `note` | 同 `B2-E4-adjudication.csv` | 原表（sample）本无 note 列，故不写入 sample |

**重建 ≠ 原件**：上面两件是「内容同源、字节非原件」。judgeA 原 `.jsonl`（48704 字节）与
原 `.md`（6116 字节）的**逐字内容已不可得**；如 judgeA 另有备份，请以备份覆盖本目录同名文件。

judgeA 分布（据其 CSV，由 judgeC 统计）：`1` = %d，`0` = %d，`None` = %d；
annotator = `%s`；date = `%s`。

## 事故证据（第三方可复核）

1. **NTFS CreationTime**：本文件与 `B2-E4-adjudication.jsonl` 的 CreationTime 至今仍是
   **02:12:58**（就地截断保留 MFT 记录），而 judgeC 自己新建的 `B2-E4-adjudication.src.jsonl`
   与脚本副本 CreationTime 为 **08:52:37**（新建）。
2. **judgeB 的审计脚本硬编码了 judgeA 产物的 (size, epoch)**：`_audit_judgeB.py:152-156` 记
   `B2-E4-adjudication.jsonl=(48704, 1791569733)`、`.md=(6116, 1791569733)`、
   `.csv=(33927, 1791569733)`、`B2-E4-sample.csv=(21822, 1791569733)`；
   epoch `1791569733` = 2026-10-10 02:15:33 本地。
3. **judgeB 明确规避过这个命名空间**：`_build_judgeB.py:12` —
   `Deliberately NOT written: EXP/B2-E4-sample.csv, EXP/B2-E4-adjudication.*`。
   judgeB 用了 `-judgeB` 后缀；**judgeC 没做这一步，这是事故的直接原因**。

## judgeC 自己的产物（另有名字，与本文件无关）

`B2-E4-adjudication-judgeC.{src.jsonl,jsonl,md,csv}`、`B2-E4-sample-judgeC.csv`、
`B2-E4-workbook-judgeC.md`（工作簿副本，100 处判定空格已填）、
`B2-E4-adjudication-judgeC-crosscheck.md`（三裁判事后对照）、
`B2-E4-adjudication-PROVENANCE-NOTE.md`（交接说明）。
""" % (", ".join(ja_cols), dd.get("1", 0), dd.get("0", 0), dd.get("None", 0),
       ja[0].get("annotator", ""), ja[0].get("date", ""))

    # ---------- 三件全部算好后，一次性落盘（避免半成品状态） ----------
    with open(sample, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=s_cols)
        w.writeheader()
        w.writerows({k: r[k] for k in s_cols} for r in s_rows)
    with open(os.path.join(exp, "B2-E4-adjudication.jsonl"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(exp, "B2-E4-adjudication.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)

    print("[①] B2-E4-sample.csv         <- judgeA 填版（原始 16 列，%d 行）" % len(s_rows))
    print("[②] B2-E4-adjudication.jsonl <- judgeA 同源重建（100 条，带 provenance 字段）")
    print("[③] B2-E4-adjudication.md    <- 墓碑（不冒充 judgeA 回执）")
    print("judgeA 分布: 1=%d 0=%d None=%d" % (dd.get("1", 0), dd.get("0", 0), dd.get("None", 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
