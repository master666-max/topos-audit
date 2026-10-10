# E-B2-4 L4-control 裁定报告（对照尺，非真值）· **judgeA / hy4-preview**

> **裁判标识**：`judge_id=judgeA` ｜ `judge_model=hy4-preview` ｜ 宿主：WorkBuddy（Otto）
> **annotator**：`L4-control:Otto(single-rater,no-kappa)`（02:15 冻结原值，jsonl 中同步保留在 `annotator_original` 字段，交叉引用不断）
> 单裁判，无独立复标｜日期：2026-10-10｜规则出处：`EXP/B2-E4-RULE.md`
> 定性：**机器对照层（L4-control）**。本产物是**对照尺**，不是金标，不写入 `topos/calib/gold.py`。
> ⚠️ **本文件为同源重建版**：原件（6116 字节，NTFS CreationTime 02:12:58）毁于 2026-10-10 08:52:37 的
> judgeC 覆盖事故，逐字内容不可得。本版由 judgeA 未被触碰的 `B2-E4-adjudication.csv`（33927 字节 / 02:15:33）
> 同源重建，判定数据 100 条与 CSV 逐字段一致；分布/机理/自纠各节按 CSV 重新汇总。
> 事故链与第三方可复核证据：`多agent判断/B2-E4-adjudication-PROVENANCE-NOTE.md`；墓碑留档：
> `多agent判断/B2-E4-adjudication-覆盖事故墓碑.md`。
> ⚠️ **命名**：三裁判对照包（`EXP/多agent判断/`）内的本线副本带 `-judgeA-hy4-preview` 后缀；
> 本文件占用的是 judgeA 被覆盖前的**原通用名路径** `EXP/B2-E4-adjudication.md`（2026-10-10 归还恢复）。

## 1. 总体分布

| truth | 计数 | 占比 |
|---|---|---|
| 1 | 2 | 2% |
| 0 | 88 | 88% |
| None | 10 | 10% |
| 合计 | 100 | 100% |

- 1 率（全样本为分母）= 0.02，Wilson 95% CI = [0.006, 0.070]，半宽 ±0.032
- 1 率（剔除 None，n=90）= 0.022，Wilson 95% CI = [0.006, 0.077] ⚠️ 剔 None 会选择性剔除难判样本，仅作对照（PREREG B2 v1.5·B2）
- None 率 = 10%（< 40% 阈值，未触发"可判性不足"标记）

## 2. 分层分布

| 层 | n | 1 | 0 | None | None 率 | 1 率(Wilson CI, n=全层) |
|---|---|---|---|---|---|---|
| `random` | 30 | 1 | 25 | 4 | 13% | 0.03 [0.01, 0.17] |
| `confluence` | 20 | 0 | 19 | 1 | 5% | 0.00 [0.00, 0.16] |
| `anchor` | 25 | 1 | 21 | 3 | 12% | 0.04 [0.01, 0.20] |
| `zero_cover` | 25 | 0 | 23 | 2 | 8% | 0.00 [0.00, 0.13] |

层内 n=20~30，CI 半宽可达 ±0.20（PREREG v1.5 诚实宽度表），层内读数仅作辅助判读，不作单点作废依据。

## 3. 判为 1 的单元（逐条机理，均附证据）

### #4 · `compile_file`（compileall.py:132，层=random）
- defect_type：`boundary`
- 机理：compileall.py:245 `for index, opt_level in enumerate(optimize)` 在 optimize=[] 时零次执行，L277 `if ok == 0` 引用未绑定的 ok → UnboundLocalError。触发条件：force=True 且 optimize=[]（非 force 路径被 L238 for/else 的 return success 掩盖）。【实测】compile_file(p, quiet=2, force=True, optimize=[]) → UnboundLocalError: cannot access local variable 'ok'；对照 force=True + optimize=[0] / -1 与 force=False + optimize=[] 均正常返回 True。

### #72 · `CGIHTTPRequestHandler.run_cgi`（http/server.py:1074，层=anchor）
- defect_type：`logic`
- 机理：http/server.py:1183 已算 decoded_query = query.replace("+"," ")，fork 分支 L1188 用它作 argv；但非 fork(Windows/subprocess)分支 L1227 用的是未解码的 query。同一契约在两条路径上行为不一致：查询串 "a+b" 在非 fork 路径传参时不会被还原为空格。【实测】inspect.getsource 核对行号：L109 定义 decoded_query，L114/L115 fork 分支使用，L153 非 fork 分支使用裸 query——该变量在 fork 分支之外的整段中再无引用，属典型遗漏而非设计。


## 4. None 的形态分布

| 形态 | 计数 |
|---|---|
| `N-CTX` | 2 |
| `N-INV` | 2 |
| `N-SHIM` | 6 |

N-SHIM 操作化口径：函数体为对另一可调用对象的单条委托调用，无分支/校验/状态写入。属性 getter 暴露自身状态（如 #44）与常量谓词（如 #29）不计为 SHIM，判 0。

