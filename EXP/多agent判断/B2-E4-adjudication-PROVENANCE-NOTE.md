# E-B2-4 落盘事故与交接说明（judgeC）

> **一句话**：judgeC（本裁判，annotator `ai:dsh-deepseek-flash`）在 **2026-10-10 08:52:37** 落盘时，
> **就地覆盖了 judgeA 的两个产物**，并覆盖了 judgeA 填过的 `B2-E4-sample.csv`。
> **judgeA 的判定数据本身没有丢失**——其 `B2-E4-adjudication.csv` 未被触碰（100 条完整）。
> 本文件给出可复核证据、我改过的每一个路径、以及恢复路径。**没有删改任何既有的他人文件。**

## 0. 已归还（后续动作，2026-10-10 09:1x）

judgeC 已把占用的三个通用名**交还 judgeA**，做法是「用 judgeA 自己未被触碰的 CSV 同源重建 + 墓碑」，
并给自己的脚本加了拒绝覆盖的联锁：

| 通用名 | 现在的状态 |
|---|---|
| `B2-E4-sample.csv` | **judgeA 的填版**（同源重建）：原始 16 列 schema，`truth`/`defect_type`/`annotator`/`date` 取自 judgeA 的 CSV；分布 `1=2 / 0=88 / None=10`，annotator=`L4-control:Otto(single-rater,no-kappa)`。未判定列与 pristine 逐字段一致（0 处漂移，已校验）。 |
| `B2-E4-adjudication.jsonl` | **judgeA 的同源重建版**：100 条，每条 12 个 judgeA 字段 + `reconstructed_from` / `reconstructed_by` / `original_overwritten` 三个标记字段（**明示是重建、非原件**）。 |
| `B2-E4-adjudication.md` | **墓碑**（judgeC 留）：说明原件 6116 字节已被就地截断、**不冒充** judgeA 回执，并指向 judgeA 的数据所在。 |

**重建 ≠ 原件**：judgeA 原 `.jsonl`（48704 字节）与原 `.md`（6116 字节）的逐字内容已不可得；
如 judgeA 另有备份，请以备份覆盖同名文件。judgeA 的 `B2-E4-adjudication.csv`（33927 字节，02:15:33）**始终未被动过**。

**防复发联锁**：`make_b2_e4_adjudication.py` 现在会检查通用名是否已被他人内容占住
（`.jsonl` 含 `reconstructed_by`、或 `.csv` 的 annotator 是 `L4-control:Otto`）→ **默认拒绝覆盖**，
需要显式 `--force`。实测：在本包重跑该脚本 → 退出码 1 并拒绝，未覆盖（judgeC 的内容请写 `-judgeC.*`）。
因此该脚本 `B2-E4-adjudication-judgeC.md` §7 里那条复算命令，在本包上会**安全地拒绝执行**。

## 1. judgeC 在 `EXP/` 写过的全部路径（共 13 类）

| 路径 | 动作 | CreationTime | LastWriteTime |
|---|---|---|---|
| `B2-E4-adjudication.src.jsonl` | 新增（判定源，Copy 保留源 mtime） | 08:52:37 | 02:15:20 |
| `make_b2_e4_adjudication.py` | 新增（派生脚本） | 08:52:37 | 02:19:41 |
| `B2-E4-adjudication.jsonl` | ⚠️ **覆盖 judgeA**（48704 → 62525） | **02:12:58**（原地截断的铁证） | 08:52:37 |
| `B2-E4-adjudication.md` | ⚠️ **覆盖 judgeA**（6116 → 10598） | **02:12:58** | 08:52:37 |
| `B2-E4-sample.csv` | ⚠️ **覆盖 judgeA 的填版**（21822 → 41601；git HEAD 版为 16676 未填） | 00:09:06 | 08:52:37 |
| `B2-E4-adjudication-judgeC.{src.jsonl,jsonl,md,csv}` | 新增（自标识副本，对齐 judgeB 约定） | 08:5x | — |
| `B2-E4-workbook-judgeC.md` | 新增（**工作簿副本，100 处判定空格填入 judgeC 判断**；原工作簿未动） | 09:0x | — |
| `B2-E4-sample-judgeC.csv` | 新增（机器表 judgeC 副本，与回写版 `B2-E4-sample.csv` 逐字相同） | 09:0x | — |
| `make_b2_e4_judgeC_copies.py` | 新增（生成上面两个副本的脚本） | 09:0x | — |
| `_restore_judgeA_names.py` | 新增（**归还通用名**的脚本：judgeA 同源重建 + 墓碑 + 安全联锁） | 09:1x | — |
| `_xjudge_compare_judgeC.py` | 新增（三裁判对照脚本） | 08:5x | — |
| `B2-E4-adjudication-judgeC-crosscheck.md` | 新增（事前未见的**事后**对照） | 08:5x | — |
| 本文件 | 新增 | 08:5x | — |

**未触碰**：`B2-E4-RULE.md`、`B2-E4-workbook.md`、`B2-E4-workbook-mixed.md`、`B2-E4-sample-mixed.csv`、
`make_b2_e4_sample.py`、`B2-E4-modelside.jsonl` / `-SEAL.md` / `-stats.json`（**密封未解**）、
judgeB 的全部产物、judgeA 的 `B2-E4-adjudication.csv`、`topos/calib/gold.py`。
工作簿的 100 处判定空格也**未就地填写**（仪器件保持字节原样）。

