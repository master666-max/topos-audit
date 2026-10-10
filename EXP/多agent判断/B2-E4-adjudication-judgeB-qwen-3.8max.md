# E-B2-4 L4-control 裁定报告 —— judgeB ＝ `qwen-3.8max`

> **产物性质**：机器对照层（L4-control），**不是金标、不是真值**。授权出处见 `B2-E4-RULE.md:6-8`
> （用户 2026-10-10 原话「根本不存在真值，你全权负责裁判，作为其他成果的对照」）。
> 本件**未写入** `topos/calib/gold.py` 的金标 CSV，符合 `WORK-ORDERS.md:106` 禁止令。
>
> **裁判 / annotator**：`ai:qwen-3.8max(L4-control,judgeB,single-rater,no-kappa)`
> —— 模型名 `qwen-3.8max` 由**用户 2026-10-10 指定**，本 agent 不自证型号；`judgeB` 是本工作区的裁判编号。
> 该串写进了全部 100 条 jsonl 记录与 csv 每一行的 `annotator` 列（改名经过见 §13）。
> **日期**：2026-10-10 ｜ **靶**：Python 3.13.12 标准库（纯 stdlib 框，13203 单元）
> **判据版本**：`B2-E4-RULE.md`（三值 1/0/None + None 四形态）｜**预注册**：`PREREG/B2.md` v1.5
> **件**：`B2-E4-adjudication-judgeB-qwen-3.8max.jsonl`（100 行，每行含 `rule` 字段，满足 RULE:40）｜`.csv`｜`-stats.json`
> **文件名**：`B2-E4-adjudication-judgeB-qwen-3.8max.*` —— 用户 2026-10-10 二次裁决「全改，文件名也要」之后模型名已进入文件名；保留 `judgeB` 是因为它是本工作区的裁判编号，且别的产出者按此编号引用本件。改名、引用传播与一次自伤的完整记录见 §13。

---

## 0. 为什么落点不是 RULE.md:11 指定的 `B2-E4-adjudication.*`

**因为那条路径已被另一个产出者占用。** 本会话开工时（首次 `ls`）`EXP/` 下**不存在** `B2-E4-adjudication.*` 与 `B2-E4.md`；
在我读完工作簿、写出第一份裁定草稿之后，它们出现了。为避免覆盖他人产物（数据无损优先），本件全部落在
`B2-E4-adjudication-judgeB-qwen-3.8max.*`，且**完全没有触碰** `B2-E4-sample.csv`（用户四步清单里的第 4 步回写目标，现已被对方填满）。

时间线（`ls --time-style=full-iso` 实测，非记忆）：

| 时刻 | 件 | 产出者 |
|---|---|---|
| 01:48:36 | `B2-E4-workbook.md`（132363 B） | 已提交（HEAD=9273432） |
| 01:52:34 | `B2-E4-modelside.jsonl` | 另一会话，**未跟踪**，PREREG A5 密封件 |
| 01:56:04 | `B2-E4-modelside-SEAL.md` | 同上 |
| 02:08:13 | `B2-E4.md`（23513 B） | **另一产出者**（早于我的第一份产物） |
| 02:15:03 | `_adj_batch1.json` | 本会话（我） |
| 02:15:33 | `B2-E4-adjudication.{csv,jsonl,md}` + `B2-E4-sample.csv` 被改写 | **另一产出者**（四件同一秒） |
| 02:36:10 | `_adj_batch2.json` | 本会话（我） |

`B2-E4-sample.csv`：HEAD blob = 16575 B（无 BOM，`truth` 列 0/100 填充）；工作树现 = 21822 B（**带 BOM**，`truth` 100/100、`defect_type` 2/100）。
本报告的单元名册一律从 **HEAD blob** 读（`git cat-file blob HEAD:EXP/B2-E4-sample.csv`，sha256 `0d4ad3343c8e7e43…`），
以免并发写入把名册在我脚下换掉。

---

## 1. 口径节（必读）

1. **单裁判。** 本件是一个裁判的 100 条读数。`RULE.md:48` 明定：单裁判无独立复标 ⇒ **标注者可靠性 κ 不可测**，
   不得以自一致性冒充。本件不报 κ，也不报 α。
2. **`0` 的含义是有界的。** 按 `RULE.md:18`，`0` = “在所示证据内确认无缺陷”，**不是**“该单元绝对无缺陷”。
   本件 75 条 `0` 全部带这一限定。
3. **`1` 的含义是有界的。** 每条 `1` 都附机理句与可信输入；11 条全部经过对真 3.13.12 stdlib 的执行验证（见 §4）。
4. **未读密封件。** `B2-E4-modelside.jsonl` / `-stats.json` / `-SEAL.md` 三件，本会话**只做过 `ls`/`stat` 与结构计数**
   （记录条数与键名），**从未读取任何判定值**。PREREG `A5` 规定解封须在人工裁定冻结之后由用户执行，本件不代劳。
5. **未读对方裁定的判定值。** 对 `B2-E4-adjudication.*` 与 `B2-E4.md`，本会话只取过：列名、行数、各列填充计数、
   以及 `B2-E4-adjudication.md` 的**标题行**与 `B2-E4.md` 的**关键词出现次数**。没有读取任何单元的 `truth`/`note` 值。
   因此 §2 的一致率对比只用到「对方 `defect_type` 非空 = 2 条」与「其 §3 两个小标题是 #4 与 #72」这两项元数据。
6. **同一单元存在两个互不知情的产出者。** 这一点按 `AGENTS.md` R-4 要求显式写进口径：本件与 `B2-E4-adjudication.*`
   是对同 100 单元的两次独立裁定，任何一方都不应被当作另一方的复核。
7. **本报告不含真值主张。** 按 `RULE.md:46`，本层**不能**折扣公开集（Devign/BigVul）的人工标签，
   **不能**给出系统真实 Se/Sp；按 `PREREG:75`，锚定层完成前一切精度数字只许以“仪器灵敏度”名义出现。

---

## 2. 总体分布

