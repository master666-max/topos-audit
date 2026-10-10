# E-B2-4 三裁判事后对照（post-hoc，**非预注册分析**）

> **为什么有这个文件**：同一 `EXP/` 目录下存在三个互不知情的 L4-control 裁判。
> 本文件由 `_xjudge_compare_judgeC.py` 在 judgeC 判定**冻结之后**生成，
> **不修改任何 truth/defect_type/rule/note**，也不解封 `B2-E4-modelside*`（§A5 密封仍然有效）。
> 这里的数字只作**相对读数**：n=100、单层 n=20~30，任何差值都必须带 Wilson 区间读。

## 0. 谁是谁（可由 mtime / CreationTime 复核）

| 裁判 | annotator | 何时落盘 | 产物 |
|---|---|---|---|
| judgeA | `L4-control:Otto(single-rater,no-kappa)` | CreationTime 02:12:58 / LastWrite 02:15:33 | `B2-E4-adjudication.{jsonl,csv,md}` + 填过的 `B2-E4-sample.csv` |
| judgeB | `L4-control-judgeB-qoder` | 02:47:47 起（`_adj_batch*` 02:15:03 / 02:36:10） | `B2-E4-adjudication-judgeB.*` |
| judgeC | `ai:dsh-deepseek-flash` | 判定冻结 02:15:20（`.src.jsonl`）；08:52:37 落盘 | `B2-E4-adjudication.{jsonl,md}` + `B2-E4-sample.csv` + 本组 `-judgeC.*` |

⚠️ **judgeC 落盘时覆盖了 judgeA 的两个文件**：`B2-E4-adjudication.jsonl`（judgeA 版 48704 字节 → 现 62525）
与 `B2-E4-adjudication.md`（judgeA 版 6116 → 现 10598）；两者 CreationTime 仍为 **02:12:58**，
证明是**就地截断**而非新建。judgeA 的 `B2-E4-adjudication.csv`（33927 字节，02:15:33）**未被触碰**，
故 judgeA 的 100 条判定**可从此 CSV 完整恢复**（本对照即用它）。
详见同目录 `B2-E4-adjudication-PROVENANCE-NOTE.md`。

## 1. 分布

| 裁判 | 1 | 0 | None | 1 率 (Wilson 95%) |
|---|---:|---:|---:|---|
| judgeA(Otto) | 2 | 88 | 10 | 2.0% [0.6%, 7.0%] |
| judgeB(qoder) | 11 | 75 | 14 | 11.0% [6.3%, 18.6%] |
| judgeC(dsh) | 4 | 96 | 0 | 4.0% [1.6%, 9.8%] |

## 2. 两两一致率

`硬一致` = 剔除任一方为 None 的单元；`全一致` = None 作第三类（`PREREG` §B2：作废线绑全一致口径）。

| 对 | 硬一致 | 全一致 |
|---|---|---|
| judgeA(Otto) vs judgeB(qoder) | 71/82 = 86.6% | 77/100 = 77.0% |
| judgeA(Otto) vs judgeC(dsh) | 88/90 = 97.8% | 88/100 = 88.0% |
| judgeB(qoder) vs judgeC(dsh) | 73/86 = 84.9% | 73/100 = 73.0% |

## 2b. 阳性集（truth=1）重叠 —— 本对照最重要的一条读数

- **judgeA(Otto)**（2 条）：#4, #72
- **judgeB(qoder)**（11 条）：#12, #20, #25, #26, #31, #33, #37, #55, #62, #93, #96
- **judgeC(dsh)**（4 条）：#4, #5, #18, #72

