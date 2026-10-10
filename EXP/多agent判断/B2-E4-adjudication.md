# B2-E4-adjudication.md —— 覆盖事故墓碑与内容去向（judgeC 留）

> **本文件原为 judgeA 的 L4-control 回执**（NTFS `CreationTime` = 2026-10-10 02:12:58，
> 原大小 **6116 字节**），于 **2026-10-10 08:52:37** 被 judgeC 的派生脚本
> `make_b2_e4_adjudication.py` 就地截断覆盖。judgeA 的原件**不可逐字恢复**
> （judgeC 未保存副本；该文件在 git 中未被跟踪，`??` 状态）。
> **judgeC 在此不伪造 judgeA 的回执**——只把数据去向写清楚。

## judgeA 的数据在哪

| 内容 | 位置 | 状态 |
|---|---|---|
| judgeA 的完整判定（100 行） | `EXP/B2-E4-adjudication.csv` | **未被触碰**（33927 字节，02:15:33；列 = seq, unit_id, file, name, lineno, stratum, truth, defect_type, rule, note, annotator, date） |
| 逐单元 jsonl（**同源重建**） | `EXP/B2-E4-adjudication.jsonl` | 由 judgeC 从上一行 CSV 重建；每条带 `reconstructed_from` / `reconstructed_by` / `original_overwritten` |
| 机器表填版（**同源重建**） | `EXP/B2-E4-sample.csv` | 原始 16 列 schema；`truth`/`defect_type`/`annotator`/`date` 取自 judgeA 的 CSV |
| judgeA 的 `rule` 与 `note` | 同 `B2-E4-adjudication.csv` | 原表（sample）本无 note 列，故不写入 sample |

**重建 ≠ 原件**：上面两件是「内容同源、字节非原件」。judgeA 原 `.jsonl`（48704 字节）与
原 `.md`（6116 字节）的**逐字内容已不可得**；如 judgeA 另有备份，请以备份覆盖本目录同名文件。

judgeA 分布（据其 CSV，由 judgeC 统计）：`1` = 2，`0` = 88，`None` = 10；
annotator = `L4-control:Otto(single-rater,no-kappa)`；date = `2026-10-10`。

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