| truth | 条数 | 占比 | Wilson 95% CI |
|---|---|---|---|
| `1` 有缺陷 | **11** | 11% | 6% – 19% |
| `0` 所示证据内无缺陷 | **75** | 75% | — |
| `None` 判不出来 | **14** | 14% | 9% – 22% |

CI 用 **Wilson score**（`PREREG` 附录 C 明定禁用 Wald）。n=100 下比例 CI 半宽约 ±7 点，与 `PREREG:129` 预告的诚实宽度一致。

`rule` 字段分布（哪条规则产出哪条读数，满足 RULE:40 可回溯要求）：
`R0`=75 ｜ `R1`=11 ｜ `RN-INV`=6 ｜ `RGAP-trunc`=4 ｜ `RN-SHIM`=3 ｜ `RGAP-extfmt`=1

`defect_type` 词表（本轮自定义，见 §7.6）：`error_handling`=5 ｜ `logic`=4 ｜ `boundary`=1 ｜ `message`=1

执行验证状态：`exec-confirmed`=10 ｜ `exec-confirmed-mechanism-corrected`=1（#20，机理措辞被实测纠正）
｜ `exec-refuted`=2（#80、#98，**原判 1 被自己证伪后撤回**）｜ 其余 87 条为 `0`/`None`，未做执行验证。

---

## 3. 分层分布 + 对 PREREG A1 序约束

| 层 | n | `1` | 1 率 (Wilson 95% CI) | `0` | `None` | None 率 | 对 40% 线 |
|---|---|---|---|---|---|---|---|
| `random` | 30 | 4 | 13% (5–30%) | 22 | 4 | 13% | 未越线 |
| `confluence` | 20 | 3 | 15% (5–36%) | 13 | 4 | 20% | 未越线 |
| `anchor` | 25 | 2 | 8% (2–25%) | 19 | 4 | 16% | 未越线 |
| `zero_cover` | 25 | 2 | 8% (2–25%) | 21 | 2 | 8% | 未越线 |

**没有任何一层 None 率 > 40%**，故 `PREREG:108` 的“可判性不足”标记本轮**不触发**（层内 α 的辅助判读资格保留，
但 `PREREG:130` 已预告层内 n=20~30 时 CI 半宽可达 ±0.20，故层内读数只作辅助）。

**A1 序约束 π(anchor) > π(random) > π(zero_cover) 被违反了一半**：
实测 π(anchor)=8% **<** π(random)=13%（违反）；π(random)=13% > π(zero_cover)=8%（满足）。
按 `PREREG` A4 的补充注册，这属“小样本下因抽样噪声而不满足”的情形：**用软惩罚、并如实记录违反幅度**——
两层的 Wilson CI 高度重叠（anchor 2–25% vs random 5–30%），违反幅度远小于噪声，
故本批定向结果若最终落在约束边界上，须按 A4 标注“**定向由约束边界决定，非数据决定**”。

一条值得记的旁证：anchor 层是四层里“看着最可疑”的一层，但它的 1 率并不高于无偏基线 random 层；
同时 §8.4 会给出 anchor 信号有 11/52 条命中落在注释与文档串散文上。两者方向一致，
但**这不能反过来当作“anchor 层无缺陷”的证据**（RULE:32 禁止把锚点当定向）。

---

## 4. 判为 `1` 的 11 条（逐条机理，全部附执行验证）

验证脚本与原始输出已落盘，可复算：`_verify_b2e4_ones.py`、`_verify_b2e4_pass2.py`、`_verify_b2e4_pass3.py`、
`_verify_pass2.stdout`、`_verify_pass3.stdout`。每条测试都带**正对照**（必须通过）与**负对照**（必须失败），
以免“尺子坏了”被读成“靶没问题”——本轮 #98 就是这个坑，见 §6。