## 5. 规程注记（必须随读数一起报）

1. **不看 evidence_hint 定向**（RULE 纪律①）：#6/#19/#21/#22/#30/#37/#38/#39/#40/#46/#47/#48/#52/#53/#54/#55/#56/#67/#72/#76/#78/#80/#92/#95 等锚点命中单元，凡无失效机理者一律判 0；#55 命中 `sink:eval` 照判 0。
2. **9 个单元的工作簿源码被截断**，已从同机同版本 stdlib（`C:\Users\26672\.workbuddy\binaries\python\versions\3.13.12\Lib`，与 framecheck.json 的 target 一致）按 `文件:行号:长度` 补全后再判：#4 / #14 / #16 / #18 / #33 / #37 / #55 / #72 / #96。这是**数据完整性修补**，不是扩大判据；若不接受，这 9 条应降为 None。
3. **未拆封模型侧读数**：`B2-E4-modelside.jsonl` / `-stats.json` / `-SEAL.md`（mtime 01:52–01:56，早于本裁定）按 PREREG v1.5·A5 密封协议保持未读，仅登记文件名与时间戳。比对须在人工裁定冻结后进行。
4. **单裁判**：无第二标注者，Krippendorff α / Gwet AC1 / κ **均不可测**（PREREG v1.5·B1-B4 的量在本层给不出），不得以自一致性冒充。作废规则的双阶段设计在本批无法执行。
5. **0 的语义限定**：每条 0 = "在所示证据内确认无缺陷"，**不是**"该单元绝对无缺陷"。
6. **本层不构成人工锚定**：按 PREREG 出口判据，锚定层完成前一切精度数字只许以"仪器灵敏度"名义出现。

## 6. 自纠记录（判 1 后经执行验证证伪）

### #98 `zoneinfo._tzpath._validate_tzfile_path`：1 → **0**

- **原判**：L108-109 `resolved.startswith(_base)` 是无分隔符的纯前缀匹配 → 判 1（security）。
- **实测 1（支持原判）**：`_base="C:\\tzdata"` 时，`key="..\tzdataX\Etc"` 的 normpath 与原串等长（过掉 L103 长度闸），`join+normpath` = `C:\tzdataX\Etc`，仍以 base 为前缀 → **ACCEPTED**，逃逸成功。
- **实测 2（证伪原判）**：`find_tzfile` 的源码是 `_validate_tzfile_path(key)` —— **不传 _base**。默认值 `_TEST_PATH = os.path.normpath(os.path.join("_","_"))[:-1]` = `"_\"`（且在 L115 被 `del`）。此时任何前导 `..` 会先吃掉 `_` 这个锚点，结果不再以 `_\` 开头 → **fail-closed**：`..\tzdataX\Etc` / `..` / `..\..\Windows` 全部 REJECTED，合法 `Etc\GMT` ACCEPTED。
- **结论**：失效机理只在 `_base` 被显式传为绝对路径时成立；生产路径不可达 → **降为 0**。
- **代价**：1 率由 3% 降为 2%。这是"宁可 None 不猜 1"同向的纪律——判 1 必须承受执行验证，不通过就撤回。
- **残留观察项（登记但不计缺陷）**：该检查的正确性依赖一个被 `del` 掉的相对哨兵常量，而非 `os.sep` 边界校验；若将来有人给 `_base` 传入真实 TZPATH，前缀旁路立即复活。

## 7. 产物（2026-10-10 归还恢复后布局）

| 文件 | 内容 | 状态 |
|---|---|---|
| `EXP/B2-E4-adjudication.csv` | 判定真件（100 行，12 列） | **原件，事故中未被触碰**（33927 B / 02:15:33） |
| `EXP/B2-E4-adjudication.jsonl` | 逐单元裁定回执（含 `reconstructed_from` / `reconstructed_by` / `original_overwritten` 标记） | 同源重建（原件 48704 B 毁于覆盖事故） |
| `EXP/B2-E4-sample.csv` | 机器表填版（原始 16 列 schema，填 truth/defect_type/annotator/date） | 同源重建（原件 21822 B 毁于覆盖事故） |
| `EXP/B2-E4-adjudication.md` | 本报告 | 同源重建（原件 6116 B 毁于覆盖事故） |
| `EXP/多agent判断/B2-E4-adjudication-judgeA-hy4-preview.{jsonl,csv,md}` | 三裁判对照包内的 `-judgeA` 后缀副本 | 重建副本（一致性计算 `calc_b2_e4_agreement.py` 的输入，勿移） |
| `EXP/多agent判断/B2-E4-sample-judgeA-hy4-preview.csv` | 对照包内的机器表副本 | 重建副本 |

**未触碰**：judgeB 与 judgeC 的全部产物；`EXP/B2-E4-adjudication.src.jsonl` / `EXP/B2-E4-adjudication-judgeC.src.jsonl`（judgeC 冻结判定源，02:15:20）。