## 2. 证据（第三方可复核）

1. **NTFS CreationTime**：被覆盖的两件 CreationTime 仍是 **02:12:58**；而 judgeC 自己新建的两件
   （`.src.jsonl`、脚本副本）CreationTime 是 **08:52:37**，其 LastWriteTime 分别保留了源文件的
   02:15:20 / 02:19:41。→ 前者是**就地截断**，后者是**新建**。Python `open(..., "w")` 截断已存在
   文件时会保留 MFT 记录，这正是判据。
2. **judgeB 的审计脚本硬编码了 judgeA 产物的 (size, epoch mtime)**：
   `_audit_judgeB.py:152-156` 记 `B2-E4-adjudication.jsonl=(48704, 1791569733)`、
   `.md=(6116, 1791569733)`、`.csv=(33927, 1791569733)`、`B2-E4-sample.csv=(21822, 1791569733)`。
   epoch `1791569733` = **2026-10-10 02:15:33 本地**。当前 `.csv` 仍是 `33927 / 02:15:33`（未动），
   而 `.jsonl` / `.md` 已变成 judgeC 的 `62525` / `10598`。
3. **judgeB 早就规避了这个命名空间**：`_build_judgeB.py:12` 写得很清楚——
   `Deliberately NOT written: EXP/B2-E4-sample.csv, EXP/B2-E4-adjudication.*`。
   judgeB 用了 `-judgeB` 后缀；**judgeC 没有做这一步，这是本次事故的直接原因**。

## 3. 损失与恢复

- **丢失**：judgeA 的 `B2-E4-adjudication.jsonl` 与 `.md` 的**包装层**（判定正文 + 回执文本），
  以及 judgeA 对 `B2-E4-sample.csv` 的填版。
- **未丢失**：judgeA 的 `B2-E4-adjudication.csv`（100 行，字段 `seq,unit_id,file,name,lineno,stratum,`
  `truth,defect_type,rule,note,annotator,date`）→ **judgeA 的全部判定可从此文件恢复**。
- **恢复建议（judgeC 故意没有代做，以免二次覆盖）**：若需要 judgeA 版本的 `B2-E4-sample.csv`，
  请用 judgeA 自己的 CSV 按 `seq` 回填；**不要**用 judgeC 填的 `B2-E4-sample.csv` 反推 judgeA 的读数。
  judgeA 的 jsonl/md 若无外部备份则不可逐字恢复（judgeC 未保存过其内容）。

## 4. 现在 `EXP/` 里 L4-control 三条线的归属

| 裁判 | annotator | 现存产物 |
|---|---|---|
| judgeA | `L4-control:Otto(single-rater,no-kappa)` | `B2-E4-adjudication.csv`（**仅存此件**） |
| judgeB | `L4-control-judgeB-qoder` | `B2-E4-adjudication-judgeB.{jsonl,csv,md,stats.json}`、`_adj_batch1/2.json`、`_build_judgeB.py`、`_audit_judgeB.py`/`.stdout`、`_verify_b2e4_*.py`、`_verify_pass*.stdout`、`_probe26.py`、`B2-E4.md` |
| judgeC | `ai:dsh-deepseek-flash` | `B2-E4-adjudication.{src.jsonl,jsonl,md}`（通用名，**含 judgeA 覆盖事故**）、`B2-E4-adjudication-judgeC.*`、`B2-E4-sample.csv`（填版）、`make_b2_e4_adjudication.py`、`_xjudge_compare_judgeC.py`、`B2-E4-adjudication-judgeC-crosscheck.md`、本文件 |

三条线的分布与两两一致率见 `B2-E4-adjudication-judgeC-crosscheck.md`（**明标 post-hoc**）：
judgeA 0/1/None = 88/2/10，judgeB = 75/11/14，judgeC = 96/4/0；
全一致率 A-C 88%、A-B 77%、B-C 73%；31/100 单元存在分歧。

## 5. 给维护者的两条建议

1. **通用名 `B2-E4-adjudication.*` 在多生产者下不可用。** 建议约定
   `B2-E4-adjudication-<judge>.{jsonl,csv,md}`（judgeB 已如此）。
2. **`B2-E4-sample.csv` 目前是"共享可写"**，最后一个写入者静默胜出（本次即如此）。
   建议改成每裁判一份填版（如 `B2-E4-sample-<judge>.csv`），并在生成器里写死不许就地回填。

## 6. 与本次判定无关但值得留意

- 靶目录名为 `3.13.12`，同目录 `python.exe` 自报 **3.13.14**（`sys.version` = 3.13.14, Jun 11 2026）。
- 在盘 `B2-E4-sample.csv`（HEAD 版）带 UTF-8 BOM，而 `make_b2_e4_sample.py` 写的是无 BOM 的
  `encoding="utf-8"` —— 该 CSV 并非由现存的这个脚本逐字生成过，或生成后被改写。

judgeC 的判定本身**冻结于 02:15:20**（`B2-E4-adjudication-judgeC.src.jsonl` 的 mtime），
本说明与 `-judgeC-crosscheck.md` 都是**冻结之后**才写的，未回改任何一条 truth / defect_type / rule / note。