| # | 单元 | 层 | defect_type | 机理（一句话） | 执行验证 |
|---|---|---|---|---|---|
| 12 | `imaplib.IMAP4.uid` | random | logic | 文档串承诺“response appropriate to command”，但除 SEARCH/SORT/THREAD 外把响应名硬编码成 `FETCH`，UID COPY/MOVE 的服务端响应被丢成 `[None]` | 实测 `Commands` 含 COPY/MOVE(states=SELECTED)、`uid()` 无 COPY 分支、非 UID 的 `copy()` 用的是 `'COPY'` |
| 20 | `pickle._Unpickler.load_binbytes` | random | error_handling | 头部短读泄漏 `struct.error` 而非 `UnpicklingError`；载荷短读不校验长度（未用现成的 `_readbytes`），且纯 Python 与 C 两实现对同一畸形流给出不同异常类型 | 实测 2 字节流 → `struct.error`；声明 100 给 3 → 静默 append；C 实现同流 → `UnpicklingError`。**原判措辞“不报任何错”不准确，已更正**（实际后续以 `EOFError` 失败） |
| 25 | `pyclbr._ModuleBrowser.visit_ImportFrom` | random | logic | 星号导入只用 `startswith('_')` 过滤——那是 Python 在**无 `__all__`** 时的回落规则，代码把它当唯一规则，没有 `__all__` 分支 | 实测：`__all__=['A']` + 定义 A、B 的模块，`from m import *` 后 pyclbr 树给 `['A','B']`，真运行时 `dir()` 只给 `['A']` |
| 26 | `pydoc.TextRepr.repr_instance` | zero_cover | error_handling | 裸 `except:` 吞掉 `BaseException`，Ctrl-C / `sys.exit` 被转成一段看似正常的 `'<X instance>'`；回落表达式自身也可能抛 | 实测 `TextRepr().repr_instance`：KeyboardInterrupt → 被吞、SystemExit → 被吞；正对照 `object()` 与负对照 ValueError 均如设计 |
| 31 | `tarfile.TarInfo._proc_gnusparse_01` | zero_cover | boundary | `zip(sparse[::2], sparse[1::2])` 对奇数个值**静默丢掉最后一个**；`int()`/缺键抛 ValueError/KeyError 而非 tarfile 承诺的 `TarError` 家族 | 实测 6 值→3 对（正对照）、5 值→2 对（第 5 值蒸发）、单值→`[]`、`'abc'`→ValueError、缺键→KeyError，后两者 `isinstance(e, TarError)=False` |
| 33 | `tokenize.main` | random | error_handling | `except KeyboardInterrupt` 只 `print` 就落出函数，进程以**退出码 0** 结束；而同函数所有其他异常路径都经 `error()` 走 `sys.exit(1)` | 实测真源码该 handler 体确为单条 print、无 exit/raise；负对照 `error()` 确以 `sys.exit(1)` 收尾 |
| 37 | `webbrowser.register_standard_browsers` | anchor | error_handling | `raw_result.decode()` 未带 `errors=`，而 `UnicodeDecodeError` 不在那个列举了四种环境故障并一律 `pass` 的 except 元组里，一次纯探测能让整个浏览器注册失败 | 实测 except 元组 =（FileNotFoundError, CalledProcessError, PermissionError, NotADirectoryError），不含 UnicodeDecodeError；`.decode()` 确无 `errors=`。**可信度弱于其余各条**（需非 UTF-8 输出），已在读数里明示 |
| 55 | `collections.namedtuple` | anchor | logic | `map(str, field_names)` 与 `intern(str(typename))` 先把一切强转成精确 `str`，使其后 `if type(name) is not str: raise TypeError(...)` **恒不可达**；非字符串输入得到的是 ValueError 而非代码自己声明的 TypeError | 实测 `namedtuple('P',[1,2])`→ValueError、`namedtuple(123,'x y')`→ValueError；正/负对照正常；并核实源码中 `map(str,` 的位置确在 `'must be strings'` 之前 |
| 62 | `email._header_value_parser.get_local_part` | confluence | message（低severity） | 报文串 `"local-part contains non-ASCII characters)"` 末尾多一个无配对的 `)`，会随 `msg.defects` 流到下游 | 实测真源码字面量确含该多余括号；实调 `get_local_part('café')` 产出的 defect 文本原样带着它 |
| 93 | `xml.etree.ElementInclude._include` | confluence | error_handling | `e.get("href")` 无 None 守卫，而 XInclude 规范里 href 可选；缺 href 时炸成 `TypeError` 而非本函数在其余五条失败路径上一律使用的 `FatalIncludeError` | 实测不带 href 的 `<xi:include parse="text"/>` → `TypeError: expected str, bytes or os.PathLike object, not NoneType`；负对照 `parse='bogus'` → 如契约抛 `FatalIncludeError` |
| 96 | `zipfile.main` 内嵌 `addToZip` | confluence | logic | 用 `isfile`/`isdir` 判类型（二者都**跟随符号链接**），递归既无 `islink` 守卫也无已访问集合 ⇒ 符号链接环导致无界递归 | 实测真源码片段不含 islink/realpath/seen；`isdir(sub/loop)=True`；跑真 CLI 于含环目录树 → rc=1，**终末症状是撞 Windows MAX_PATH 的未捕获 `FileNotFoundError`（并留下 12664 B 半成品 zip），不是我原先预测的 RecursionError**，已更正 |

**#62 的严重度分级**：这是本批唯一一条纯诊断文本缺陷，不影响解析结果。已在 jsonl 里标 `defect_type=message`，
便于读者按需剔除后重算 1 率（剔除后为 10/100）。

---

## 5. `None` 的 14 条：形态分布

| 形态 | 条数 | 单元 | 判据出处 |
|---|---|---|---|
| `N-INV` 依赖未记录不变量 | 6 | #11 #17 #54 #57 #83 #94 | RULE:26 |
| `RGAP-trunc` 工作簿截断（**规则外**） | 4 | #4 #14 #16 #72 | RULE:3-4 |
| `N-SHIM` 壳/转发单元 | 3 | #10 #22 #24 | RULE:27 |
| `RGAP-extfmt` 依赖外部接口未记录格式（**规则外**） | 1 | #40 | RULE:3-4 |
| `N-CTX` 跨文件语义缺失 | **0** | — | RULE:25 |
| `N-VER` 版本敏感 | **0** | — | RULE:28 |

**`N-CTX` 一条都没用，是刻意的**：它的判据要求“该单元的正确性依赖调用方如何用它”，而工作簿的调用方信息不可靠（§8.5）。
用它当 None 的理由会把仪器缺陷洗成靶的性质。

**两条规则外形态（rule_gap）**，按 `RULE.md:3-4` 记录且**未修改规则文件**：

- **`RGAP-trunc`（工作簿截断）**：RULE 的 None 四形态里没有“所示源码被截断”这一类。
  处理政策见 §7.1。9 个截断单元里 4 个（#4 #14 #16 #72）隐藏段正好承载文档串承诺的行为，故记 rule_gap；
  另 5 个（#18 #33 #37 #55 #96）机理在可见段内，照常判定。
- **`RGAP-extfmt`（外部接口格式未记录）**：#40 `_aix_bos_rte` 的正确性取决于 `lslpp -Lqc bos.rte` 的字段布局。
  这既不是跨文件调用者（N-CTX）、也不是类/模块级不变量（N-INV）、更不是壳（N-SHIM）或版本门（N-VER）。
  对一个以真实代码为靶的审计工具来说，“依赖外部命令/协议/文件格式的未记录契约”是**常见**情形，
  规则表缺这一格值得回补（但按 RULE:3-4 只能登记，不能由裁判改规则）。

---

## 6. 自纠 / 撤回记录（2 条）

两条原判 `1` 经对真 stdlib 执行验证后**被自己证伪**，改判 `0`。撤回理由与复算命令都在 jsonl 的 `note` 里，
`retracted_from` 字段标 `"1"`，`verification` 字段标 `exec-refuted`。**自纠率 2/13 = 15.4%**（对最初判为 1 的 13 条而言）。

### #98 `zoneinfo._tzpath._validate_tzfile_path`：1(security) → **0**

