# E-B2-4 模型侧对照标注 · 密封件（混合框 100 单元）

> **落盘**：2026-10-10 01:53 ｜ **裁判**：模型侧（AI），单裁判 ｜ **靶**：Python 安装件 `Lib`（混合框）
> **协议**：`PREREG/B2.md` 判据锁定附录 **v1.5** §A1 / §A4 / §A5 / §B2 / §B3 / §C
> **判定规则**：`EXP/B2-E4-RULE.md`（规则先于判定落盘，全程未改）

---

## 0. 这份件是什么，不是什么

**授权原话**（用户，2026-10-10）：

> 「别管他妈那么多，根本不存在真值，你全权负责裁判，作为其他成果的对照」

据此 L4 由 `PREREG/B2.md:45` 的「唯一人工层」改定性为**机器对照层**。

| 是 | 不是 |
|---|---|
| 模型侧对 100 单元的三分类（1/0/None）标注 + Wilson 读数 + SHA256 密封 | **不是** E-B2-4 完成——E-B2-4 需要第二名标注者才能起算 α |
| v1.5 §A5 意义上的「模型侧读数」，供人工裁定冻结后解封比对 | **不是**金标——不写入 `topos/calib/gold.py`（那是 `WORK-ORDERS.md:106` 禁止令的字面对象） |
| 各信号源（锚点池/曲率池/零覆盖）的**共同对照尺** | **不是**真实精度——`PREREG:75` 的「仪器灵敏度」限定继续有效 |
| 分层间缺陷率差的**相对**读数 | **不是**折扣系数——折扣公开集需要人际一致率，机器对照给不出该量 |

**单裁判的硬限制**：Krippendorff α / Gwet AC1 / Cohen κ **均需 ≥2 名标注者**。本件只有模型侧一方 ⇒ **v1.5 §B 全部判据不可起算**，不是「过了」也不是「废了」，是**尚未开始**。

---

## 1. 密封（v1.5 §A5）

| 项 | 值 |
|---|---|
| 密封物 | `EXP/B2-E4-modelside.jsonl` |
| SHA256 | `8147293be49351e7a37dbf63b21ec4d0f578d56a3564ea06eb0e5fccd091fb04` |
| 字节数 | 33046 |
| 密封时刻 | 2026-10-10T01:53:20+0800 |
| 派生读数 | `EXP/B2-E4-modelside-stats.json`（由 `EXP/make_b2_e4_modelside_stats.py` 可复算，非密封物） |
| 判定所依据的清单 | `EXP/B2-E4-sample-mixed.csv`（从 `bd3144a` 恢复，见 §7） |
| 判定所依据的工作簿 | `EXP/B2-E4-workbook-mixed.md`（并发会话改名保留，未被覆盖） |

§A5 要求「无哈希记录的密封不具证据力」——本件即该哈希记录。**解封条件**：人工裁定冻结后。

---

## 2. 读数（Wilson score，v1.5 §C 禁用 Wald）

### 2.1 全池（§B3：只作参考，**禁止配额加权合成**）

| 口径 | k/n | 点估计 | Wilson 半宽 | 95% 区间 |
|---|---|---|---|---|
| 硬口（剔 None） | 3/96 | 0.0493 | ±0.0386 | [0.0107, 0.0879] |
| 全口（None 作第三类） | 3/100 | 0.0474 | ±0.0371 | [0.0103, 0.0845] |
| None 率 | 4/100 | 0.0570 | ±0.0414 | — |

三态互斥且相加等于分母：3 + 93 + 4 = 100 ✓（脚本内 `assert` 强制，不等即中止）

### 2.2 层内（§B3：**主判读**）

| 层 | n | 1 | 0 | None | 硬口 k/n | 硬口点估计 | Wilson 95% | None 率 | >40%？ |
|---|---|---|---|---|---|---|---|---|---|
| `anchor` | 25 | 1 | 24 | 0 | 1/25 | 0.1013 | [0.0071, 0.1954] | 0/25 | 否 |
| `random` | 30 | 1 | 28 | 1 | 1/29 | 0.0889 | [0.0061, 0.1718] | 1/30 | 否 |
| `confluence` | 20 | 1 | 17 | 2 | 1/18 | 0.1337 | [0.0099, 0.2576] | 2/20 | 否 |
| `zero_cover` | 25 | 0 | 24 | 1 | 0/24 | 0.0690 | [0.0000, 0.1380] | 1/25 | 否 |