| 两两交集 | 交集大小 |
|---|---:|
| judgeA(Otto) ∩ judgeB(qoder) | 0  |
| judgeA(Otto) ∩ judgeC(dsh) | 2 (#4, #72) |
| judgeB(qoder) ∩ judgeC(dsh) | 0  |

并集 = **15** 条；三裁判**共同**认定 = **0** 条 。

**读法（关键）**：三名机器裁判在**阴性类**上高度一致（硬一致 85%~98%），
而在**阳性类**上几乎不相交。这意味着：

1. 任何被 0 类主导的「一致率」都会**虚高**——A vs C 的全一致 88% 里，绝大部分只是「都说了 0」。
   这正是 `PREREG/B2.md` §B3（prevalence 悖论）与 `B2-E4-README.md` 假共识哨兵要防的形态，
   只不过这次「假共识」发生在**机器裁判之间**。
2. 拿本层当「对照尺」去比各信号源时，**必须分裁判报**（或报并集/交集），
   不能把三个裁判的 1 混成一个「机器真值」——它们的阳性集互不覆盖，混合等于把分歧藏进一个数里。
3. 三裁判并集 15 条 > 任一裁判，说明机器尺子的**召回**靠并集、**精确**不可由单裁判承担；
   这与 `RULE.md`「本层产出是对照尺，不是金标」一致。

## 3. 分歧明细（按层）

| seq | 层 | 单元 | judgeA(Otto) | judgeB(qoder) | judgeC(dsh) |
|---:|---|---|---|---|---|
| 4 | random | `compile_file` | 1 | None | 1 |
| 5 | confluence | `_update_func_cell_for__class__` | 0 | 0 | 1 |
| 10 | confluence | `_Globber.compile` | None | None | 0 |
| 11 | zero_cover | `GzipFile.seek` | None | None | 0 |
| 12 | random | `IMAP4.uid` | 0 | 1 | 0 |
| 14 | confluence | `getfullargspec` | 0 | None | 0 |
| 16 | confluence | `normalize` | 0 | None | 0 |
| 17 | random | `ModuleFinder.import_hook` | None | None | 0 |
| 18 | zero_cover | `netrc._parse` | 0 | 0 | 1 |
| 19 | anchor | `spawnl` | None | 0 | 0 |
| 20 | random | `_Unpickler.load_binbytes` | 0 | 1 | 0 |
| 22 | anchor | `genops` | None | None | 0 |
| 24 | zero_cover | `ProfileBrowser.do_callers` | None | None | 0 |
| 25 | random | `_ModuleBrowser.visit_ImportFrom` | 0 | 1 | 0 |
| 26 | zero_cover | `TextRepr.repr_instance` | 0 | 1 | 0 |
| 28 | random | `TCPServer.get_request` | None | 0 | 0 |
| 31 | zero_cover | `TarInfo._proc_gnusparse_01` | 0 | 1 | 0 |
| 33 | random | `main` | 0 | 1 | 0 |
| 37 | anchor | `register_standard_browsers` | 0 | 1 | 0 |
| 40 | anchor | `_aix_bos_rte` | 0 | None | 0 |
| 54 | anchor | `_UnixSelectorEventLoop._make_subprocess_transport` | 0 | None | 0 |
| 55 | anchor | `namedtuple` | 0 | 1 | 0 |
| 57 | confluence | `_encode_base64` | 0 | None | 0 |
| 62 | confluence | `get_local_part` | 0 | 1 | 0 |
| 72 | anchor | `CGIHTTPRequestHandler.run_cgi` | 1 | None | 1 |
| 74 | random | `NamespaceReader._resolve_zip_path` | None | 0 | 0 |
| 83 | random | `MagicMixin._mock_set_magics` | None | None | 0 |
| 92 | anchor | `DOMBuilder._parse_bytestream` | None | 0 | 0 |
| 93 | confluence | `_include` | 0 | 1 | 0 |
| 94 | random | `Unmarshaller.end_value` | 0 | None | 0 |
| 96 | confluence | `main` | 0 | 1 | 0 |

分歧单元数 = **31/100**。

## 4. judgeC 的自我披露（看到另两裁判之后，不回改自己的判定）

- judgeA 在 **#4 `compile_file`** 上报的机理与 judgeC **不同**：judgeA 指出
  `optimize=[]` 且 `force=True` 时 245 行 for 体零次执行 → 277 行 `if ok == 0` 引用未绑定 →
  `UnboundLocalError`，并附**实测**（`compile_file(p, quiet=2, force=True, optimize=[])`）。
  judgeC 读同一函数时走的是另一条路（hash 失效模式下新鲜度快路永不成立），**未发现**该 `ok` 未绑定路径。
  这是 judgeC 这条尺子的**灵敏度缺口**：它按 P1 拒用执行验证，因而漏掉了一个可实测的边界缺陷。
- 本条**不回改** judgeC 的 #4 读数（规则先于判定；事后改判会把对照尺污染成「看过答案」的尺子）。
  它只作为「同层裁判间的互补性」读数登记：三裁判的并集 > 任一裁判。
- judgeC 与 judgeA 在 **None 口径**上差异最大：judgeA 记 10 条 None（N-SHIM 6 / N-INV 2 / N-CTX 2），
  judgeC 记 0 条。按 judgeC 报告 §2 的披露，这来自证据范围不同（judgeC 把截断体与同文件被调方就地解析），
  而不是「谁更保守」。这一条**正是**该被拿去比较的量：同一工作簿上，两名机器裁判的 None 率差 10 个百分点。

## 5. 产物

- `EXP/B2-E4-adjudication-judgeC.src.jsonl` —— 已存在，跳过
- `EXP/B2-E4-adjudication-judgeC.jsonl` —— 已存在，跳过
- `EXP/B2-E4-adjudication-judgeC.md` —— 已存在，跳过
- `EXP/B2-E4-adjudication-judgeC.csv` —— 已存在，跳过