- **原判机理**（当时看起来成立，且我用 posixpath 与 ntpath 双向重放都“通过”了）：第三道检查 `resolved.startswith(_base)`
  是裸前缀比较、缺分隔符边界，故 `../zoneinfo-leaks/secret` → `/usr/share/zoneinfo-leaks/secret` 会被放行，逃出 TZPATH。
- **证伪**：生产唯一调用点是 `find_tzfile(key) → _validate_tzfile_path(key)`，**不传 `_base`**；
  默认 `_base=_TEST_PATH=normpath(join('_','_'))[:-1]`，实测其值为 `'_' + os.sep` —— **以分隔符结尾**，
  `startswith` 因此天然带边界；且这个合成根只有一个分量，任何 `..` 都会整体弹出它。
- **实测（真函数，带正反对照）**：正对照 `Europe/London` → ACCEPTED（证明尺子有效）；
  负对照 `../etc/passwd` → REJECTED（证明尺子有分辨力）；`../zoneinfo-leaks/secret` → **REJECTED**；
  `../_x/secret` → REJECTED；`a/../../secret` → 被第二道长度检查 REJECTED。
- **残留（降级为加固建议，非缺陷）**：显式传入**不以分隔符结尾**的 `_base` 时弱点确实可达
  （实测 Windows 型 `_base` 不加尾分隔符 → 攻击 ACCEPTED，加尾分隔符 → REJECTED）。
  但 `_base` 是下划线私有参数、`_TEST_PATH` 用后即 `del`、模块内唯一调用点不传该参数 ⇒ 按 RULE:17“可信输入或状态”不成立。
- **方法论教训（这是本轮最贵的一课）**：我先后**两次**用 `'/'` 型 `_base` 在 Windows 上测这个函数，
  两次都得到“全部被拒”，连正对照 `Europe/London` 都被拒——分隔符不一致的尺子会把“靶没问题”与“尺子坏了”
  变成同一个读数。**只有带上正对照才分得开这两者。**

### #80 `multiprocessing.spawn.get_preparation_data`：1(logic) → **0**

- **原判机理两条**：①`main_module.__spec__` 是无守卫的直接取属性（而同函数对 `__file__` 却用了 `getattr(...,None)`），
  `__main__` 缺 `__spec__` 时抛 AttributeError，而本函数是 spawn 方式下每个子进程的必经之路；
  ②`sys_path[i] = process.ORIGINAL_DIR` 未守卫 None，而 20 行后作者自己写了 `is not None`，等于自证 None 可达。
- **证伪①**：实测五种真实启动方式（`python -c` / `python script.py` / `python -m mod` / `python -I -c` / `python -` 标准输入），
  `sys.modules['__main__']` **全部** `hasattr('__spec__')==True`（值为 `None` 或 `ModuleSpec`）。
  我原先的复现是靠 `delattr` 硬造的——**夹具造出来的状态，不是靶上真实存在的状态**。
- **证伪②**：实测 `multiprocessing.process.ORIGINAL_DIR` 在导入期即为绝对路径字符串（非 None）；
  `spawn.py` 内唯一赋值点是子进程侧 `process.ORIGINAL_DIR = data['orig_dir']`。父进程路径上 None 不可达。
- **残留观察（不升格）**：两个同类 dunder 一个守卫一个不守卫，风格不对称；`is not None` 那句在当前实现下恒真，属防御性冗余。

---

## 7. 解释性判据（本轮新增，披露而非偷用）

RULE.md 的三值判据在 4 处不够用。以下解释**全部登记在此**，未回改 `B2-E4-RULE.md`（RULE:3-4 禁止裁判改规则）。

1. **截断政策**（影响 9 个单元）：单元被截断时——
   (a) 隐藏段承载文档串承诺的行为 ⇒ `None` + `RGAP-trunc`；
   (b) 机理在可见段内完整成立 ⇒ 照常判 `1`（#33 #37 #55 #96 属此类）；
   (c) 可见段自足、隐藏段与契约无关 ⇒ 判 `0` 并在读数里写明“所示 N/M 行”（#18 属此类，60/63）。
2. **N-SHIM 的边界**（影响 5 个单元的归类）：RULE:27 的“纯转发或属性搬运”字面上会把所有单行委托都扫进来。
   本轮限定为——**委托对象是本仓内部逻辑、其契约无法从工作簿得知**时才记 N-SHIM（#10 `_compile_pattern`、
   #22 `_genops`、#24 `self.generic`）。若委托对象是契约已知的语言/标准库原语，则照常判定，
   因为“这次委托是否兑现本单元自己的契约”是可判的：#19 `os.spawnv`（实测为内建）、#28 `socket.accept`
   （实测 doc 为 `accept() -> (socket object, address info)`）、#59 `deque.extend`、#75 `map(str.strip,·)`、
   #79 `Event.wait`、#44 `return self._errors`。**#19 与 #28 因此从 None 改判 0**（见 `-stats.json` 的 revisions）。
3. **`assert` 当前置条件守卫的口径**（影响 #49 #58 #83 #90）：`assert` 在 `-O` 下被剥掉属既有语言语义，
   标准库通行以 assert 表“程序员错误”前置条件。本轮口径：**除非该单元自己承诺了具体异常类型**，
   否则 assert-as-validation 记为观察项、不升格为 `1`。#55 之所以升格，是因为它自己写了 `raise TypeError(...)` 而该分支不可达。
4. **N-INV 的触发门槛**（影响 #11 #87 #100 的分野）：只在**所示源码给出正面证据**表明决定性状态空间比假设更大时才判 N-INV。
   #11 判 N-INV 是因为 `if WRITE / elif READ` **没有 else**（正面暗示存在第三种 mode 值）；
   #87 判 `0` 是因为两个缓冲区在同一守卫下成对创建（这种写法只在“二者恒同步”成立时才讲得通，无正面反证）；
   #100 判 `0` 同理。这条门槛是为了防止把“我看不全”一律洗成 None。
5. **严重度分级**：`defect_type=message` 专留给只影响诊断文本、不影响行为的缺陷（本轮仅 #62），
   使读者能按需剔除后重算 1 率。