四层配额与 `QUOTA`（25/25/20/30）逐项相符（脚本 `quota_match` 全 true）。
**没有任何一层 None 率 >40%**，故 §B2 的「可判性不足」条款本次不触发。

> Wilson 在 k=0 时点估计不为 0（`anchor` 的 None 率 0/25 → 0.0666、`zero_cover` 的硬口 0/24 → 0.0690 都是收缩后的中心），**读 k/n 列，不要读点估计列判有无**。

### 2.3 按来源（混合框特有，纯 stdlib 新样本无此栏）

| 来源 | n | 1 | 0 | None | 硬口点估计 | Wilson 95% |
|---|---|---|---|---|---|---|
| stdlib | 71 | 3 | 67 | 1 | 0.0666 | [0.0147, 0.1186] |
| site-packages | 29 | 0 | 26 | 3 | 0.0644 | [0.0000, 0.1287] |

自然权（用 `B2-E4-framecheck.json` 的真实框构成 stdlib 0.7255 / site-packages 0.2745，**非配额权**）：
硬口 0.0660 ｜ 全口 0.0638 ｜ None 率 0.0694。
（此三值是两层 Wilson 中心的加权平均，仅作对照，不带自己的区间。）

### 2.4 与 v1.5 §C「诚实宽度」表的对照

§C 预估「n=100 下比例 CI 半宽 ±7~10 点」。**实测全池硬口半宽 ±3.9 点、层内 ±6.9~12.4 点**——全池比预估窄（因为 k=3 极小，Wilson 在低患病率下收窄），层内与预估一致。这不是好消息：窄是因为**分子太小**，不是精度 high。

---

## 3. A1 序约束（软判定，v1.5 §A4）

期望 `π(anchor) > π(random) > π(zero_cover)`。

| 相邻对 | 实测 | 违反幅度 | Wilson 区间是否重叠 |
|---|---|---|---|
| anchor vs random | 0.1013 > 0.0889 | 无违反 | **重叠** [0.0071,0.1954] ∩ [0.0061,0.1718] |
| random vs zero_cover | 0.0889 > 0.0690 | 无违反 | **重叠** [0.0061,0.1718] ∩ [0.0000,0.1380] |

**裁定**：序约束**满足**，但两对相邻区间**全部重叠** ⇒ 定向由抽样噪声决定，**不具证据力**。
按 §A4 如实记幅度 = 0（无违反），但同时记「满足」这个结论本身不可用作镜像解的破法依据。
三层的分子分别是 1 / 1 / 0 —— 在这个量级上谈序关系等于谈噪声。

---

## 4. 判 `1` 的三条（每条带机理与复现）

### #42 `email/contentmanager.py::_encode_base64:136` — logic/boundary，**实测复现**

`unencoded_bytes_per_line = max_line_length // 4 * 3`（`:138`）在 `max_line_length ∈ {None, 0, 1, 2, 3}` 时失效。

两条独立触发路径（本机实测输出）：

```
email.policy.HTTP（stdlib 公开策略，policy.py:231 设 max_line_length=None）
  → EmailMessage.set_content(b'...') 抛 TypeError:
    unsupported operand type(s) for //: 'NoneType' and 'int'

email.policy.default.clone(max_line_length=0)
  → 抛 ValueError: range() arg 3 must not be zero
```

复现：

```python
import email.policy
from email.message import EmailMessage
for pol in (email.policy.HTTP, email.policy.default.clone(max_line_length=0)):
    m = EmailMessage(policy=pol)
    m.set_content(b'\x00\x01\x02', maintype='application', subtype='octet-stream')
```

**根因是调用点不对称**：`contentmanager.py:237` 直传 `msg.policy.max_line_length` 无保护；
同文件 `:147` 的另一调用点有 `maxlen = policy.max_line_length or sys.maxsize`，
且 `:146` 注释明写「If max_line_length is 0 or None, there is no limit」。
⇒ **同一契约在一个调用点被遵守、在另一个被违反**。实测 `max_line_length=4/78` 正常。

### #43 `email/encoders.py::encode_7or8bit:47` — logic，**实测复现**

docstring 写「**Set** the Content-Transfer-Encoding header to 7bit or 8bit」，
但 `msg['Content-Transfer-Encoding'] = ...` 在 `email.message.Message` 上是**追加**而非替换。

```
调用前 CTE 头数: 1
调用后 CTE 头数: 2   ['base64', '7bit']
```

RFC 5322 要求 CTE 在一个 body part 中至多出现一次。`Message.replace_header` 正是为此存在。
注：同模块 `encode_base64` / `encode_quopri` 有同族写法 ⇒ 这是**模块级一致的设计缺陷**，
但本单元的行为确实偏离**其自身文档串**，按 `B2-E4-RULE.md` 的 `1` 判据成立。

### #92 `xml/dom/xmlbuilder.py::DOMBuilder.parse:187` — resource_leak，源码级证实

`fp = urllib.request.urlopen(input.systemId)`（工作簿标 L8，即 `xmlbuilder.py:194`）
打开的流在**任何路径上都不被关闭**：

- 本函数无 `close()` / `with`；
- `_parse_bytestream` 只做 `builder.parseFile(stream)` 后 `return`；
- 实测 `expatbuilder.ExpatBuilder.parseFile` 源码为 `while buffer := file.read(16*1024)` 循环后直接 `return doc`，同样无 `close`。

`byteStream` 分支由调用方持有、不关是正确的；但 `urlopen` 得到的流**由本函数持有**
⇒ 每次以 systemId 解析都泄漏一个 HTTP 连接直到 GC。
对照：同文件 `DOMEntityResolver.resolveEntity` 用 `self._get_opener().open(systemId)`，走的是可管理的 opener。

---

## 5. 判 `None` 的四条（形态码见 `B2-E4-RULE.md`）

| seq | 单元 | 码 | 为什么判不出来 |
|---|---|---|---|
| 64 | `pip/.../package_finder.py::LinkEvaluator.get_version_sort_key:283` | N-CTX | `if s.isdigit()` 静默丢非数字段 ⇒ `'1.0.0rc1'` 与 `'1.0.0'` 同键 `(1,0,0)`；是否成缺陷取决于调用方 `evaluate_link`（跨文件未扫描）对并列键的容忍度 |
| 77 | `pip/_vendor/idna/core.py::check_bidi:70` | N-CTX | 补读截断尾部后 rule 2–6 与 RFC 5893 对应；但 rule 1 用 `label[0]`，空 label + `check_ltr=True` 时抛 IndexError 而非 IDNABidiError——该路径可达性取决于 `check_label`（跨文件未扫描） |
| 83 | `pip/_vendor/pygments/lexers/__init__.py::guess_lexer:304` | N-CTX | `rv > best_lexer[0]` 在任一 lexer 的 `analyse_text` 返回 None 时抛 TypeError；可达性取决于注册的 lexer 集合（跨包未扫描） |
| 96 | `zoneinfo/_zoneinfo.py::ZoneInfo.dst:112` | N-CTX | 读 `_find_trans` 源码：`dt is None` 返回 `_NO_TTINFO` ⇒ `dst(None)` 给 timedelta 而非 tzinfo 契约的 TypeError；是否成缺陷取决于「纯 Python 回退须与 C 实现行为一致」这条契约，而它不在所示上下文内 |

**一条被环境缺项挡住的验证（如实报，不猜）**：#96 原拟实测 C 实现与纯 Python 回退对 `None` 的分歧，
被 `ZoneInfoNotFoundError: No time zone found with key UTC` 挡住——**本机无 tzdata**。
按 `agents.md` R-1 的口径，这是环境缺项，记为验证受阻而非「无缺陷」。

---

## 6. 工作簿交付形态缺陷（与判定独立，影响下一批）