6. **`defect_type` 词表**（README:34 只给了 logic/security/boundary 三个例子）：本轮实际使用
   `logic` / `error_handling` / `boundary` / `message`；`security` 一条未用（唯一候选 #98 已撤回）。

---

## 8. 仪器发现（针对工作簿与抽样框本身，共 7 条）

这些是**对照尺在量靶的过程中量到的仪器性质**。按 RULE:32，其中锚点相关的各条**一律未用于设定任何 truth 值**。

1. **源码保真度：100/100 逐字节相符（正面结论）。**
   把每个单元的所示源码块与真 3.13.12 stdlib 文件在所述 `lineno` 处的等长片段逐行比对：
   **100 个单元全部完全一致，0 处不符，0 个文件缺失**。工作簿对靶的渲染是忠实的——
   这一条很重要，因为它排除了“裁判在判一份被改写过的源码”这种最坏情形。
   （脚本 `_verify_b2e4_pass3.py`，输出 `_verify_pass3.stdout`。）
2. **截断：9/100，且恒为 60 行。** 生成器 `make_b2_e4_sample.py` 里 `MAX_SRC_LINES = 60`、`shown = src_lines[:60]`。
   可见比例从 97%（#18 60/63、#33 60/62）到 **31%**（#72 60/196）、35%（#55 60/173）、41%（#4 60/148）。
   其中 4 个单元因隐藏段承载契约而**完全不可判**。
3. **截断会精确切掉锚点层选样所依据的证据。** #72 `CGIHTTPRequestHandler.run_cgi` 的 5 条锚点命中行位于
   L145/146/156/161/162，**全部在 60 行窗口之外**。也就是说：锚点层正是因为这些 subprocess 用法才把它选进样本，
   而工作簿把被选中的证据整段截掉了。这是抽样层与呈现层的口径冲突，不是 bug，但会让 anchor 层的裁定系统性偏向 None。
4. **装饰器行 0/100 全部丢失。** 全工作簿没有任何一个单元的所示源码以 `@` 开头（抽取器从 `def` 行起切）。
   后果：`@property` / `@staticmethod` / `@abstractmethod` / `@contextmanager` 一律不可见。
   具体风险点——#74 `_resolve_zip_path(path_str: str)` 无 `self` 且体内有 `yield`，必是 `@staticmethod` 生成器；
   #48 #52 #53 的 `raise NotImplementedError` 必是 `@abstractmethod`；#44 `errors` 必是 `@property`；
   #63 `rule` 与 #64 `_au` 实为 `@rule` 装饰器与其被装饰函数的一对，这层关系在工作簿里完全看不见。
   **本轮口径：装饰器缺失一律不得当作缺陷证据。**
5. **锚点信号有 11/52 条命中落在注释或文档串散文上。** 例：#22 `genops` 一个单元命中 5 次，
   其中 L1 是形参名 `pickle`、L2/L4/L6/L14 全是文档串文本；#19 `spawnl` 命中的是文档串里 “in a subprocess” 这句话；
   #6 `Enum.__new__` 命中的是一行提到 pickle 的注释；#52/#53 的命中全在文档串与 URL 上。
   这直接量化了 anchor 层的假阳性来源：**锚点是词法模式匹配，不区分代码与散文**。
   （再次声明：本条**未**用于压低任何 anchor 单元的 truth；#6 #21 #46 #47 #48 #52 #53 #76 #92 #95 等 anchor 单元仍按源码判 `0`。）
6. **`同文件调用者` 字段被同名方法污染。** 该字段按**裸方法名**匹配，于是把别的类里同名方法误报成调用者。
   最清楚的例子是 #84 `MagicProxy.__init__`：列出的 8 个“调用者”是 `_SentinelObject.__init__`、`_Sentinel.__init__`、
   `_MockIter.__init__`、`Base.__init__`、`NonCallableMock.__init__`、`CallableMixin.__init__`、`_patch.__init__`、
   `_patch_dict.__init__` ——它们是各自类的构造器，不可能是 `MagicProxy.__init__` 的调用者。
   同类情形还有 #44（列出 `TextIOBase.errors`/`StringIO.errors`）、#51（列出 `Lock.release`/`Semaphore.release` 等）。
   **后果**：RULE:25 的 `N-CTX` 形态以调用者信息为判据，故本轮**完全不依据该字段判 None**（§5 里 N-CTX = 0 条即由此而来）。
   另有 23/100 个单元根本没有该行。
7. **RULE 的 None 四形态有两个洞**，本轮各登记一条 rule_gap：截断（4 条）与外部接口格式依赖（1 条）。见 §5。

---

## 9. 对 `PREREG/B2.md` E-B2-4 判据的三态

| 判据 | 要求 | 本件的态 | 依据 |
|---|---|---|---|
| ① | 100 单元完成仲裁，折扣系数读数 CI 半宽 <0.15 | **不适用（登记盲区）** | 100 单元已完成，但“折扣系数”是**人际一致率**的折扣；`RULE.md:46` 明定机器对照层**给不出**该量。硬报一个数字就是把对照尺冒充金标 |
| ② | 5% 随机复核与仲裁结论一致率 ≥80% | **不可测；已用更强的替代读数** | 单裁判无独立复标（`RULE.md:48`），5% 复核无从做起。**替代**：13 条初判 `1` 全部做了执行验证，2 条被自己证伪并撤回（自纠率 15.4%），11 条终判 `1` 全部 `exec-confirmed`。这测的是“判定可被外部证据推翻的比例”，**不是**原判据，故不宣称②咬合 |
| ③ | 假共识检查：人 vs LLM 预标一致率不得显著高于人 vs 真值 | **不适用** | 需要“真值”端，而 `RULE.md:6-8` 已把本层从“唯一人工层”改定性为机器对照层，真值端不存在 |
| A5 | 模型侧读数须 SHA256 密封，仲裁冻结后方可解封 | **咬合（我方一侧）** | 本会话从未读取 `B2-E4-modelside.*` 的任何判定值，只做过 `ls`/`stat`/条数与键名计数。解封须由用户在裁定冻结后执行 |
| B2 | 任一层 None 率 >40% ⇒ 该层标“可判性不足” | **咬合（未触发）** | 四层 None 率为 13%/20%/16%/8%，均未越线（§3） |
| C | 比例 CI 用 Wilson，禁 Wald | **咬合** | §2 §3 全部为 Wilson score |