| # | 缺陷 | 证据 | 后果 |
|---|---|---|---|
| D1 | 长函数**静默截断** | `MAX_SRC_LINES = 60`（`make_b2_e4_sample.py:30`）；6/100 节带「已截断」标记，`loc>60` 的 6 个单元全中 | 裁判必须自行回盘读尾部。本次 6 条全部补读，其中 #38 `namedtuple` 的关键 `eval` 段就在被截掉的部分 |
| D2 | 「本函数调用」列 `calls[:12]` **静默截断**，无省略号无计数 | `:133`；#7 `inspect.getfile` 的列表恰好 12 项，源码里实际调用的 `istraceback` 排第 13 位被吃掉 | 裁判可能误判「该名字未定义/未调用」。按字母序截断 ⇒ 被吃掉的恒定是字母序靠后的那批，**不是随机缺失** |
| D3 | 「同文件调用者」列 `callers[:8]` 同样静默截断 | `:136`；#18 恰好 8 项 | 同 D2 |
| D4 | 截断提示只给「完整见 `file:line`」，不给应读到第几行 | `:144` | 裁判要自己算 `lineno + loc - 1` |

**提交信息与产物的口径差**：`df80ded` 声称工作簿「每节：**完整源码**+…」，实际 6/100 节截断。

---

## 7. 抽样框缺陷（`B2-E4-framecheck.json` 实测）

| # | 缺陷 | 实测 | 状态 |
|---|---|---|---|
| F1 | 扫描根含 `site-packages`，但工作簿标题写死「靶仓：Python 标准库」 | 全框 18198 单元中 site-packages **4995（27.45%）**，全是 pip（`pip/_vendor` 3419 + `pip/_internal` 1573）；标题字符串在 `:156` 硬编码，非从扫描结果推导 | **已被并发会话修复**（`9273432`：排除 site-packages，纯 stdlib 框 13203，混合版保留为 `-mixed`）。我的 framecheck 读数与他们独立重生成后的「零覆盖 97.6%／抽样框 13203」一致 |
| F2 | **靶是符号链接，指向别的工具管理的活目录** | `versions/3.13.12` → `AppData/Local/Programs/WorkBuddy/resources/vendor/python/`；该解释器自报 **3.13.14**，不是 3.13.12 | **未修**：新工作簿头部仍写「靶仓：Python **3.13.12** 标准库」。抽样框既贴错版本标签，又随时可被 WorkBuddy 升级 ⇒ **框不可冻结，样本不可复现** |
| F3 | README 的零覆盖分子**无凭据** | `README:24` 写「零覆盖 97.8%（**17791**/18198）」；生成器的 `print` 只输出百分比（旧 `:170`、新 `:183`），从不输出分子；我用与生成器逐字相同的算式现量得 **17798**/18198 | **未修**：README 未随 F1 更新，`README:10` 仍写「N=18198」，而 18198 现在是**混合框**的数（纯 stdlib 框是 13203）；`README:37` 仍描述旧的人工仲裁流程（「你只裁分歧样本…~8 小时」），与 v1.5 的 α 协议不一致 |

F2 是三条里最重的：**E-B2-4 的样本无法被第二个人复现**，因为靶不是一个冻结的树，
而是一个别的程序会就地升级的目录，且路径名与内容版本已经不符。

---

## 8. 并发碰撞（口径节）

同一个 `EXP/` 目录在本批作业期间有**两个互不知情的产出者**。时间线（均为本机实测时刻）：