**出口判据**（`PREREG:73`：B2 批五枚全咬合或缺省层如实登记）：本件对 E-B2-4 的贡献是
**①③不适用、②不可测（已给替代读数）、A5/B2/C 咬合**，缺省项如上如实登记，不作粉饰。

---

## 10. 与另一产出者的读数对比（仅用元数据，未读其判定值）

> **口径更新**：本节写于工作区只有两个裁判时。此后又长出 judgeC 与 `多agent判断/` 一条线，
> 且发生过一次覆盖事故——那些都登记在 **§13.4**，本节不回填、不改写（历史引文照原样留档）。

| 项 | 本件 judgeB | `B2-E4-adjudication.*`（另一产出者） |
|---|---|---|
| 单元数 | 100 | 100（jsonl 100 行、csv 100 行） |
| `truth` 填充 | 100 | 100 |
| 判 `1` 的条数 | **11** | **2**（`defect_type` 非空 = 2） |
| 判 `1` 的单元 | #12 #20 #25 #26 #31 #33 #37 #55 #62 #93 #96 | **#4 #72**（据其报告 §3 的两个小标题） |
| 两者交集 | **∅（零重叠）** | |
| 执行验证 | 11/11 条 `1` 全部执行验证，另有 2 条自纠撤回 | 其报告有 §6「自纠记录（判 1 后经执行验证证伪）」，其中 **#98 由 1 改 0**——与本件独立得到的结论一致 |

两点值得用户裁决时注意：

- **零重叠不是小事。** 1 率 11% vs 2%，且两个集合完全不相交。若把两份裁定当两个标注者算 Krippendorff's α
  （`PREREG` B1 的主判据、原生支持 None 三分类），α 会远低于 `PREREG:51/108` 的 0.60 作废线。
  按 B4 的双阶段规则，那将触发“补第二批 n=100、同一分层配额、同一协议，且第二批为终局”。
  **但 α 由本件单独算不出来**——`RULE.md:48` 说的是单裁判无独立复标故不可测；两份独立裁定并存，
  才使这个量第一次变成可测的。**用户 2026-10-10 已裁：不算 α，两份各自成立、互为对照**（原话「不用管他，
  写你自己的，相互对照」）。故本件到此为止，不去读对方的判定值，也不合成任何一致率数字。
- **对方仅有的 2 条 `1` 都落在截断最严重的两个单元上**（#4 示 41%、#72 示 31%），而这两个单元本件都判 `None/RGAP-trunc`。
  这指向一个**方法论分歧**：`RULE.md:17-19` 把三值判据全部定义在“所示上下文/所示源码”上，
  而 #72 的 5 条锚点命中行全在 60 行窗口之外（§8.3）。若对方是去读了未截断的真源码才断出机理，
  那两份裁定的**证据基不同**，直接算 α 会把“证据基差异”读成“标注者不可靠”。这一点需要先厘清，否则 α 的含义会被污染。
  （我没有读对方的 note，所以这只是从其 §3 标题与截断比例推出的**待查问题**，不是结论。）

---

## 11. 产物与复算

| 件 | 说明 |
|---|---|
| `B2-E4-adjudication-judgeB-qwen-3.8max.jsonl` | 100 行，每行含 `rule`/`truth`/`defect_type`/`note`/`verification`/`retracted_from`/`truncated`/`obs_verified`/`layer=L4-control`/`is_gold=false` |
| `B2-E4-adjudication-judgeB-qwen-3.8max.csv` | 同内容表格版，UTF-8 with BOM（Excel 直开） |
| `B2-E4-adjudication-judgeB-qwen-3.8max-stats.json` | 分布、分层、**4 条 revisions 的完整改判理由**、名册 HEAD sha256 |
| `B2-E4-adjudication-judgeB-qwen-3.8max.md` | 本报告 |
| `_adj_batch1.json` / `_adj_batch2.json` | 冻结的原始草稿（改判**之前**的状态，保留以便复算改判幅度） |
| `_build_judgeB.py` / `_build_judgeB.stdout` | 报告与 jsonl/csv 的生成器与其实测输出 |
| `_verify_b2e4_ones.py` | 执行验证 pass 1（12 条 `1` 的初验；#96/#26 的夹具在此轮有缺陷，见 pass 2/3） |
| `_verify_b2e4_pass2.py` / `_verify_pass2.stdout` | pass 2：#20 改测纯 Python `_Unpickler`、#80 改测真实启动方式、#96 真 CLI 跑符号链接环 |
| `_verify_b2e4_pass3.py` / `_verify_pass3.stdout` | pass 3：**100/100 源码保真核对** + #26 定位到真类 `TextRepr` 后重测 |

复算入口（本机实测可用）：

```
py -X utf8 EXP/_verify_b2e4_pass3.py          # 源码保真 100/100 + #26
py -X utf8 EXP/_verify_b2e4_pass2.py          # #20 #80 #96
py -X utf8 EXP/_build_judgeB.py               # 重建 jsonl/csv/stats（幂等）
```

解释器：`C:\Users\26672\.workbuddy\binaries\python\versions\3.13.12\python.exe`（实测 3.13.14），
即 `B2-E4-framecheck.json` 里 `target` 所指的那一棵 stdlib。

---

## 12. 裁决记录（用户 2026-10-10 当场裁，五项）

按「裁定与实施分两栏」的口径记：左栏是用户裁了什么，右栏是**当前实际落地状态**（不是"打算做"）。

| # | 事项 | 用户裁决（原话/要旨） | 实施状态（已落地证据） |
|---|---|---|---|
| 1 | `B2-E4-sample.csv` 归属 | **「保持现状不动」** | 已落地。实测该文件 size=21822、mtime=1791569733 与对方写完时一致，`_audit_judgeB.py` G 节 PASS；本会话从未对它写入。它仍是**对方**填的版本（truth 100/100、带 BOM），我的 11 条不在其中 |
| 2 | 落点冲突（RULE.md:11 的 `B2-E4-adjudication.*` 被占用） | 随第 1 项一并裁：各写各的、互为对照。**后续追加裁决**（用户「全改，文件名也要」）：文件名须带模型名 | 已落地。本件四件套为 `B2-E4-adjudication-judgeB-qwen-3.8max.{jsonl,csv,md}` ＋ `…-stats.json`，sha256 见 §13.5。**未创建、未修改**任何 `B2-E4-adjudication.*` 通用名。改名经过与引用传播见 §13.3–§13.5 |
| 3 | 是否算双裁判 α / 是否去查对方证据基 | **「不用管他，写你自己的，相互对照」** | 已落地。**未计算 α**，未读对方任何判定值或 note。§10 的对比只用元数据（对方 `defect_type` 非空=2、其 §3 两个小标题为 #4/#72）。§10 第二条关于"对方是否读了未截断源码"的疑问，按此裁**登记为开放问题、不再追** |
| 4 | `B2-E4-modelside.*` 解封 | **「保持密封，等你发话」** | 已落地。三件 size/mtime 实测未变（`_audit_judgeB.py` G 节 PASS）。本会话对其只做 `ls`/`stat` 与"记录条数+键名"级别的结构计数，**从未读取任何判定值**。本件已冻结，解封时机由用户掌握 |
| 5 | 两条 rule_gap 是否回补进 `B2-E4-RULE.md` | 未裁（用户未就此发话） | **仍开放**。按 RULE:3-4 裁判无权改规则，本件只在 §5/§7.1 登记：`RGAP-trunc`（截断，4 条）与 `RGAP-extfmt`（外部接口格式未记录，1 条）。规则文件未被本会话修改 |

**由此确定本件的最终地位**：它是一份**独立、已冻结、每条 `1` 都经执行验证**的 L4-control 对照读数，
与另一产出者的 `B2-E4-adjudication.*` **并列为两份互不合并的对照**，不合成任何一致率、不充当金标、不进 `gold.py`。

---

---

## 13. 裁判身份打标与改名（用户 2026-10-10 两次裁决）

### 13.1 两次裁决，以及我第一次为什么只做了一半

- **第一次**：用户「能不能在后缀上标好自己的模型名啊」。我先只改了 `annotator` 字段、保留文件名，
  理由是实测到 `judgeB` 这个后缀已被别的产出者按精确路径引用，改名会打断别人的脚本。
- **第二次**：用户「全改，文件名也要」，并在我明示「得连 judgeC 那个对照脚本一起改——那是别人的文件，
  我要你一句话再动」之后给出授权。据此**文件名也改了**，并对外部引用做了最小必要修补。

### 13.2 最终命名

| 项 | 值 |
|---|---|
| 文件名 | `B2-E4-adjudication-judgeB-qwen-3.8max.{jsonl,csv,md}` ＋ `…-qwen-3.8max-stats.json` |
| `annotator` | `ai:qwen-3.8max(L4-control,judgeB,single-rater,no-kappa)` |
| 模型名出处 | **用户 2026-10-10 指定**；本 agent 不自证型号，故报告抬头与本节都注明是用户给的名字 |
| 为什么保留 `judgeB` | 它是本工作区的裁判编号（judgeA=`Otto`、judgeC=`ai:deepseek-v4.1-flash`），别的产出者按此编号引用本件；丢掉它会让引用无处对齐 |
| 为什么对齐 `ai:<model>` 前缀 | judgeC 已用该写法，统一后三裁判的 `annotator` 可机器解析 |

`.jsonl` 的 100 条记录与 `.csv` 的 100 行**每一行都带** `annotator`，覆盖面大于文件名后缀本身。

### 13.3 改名的爆炸半径（先量后动）

动手前实测了 `judgeB` 在他人文件里的引用形态，结论是**功能性引用只有 1 处**：

| 文件 | 引用形态 | 处置 |
|---|---|---|
| `_xjudge_compare_judgeC.py:90` | `load_jsonl(os.path.join(exp, "B2-E4-adjudication-judgeB.jsonl"))` —— **精确路径，改名即崩** | 已改（见 13.4） |
| `_xjudge_compare_judgeC.py:117/132` | 显示标签 `judgeB(qoder)`、输出表里的旧 annotator 与旧路径 | 已改（同一次编辑） |
| `_xjudge_compare_judgeC.py:9/10/16` | 文档串里的历史叙述 | **未改**（历史记录） |
| `B2-E4-adjudication-PROVENANCE-NOTE.md`（15 处） | 事故记录，叙述"judgeB 用了 -judgeB 后缀" | **未改**（改它等于篡改事故记录） |
| `B2-E4-adjudication-judgeC-crosscheck.md`（10 处） | 事后对照报告 | **未改**（历史） |
| `_restore_judgeA_names.py`（7 处） | 引用 `_build_judgeB.py:12` 与 `_audit_judgeB.py:152-156` 作为**证据行号** | **未改**，且据此**没有**给这两个工具脚本改名——改了会让别人的引证指向不存在的文件 |
| `B2-E4-adjudication.md`（6 处） | judgeC 留的墓碑 | **未改** |

同时实测**没有**正在运行的 python/node 进程持有这些路径（按 Name 白名单查询，未按命令行模式匹配以免误伤自身）。

### 13.4 对他人文件的那一次编辑（授权、备份、语法门、回滚、往返证明）

被改的文件：`EXP/_xjudge_compare_judgeC.py`（judgeC 所有）。做法：