| 时刻 | 事件 | 归属 |
|---|---|---|
| 01:17:33 | `df80ded` 提交混合框工作簿 | 另一会话 |
| 01:21 | `EXP.7z` 打包（内含混合框四件） | 另一会话 |
| ~01:25 | 用户把 `EXP.7z` 交给我，令「判！」 | 用户 |
| 01:33:49 | 我落 `B2-E4-RULE.md`（判定规则先于判定） | 我 |
| 01:35:18 | 我落 `make_b2_e4_framecheck.py` | 我 |
| 01:38:10 | `bd3144a` 提交 PREREG v1.5，**并把我未提交的 RULE.md / framecheck.py / EXP.7z 一起扫进提交**，同时扫进 `__pycache__/*.cpython-314.pyc` 十余件 | 另一会话 |
| 01:39 | 我的 framecheck 跑出 `B2-E4-framecheck.json` | 我 |
| 01:43–01:44 | 另一会话改 `make_b2_e4_sample.py`（排除 site-packages）、把工作簿改名为 `-mixed` | 另一会话 |
| 01:47:31 | **`B2-E4-sample.csv` 被原地覆盖**为纯 stdlib 新样本 | 另一会话 |
| 01:48:36 | 新 `B2-E4-workbook.md` 生成（132363 字节） | 另一会话 |
| 01:49:01 | `9273432` 提交上述全部 | 另一会话 |
| 01:53:20 | 我密封模型侧读数 | 我 |

**后果与处置**：

1. 我裁的 100 单元是**混合框**那批，其清单已被原地覆盖。已从 `bd3144a` 恢复为
   `EXP/B2-E4-sample-mixed.csv`（**新文件，未覆盖任何现存产物**），判定按 `seq` 对齐并逐条交叉核对
   `unit_id`——发现并修正 1 处我自己的转写错（seq 30 漏了类名限定 `BaseEventLoop.`，单元本身是同一个）。
2. 新旧样本**交集仅 29**，⇒ 新的纯 stdlib 样本有 **72 单元未经模型侧裁判**。本件不覆盖它们。
3. `.gitignore` 没有 `__pycache__` 条目（全文只有 `reference/*` 与 `exp-out/`），
   所以 `bd3144a` 才会把 `.pyc` 提交进库。其中 `cpython-314` 的 `.pyc` 有可能来自我的
   `py -X utf8` 导入探针（本机 `py` 解析到 Python 3.14）——**这份足迹可能是我留的，如实报**。
4. 我**没有**运行被修改过的生成器（它会原地覆盖 CSV/workbook），也**没有** stage 或提交任何文件；
   `git status` 里那个 staged 改名不是我的改动，我未触碰。

---

## 9. 复现

```bash
cd topos-audit
P="C:/Users/26672/.workbuddy/binaries/python/versions/3.13.12/python.exe"

# 判定规则（先于判定落盘）
cat EXP/B2-E4-RULE.md

# 100 条判定原始数据（密封物）
sha256sum EXP/B2-E4-modelside.jsonl   # 应为 8147293b...91fb04

# 读数复算（Wilson / 三态 / 序约束 / 密封）
PYTHONUTF8=1 "$P" -X utf8 EXP/make_b2_e4_modelside_stats.py

# 抽样框构成复算
PYTHONUTF8=1 "$P" -X utf8 EXP/make_b2_e4_framecheck.py

# 三条缺陷的实测复现见 §4（#42 / #43 可直接跑，#92 为源码级证实）
```

---

## 10. 未做 / 待裁

| 项 | 状态 |
|---|---|
| 新纯 stdlib 样本（`9273432`）的模型侧标注 | **未做**——72 单元待裁。要不要做请明示：靶仍在漂（F2 未修），现在标可能再被覆盖一次 |
| v1.5 §A5 的「用户侧」密封读数 | 不在我职权内——§A5 写明由**用户**在仲裁开始前落盘 |
| Krippendorff α / Gwet AC1 / Cohen κ | **不可计算**（单裁判）。需第二名标注者 |
| §B4 双阶段作废判定 | **未触发**——第一批 α 都还没起算 |
| E-B2-4 回执 `EXP/B2-E4.md` | **未写**。本件是模型侧密封件，不是实验回执；回执应在人工侧就位、α 可算之后再落 |
| `topos/calib/gold.py` 的 `annotator` 校验 | **未加**（`gold.py:24` 仍是自由文本、默认 `""`、零校验；`selftest.py` 对 gold/L4/annotator 零引用）。这是 W8 禁止令目前只停在强制力阶梯第⑤级的原因。**不自行改**——按 `agents.md` R-2 与被门管者不得自行放宽/收紧门的原则，交由该仓所有者裁决 |
| F2 / F3 | **未修**——不在我被授权的范围内（我受命裁判，不受命改别人的抽样框与 README） |