1. **先备份**：`_xjudge_compare_judgeC.py.judgeB-edit-backup`（12720 B，sha256 `64af782a3ecb4ed8…`）。
2. **4 处字符串替换**：读取路径、显示标签、输出表里的 annotator、输出表里的路径通配。
3. **3 行独立注释**插在 `load_jsonl` 调用上方，写明改动者、日期、原因与备份文件名。
4. **语法门**：写入前 `ast.parse` 通过才落盘；写入后**重新读盘**再 `ast.parse` 一次（写入回执≠落盘）。
5. **往返证明**：把写好的文件按相反顺序撤销我这 4 处替换并删掉 3 行注释，结果与备份**逐字节相等**——
   即我确实只动了这 7 行，别的行一个字节没碰。

**一次自伤，如实记录**：第一次尝试把标记写成**行内注释**追加到 `("judgeB(qoder)", b)` 后面，
而那一行是列表字面量的中间一项，注释把同行的 `, ("judgeC(dsh)", c)]` 一起吃掉，
`ast.parse` 报 `'[' was never closed (line 117)`。语法门当场拦下并**从备份自动回滚**（实测回滚后与备份 sha 相等），
没有留下半成品。止法：标记一律独占一行，绝不追加到多项目表达式的中间。

### 13.5 证明改名与改标都没有动判定内容

| 环节 | 证据 |
|---|---|
| 改 `annotator`（第一次裁决） | `_retag_judgeB.py` / `.stdout`：100 条 × 17 个判定字段逐格比对，**漂移 0 处**；truth 分布改前改后同为 `0=75 / None=14 / 1=11` |
| 改文件名（第二次裁决） | `_rename_to_model_tag.py` / `.stdout`：新旧 `.jsonl`/`.csv`/`-stats.json` **sha256 逐一相等**（`aa68ef38…` / `77c76cff…` / `5365b100…`），即改名是纯路径操作、内容零变化；**先证等值再删旧名**，未证等值就拒绝删除 |
| 改前状态存档 | `B2-E4-adjudication-judgeB.pretag.{jsonl,csv,md}` ＋ `.pretag-stats.json` 四件全部保留，一件未删 |
| 密封件 | `B2-E4-modelside.{jsonl,-SEAL.md,-stats.json}` 三件 size 与 mtime 在每一步之后都重新实测未变 |
| 全量复核 | `_audit_judgeB.py` / `.stdout`：改完重跑，AUDIT PASS |

改名后交付件 sha256：`.jsonl` `aa68ef385b137dc0…`、`.csv` `77c76cff1b6125c1…`、`-stats.json` `5365b100f1d69809…`。

### 13.6 工作区现状（三裁判 + 第四条线，本节只登记不主张）

- **judgeA**（`L4-control:Otto(single-rater,no-kappa)`）：分布 `0/1/None = 88/2/10`。
  08:52:37 被 judgeC 就地覆盖了 `B2-E4-adjudication.jsonl`/`.md` 与其填过的 `B2-E4-sample.csv`；
  但 `B2-E4-adjudication.csv`（33927 B）始终未被动过，100 条判定可从中恢复。judgeC 已于 09:1x 同源重建并留墓碑。
- **judgeB**（本件）：`75/11/14`。四件产物经 sha 复核全程未被动过。
- **judgeC**（`ai:deepseek-v4.1-flash`）：`96/4/0`。判定冻结于 02:15:20 的 `.src.jsonl`，落盘在 08:52:37。
- 另有 `EXP/多agent判断/`（`B2-E4_预标_评估器A_v2_*`，09:18）一条线，本会话未读其内容。
- judgeC 事后算的两两一致率（其 `-crosscheck.md`，**明标 post-hoc**）：A-C 88%、A-B 77%、B-C 73%，31/100 单元有分歧。
  按用户裁决「不用管他，写你自己的，相互对照」，**本件不采信、不重算、不合并这些数字**，仅登记其存在。

### 13.7 污染披露：我意外读到了 judgeC 的脚本全文（含其对 judgeA 的转述）

`_fix_foreign_ref.py` 的往返证明用了 `chk(label, got, want)`，而该函数在**不相等时会把两个值整串打印**；
这次它相等（PASS），但打印语句仍把 `got` 与 `want` 各输出了一遍——于是 judgeC 那 12 KB 脚本的全文
（含它写进 crosscheck 的叙述）进了我的上下文，落在 `_fix_foreign_ref.stdout` 里。这是我自己的仪器噪音造成的，
不是主动去读。因此我现在知道两件本不该在冻结后知道的事：

1. **judgeA 在 #4 `compile_file` 上的机理**：`optimize=[]` 且 `force=True` 时第 245 行的 for 体零次执行，
   导致第 277 行 `if ok == 0` 引用未绑定变量而抛 `UnboundLocalError`，且 judgeA 附了实测。
2. **judgeA 的证据基超出了工作簿所示上下文**——#4 在工作簿里只给了 60/148 行（41%），
   第 245/277 行都在隐藏段里。这**回答了 §10 留下的那个开放问题**：至少 judgeA 是去读了未截断的真源码。

**处置（纪律优先于收获）**：本件对 **#4 的读数不改**，仍是 `None` / `RGAP-trunc`。理由是
`RULE.md:3-4`「规则先于判定，不可事后调整」，以及事后按别人的答案改判会把对照尺污染成"看过答案的尺子"
——judgeC 对同一个诱惑也采取了不改判的处置。我在此登记这次污染，让后来者知道：
本件的 100 条读数**冻结于 02:36:10（`_adj_batch2.json`）**，早于我见到 judgeC 脚本的时刻；
`_retag`/`_rename`/`_propagate`/`_fix_foreign_ref` 四步都已逐字段证明未动任何判定字段。
**若用户希望把 judgeA 的 #4 机理纳入，正确做法是开第二批 n=100（`PREREG` B4 的终局批），而不是回填这一批。**

顺带一条对本件自身口径的影响，也在此登记而不回填：既然已知有裁判会去读未截断的真源码，
那么本件 §8.2 的"9 个截断单元里 4 个记 rule_gap"就**不是**所有裁判的共同口径，
三裁判的 None 率之差（judgeA 10 / judgeB 14 / judgeC 0）里有一部分来自**证据范围不同**，
而不是"谁更保守"。比较三裁判时必须把这一层分开说，否则会把口径差读成可靠性差。
