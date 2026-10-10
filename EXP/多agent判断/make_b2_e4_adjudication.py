# -*- coding: utf-8 -*-
"""EXP/make_b2_e4_adjudication.py —— 把 L4-control 判定源派生成三件产物。

输入（本仓内）：
  EXP/B2-E4-adjudication.src.jsonl   判定源（每条一行，仅含 seq + 判定字段）
  EXP/B2-E4-sample.csv               抽样清单（生成器产物；只读其前 17 列）

输出（EXP/ 下）：
  B2-E4-adjudication.jsonl   自足版判定（补 unit_id/file/name/lineno/loc/stratum）
  B2-E4-sample.csv           回写版：truth/defect_type/annotator/date + 追加 note 列
  B2-E4-adjudication.md      人读回执（分布 / 分层 Wilson CI / 口径 / 限制）

纪律：
  - 不改 RULE.md / workbook / mixed 版 / 生成器 / topos/calib/gold.py（本层不是金标）。
  - CSV 原 17 列顺序逐字保持，仅在**末尾追加** note 列；source_layer 由生成器写的
    L4-reference 改为 RULE.md 重新定性后的 L4-control（此单字段改写已在 md 里披露）。
"""
import csv
import json
import os
import sys
from collections import Counter

ANNOTATOR = "ai:deepseek-v4.1-flash"
DATE = "2026-10-10"          # 与本材料包时钟一致（RULE.md 授权出处标注为 2026-10-10）
SOURCE_LAYER_IN = "L4-reference"   # 生成器写入值（保留用于披露）
SOURCE_LAYER_OUT = "L4-control"    # RULE.md 重新定性后的层名
Z = 1.959963985


def wilson(k, n, z=Z):
    """Wilson score 区间（PREREG/B2.md v1.5 §C：比例禁用 Wald）。"""
    if n <= 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def load_src(path):
    rows = {}
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit("src jsonl 第 %d 行不是合法 JSON: %s" % (ln, e))
            s = o["seq"]
            if s in rows:
                raise SystemExit("src jsonl 撞号: seq=%s" % s)
            if o.get("truth") not in ("0", "1", "None"):
                raise SystemExit("seq=%s truth 非法: %r" % (s, o.get("truth")))
            if not o.get("rule"):
                raise SystemExit("seq=%s 缺 rule 字段（RULE.md 纪律#5 要求）" % s)
            rows[s] = o
    return rows


def guard_generic(paths):
    """安全联锁（2026-10-10 事故后加）：通用名 B2-E4-adjudication.* / B2-E4-sample.csv
    若已被**别的裁判**的内容占住（judgeA 的 Otto 填版 / judgeA 的同源重建版），
    默认拒绝覆盖——judgeC 曾在 08:52:37 就地截断过 judgeA 的这两个文件。
    确要覆盖时显式加 --force。"""
    if "--force" in sys.argv:
        return
    for p in paths:
        if not os.path.exists(p):
            continue
        if p.endswith(".jsonl"):
            head = open(p, encoding="utf-8").read(8000)
            if "reconstructed_by" in head:
                raise SystemExit(
                    "拒绝覆盖 %s：它是他人（judgeA）内容的同源重建版。\n"
                    "  judgeC 的产物请写自己的名字（B2-E4-adjudication-judgeC.*）；\n"
                    "  确要覆盖通用名请显式加 --force。" % p)
        elif p.endswith(".csv"):
            with open(p, encoding="utf-8-sig", newline="") as f:
                first = next(csv.DictReader(f), None)
            if first and str(first.get("annotator", "")).startswith("L4-control:Otto"):
                raise SystemExit(
                    "拒绝覆盖 %s：其 annotator 是 judgeA（L4-control:Otto）。\n"
                    "  确要覆盖通用名请显式加 --force。" % p)


def main():
    if len(sys.argv) < 2:
        print("用法: make_b2_e4_adjudication.py <repo_root> [src_jsonl]")
        return 2
    root = os.path.abspath(sys.argv[1])
    exp = os.path.join(root, "EXP")
    src = sys.argv[2] if len(sys.argv) > 2 else os.path.join(exp, "B2-E4-adjudication.src.jsonl")
    sample = os.path.join(exp, "B2-E4-sample.csv")

    judge = load_src(src)
    # 实测：生成器源码写的是 encoding="utf-8"（无 BOM），但在盘上的 B2-E4-sample.csv
    # 带 UTF-8 BOM（EF BB BF）——产物与脚本不一致。读用 utf-8-sig 兼容两态；
    # 写回沿用 utf-8-sig：note 列含中文，去掉 BOM 会让 zh-CN 下的 Excel 误判编码。
    with open(sample, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        cols = list(rd.fieldnames)
        srows = list(rd)
    # 生成器产物的原始列序（不含 note）
    if cols[-1] == "note":
        cols = cols[:-1]

    missing = [r["seq"] for r in srows if int(r["seq"]) not in judge]
    extra = sorted(set(judge) - {int(r["seq"]) for r in srows})
    if missing or extra:
        raise SystemExit("判定与抽样清单不匹配：缺 %s / 多 %s" % (missing[:5], extra[:5]))

    # 安全联锁：不许再覆盖他人占住的通用名（2026-10-10 事故的教训）
    guard_generic([os.path.join(exp, "B2-E4-adjudication.jsonl"),
                   os.path.join(exp, "B2-E4-adjudication.md"),
                   sample])

    # ---------- ① 自足版 jsonl ----------
    out_jsonl = os.path.join(exp, "B2-E4-adjudication.jsonl")
    lines = []
    for r in srows:
        j = judge[int(r["seq"])]
        rec = {
            "seq": int(r["seq"]),
            "unit_id": r["unit_id"],
            "file": r["file"],
            "name": r["name"],
            "lineno": r["lineno"],
            "loc": r["loc"],
            "stratum": r["stratum"],
            "truth": j["truth"],
            "defect_type": j.get("defect_type", ""),
            "rule": j["rule"],
            "confidence": j.get("confidence", ""),
            "evidence_scope": j.get("evidence_scope", ""),
            "note": j["note"],
            "annotator": ANNOTATOR,
            "date": DATE,
            "source_layer": SOURCE_LAYER_OUT,
            "not_gold": True,
        }
        lines.append(json.dumps(rec, ensure_ascii=False))
    with open(out_jsonl, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    # ---------- ② 回写 CSV ----------
    out_csv = sample
    note_col = "note"
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols + [note_col])
        w.writeheader()
        for r in srows:
            j = judge[int(r["seq"])]
            r["truth"] = j["truth"]
            r["defect_type"] = j.get("defect_type", "")
            r["annotator"] = ANNOTATOR
            r["date"] = DATE
            r["source_layer"] = SOURCE_LAYER_OUT
            r[note_col] = j["note"]
            w.writerow({k: r[k] for k in cols + [note_col]})

    # ---------- ③ 人读回执 ----------
    n = len(srows)
    truth = Counter(judge[int(r["seq"])]["truth"] for r in srows)
    strata = sorted({r["stratum"] for r in srows})
    ones = [r for r in srows if judge[int(r["seq"])]["truth"] == "1"]

    L = []
    A = L.append
    A("# E-B2-4 L4-control 判定回执（100 单元）")
    A("")
    A("> **这是什么**：按 `EXP/B2-E4-RULE.md` 产出的**机器对照层（L4-control）**读数，")
    A("> 不是金标、不是真值。落点 `EXP/B2-E4-adjudication.*`，**未写入** `topos/calib/gold.py`")
    A("> （`WORK-ORDERS.md:106` 禁止令的对象）。")
    A("> **裁判**：`%s`（机器）｜ **日期**：`%s` ｜ **靶仓**：标准库树 `binaries\\python\\versions\\3.13.12\\Lib`（目录标签 3.13.12；同目录 `python.exe` 自报 3.13.14，见 §7）" % (ANNOTATOR, DATE))
    A("> **规则先于判定**：判定口径全部来自 `B2-E4-RULE.md`（三值 + None 四形态），本回执不改规则。")
    A("")
    A("## 1. 分布")
    A("")
    A("| truth | 计数 | 占比 | Wilson 95% CI |")
    A("|---|---:|---:|---|")
    for t in ("1", "0", "None"):
        k = truth.get(t, 0)
        p, lo, hi = wilson(k, n)
        A("| `%s` | %d | %.1f%% | [%.1f%%, %.1f%%] |" % (t, k, 100 * p, 100 * lo, 100 * hi))
    A("")
    A("### 分层 1 率（设计变量分层，报告层内读数）")
    A("")
    A("| 层 | n | 1 数 | 层内 1 率 | Wilson 95% CI |")
    A("|---|---:|---:|---:|---|")
    for s in strata:
        rs = [r for r in srows if r["stratum"] == s]
        k = sum(1 for r in rs if judge[int(r["seq"])]["truth"] == "1")
        p, lo, hi = wilson(k, len(rs))
        A("| `%s` | %d | %d | %.2f%% | [%.2f%%, %.2f%%] |" % (s, len(rs), k, 100 * p, 100 * lo, 100 * hi))
    A("")
    A("**A1 序约束（`PREREG/B2.md` v1.5 §A：pi(anchor) > pi(random) > pi(zero_cover)）在本层不成立。**")
    A("四层各只有 1 条 `1`：这是**并列**，不是序。分层 n=20~30 时层内 1 率的 Wilson 半宽约 ±7~9 个点，")
    A("而四层的点估计彼此相差 <2 个点 ⇒ 本层读数对该序约束**零分辨力**。")
    A("据此：**不能把 L4-control 当作 A1 的支撑来源**；A1 若要成立，须由别的证据（自然层权下的大样本、")
    A("或 L1 执行正样本侧）提供。此条按 §A4「如实记录违反幅度」登记，且不足以判定「定向由约束边界决定」。")
    A("")
    A("**旁证（E-X1 教训的又一次实测）**：`zero_cover` 层 25 条里确认了 1 条缺陷（#18 `netrc._parse`）。")
    A("即「不在任何池内」不等于「干净」—— 盲区里的缺陷正是池式信号源结构上检不到的那一类。")
    A("注意这条是判定的**副产品**，不是定向搜索的结果；样本量只有 1，不足以估盲区缺陷率。")
    A("")
    A("## 2. None 的四形态（计数）")
    A("")
    A("| 码 | 形态 | 计数 |")
    A("|---|---|---:|")
    for code, what in (("N-CTX", "跨文件语义缺失"), ("N-INV", "依赖未记录不变量"),
                       ("N-SHIM", "壳/转发单元"), ("N-VER", "版本敏感")):
        c = sum(1 for r in srows if judge[int(r["seq"])]["rule"] == code)
        A("| `%s` | %s | %d |" % (code, what, c))
    A("")
    A("**None 率 = 0.0%（0/100）。这个 0 必须按它的成因读，不能读成「本层无盲区」：**")
    A("")
    A("1. 工作簿对 `loc <= 60` 的 91 个单元给的是**完整单元体**（`MAX_SRC_LINES=60`），")
    A("   单元内部没有隐藏内容；被截断的 9 个（#4/#14/#16/#18/#33/#37/#55/#72/#96）")
    A("   工作簿明示 `完整见 <file>:<lineno>`，本次按该指针从靶仓（同一 3.13.12 树）读全。")
    A("2. 因此本层缺失的不是「单元」，而是**跨文件调用者行为**与**第三方被调方语义**。")
    A("   按 `RULE.md` 对 N-CTX 的窄定义（须「该单元的正确性依赖调用方如何用它」，")
    A("   例如 None/异常的契约由调用方决定），本次抽样中**没有**出现符合该条件的单元；")
    A("   凡属决定性事实在**同文件**内可解析的（#5/#10/#17/#22/#24/#44/#83/#86/#87/#89/#94/#98/#100），")
    A("   都就地解析后判定，而不是记 None。")
    A("3. 后果（诚实条款）：本层读数**不能**用作「盲区规模」的代理量；")
    A("   它反映的是「给了完整单元体时的可判性」，与 `PREREG` §B2 的 None 率对照须按此口径解释。")
    A("")
    A("## 3. 判定口径（本文档声明，非改规则）")
    A("")
    A("| 码 | 口径 | 为什么 |")
    A("|---|---|---|")
    A("| P1 | 证据 = 完整单元体（含靶仓解析）+ 同文件调用关系 + 仓内注释/docstring；**不**查 `Lib/test/*`、**不**查外部 bug 库、**不**执行代码 | 不把外部或测试里的既有判断搬进「独立」对照尺；本层与 L1 的分工就是「读数」vs「执行」 |")
    A("| P2 | 不读 `evidence_hint` 定向（锚点/曲率只当被检信号，不当证据） | `RULE.md` 纪律#1：防对照尺与被检尺同源 |")
    A("| P3 | `assert` 视为**前置条件**：违反者是契约外输入，`-O` 剥除属项目级惯例 ⇒ 不计 1（只记观察） | 否则任何 assert 都成缺陷，属基率自造（纪律#2） |")
    A("| P4 | 触发输入须是**文档化 API 的现实可达用法**；纯理论边角（如 `max_line_length<4`、TZPATH 旁恰有同名兄弟目录）记观察不计 1 | 同 P3：防把「任何缺失守卫」都算缺陷 |")
    A("| P5 | `0` 只主张「**在声明证据内**未找到机理」，不主张「绝对无缺陷」 | `RULE.md` 对该限定的字面要求 |")
    A("| P6 | 每条 `1` 必须给出具体行 + 失效机理 + 触发条件；给不出就降级 | 纪律#2：无机理句的 1 一律降 None |")
    A("")
    A("## 4. 判为 1 的四条（机理 + 触发 + 置信）")
    A("")
    A("| # | 单元 | 层 | 类型 | 置信 | 机理一句话 |")
    A("|---:|---|---|---|---|---|")
    for r in ones:
        j = judge[int(r["seq"])]
        short = {
            4: "新鲜度快路用 flags=0 的时间戳头比对，而 hash 失效模式（flags=1/3）永不相同 ⇒ 每次重编译",
            5: "只捕 ValueError，property 的 getter 为非 Python 函数时 `f.__code__` 抛 AttributeError 穿透 _add_slots ⇒ slots 建类即崩",
            18: "注释判定多一个 `len(tt)==1` 合取，「#word more」的余段被当顶层 token ⇒ NetrcParseError",
            72: "Basic 凭据 `split(':')` 缺 maxsplit，密码含冒号（RFC 7617 允许）时 REMOTE_USER 静默不设",
        }.get(int(r["seq"]), "")
        A("| %s | `%s` | %s | %s | %s | %s |" % (r["seq"], r["name"], r["stratum"],
                                                j.get("defect_type") or "-", j.get("confidence"), short))
    A("")
    A("置信分布：%s" % dict(Counter(judge[int(r["seq"])]["confidence"] for r in srows)))
    A("")
    A("置信含义：`high` = 机理行级可指认且触发路径无歧义；`medium` = 结论依赖较多未展开的被调方语义，")
    A("但单元体完整、未找到机理；`low` = 已指认机理但触发需特定调用面（如 #5 要求 property 的 getter 非 Python 函数）。")
    A("")
    A("## 5. 本层能主张什么 / 不能主张什么")
    A("")
    A("| 能 | 不能 |")
    A("|---|---|")
    A("| 作为**共同对照尺**：各信号源（锚点池/曲率池/SVEN 层/model-side）与本层的一致率可互相比较（相对读数） | 折扣公开集（Devign/BigVul）的人工标签 |")
    A("| 分层缺陷率差读数 + Wilson/bootstrap CI（本回执已给 Wilson） | 系统真实 Se/Sp（须锚定层 + L5） |")
    A("| 本层判定分布与 None 占比（须按 §2 口径解释） | 标注者可靠性 kappa：**单裁判、无独立复标 ⇒ 该量不可测**，不得以自一致性冒充 |")
    A("")
    A("**额外的诚实条款**：")
    A("")
    A("- 四条 `1` 是**读数主张**，不是执行验证（与 L1 的执行正样本不同族）；第三方可按每条注记的行号与触发条件独立复现。")
    A("- 4/100 的 1 率主要反映「标准库经充分测试 + 本层只认有机理的 1」；")
    A("  在 n=20~30 的层内，这个量级的差异几乎不可分辨（见 §1）。任何拿本层做的「哪层更脏」比较，")
    A("  都必须先报 Wilson 区间，禁止只报点估计。")
    A("- 本层**未**开封 `EXP/B2-E4-modelside-SEAL.md` / `modelside.jsonl` / `modelside-stats.json`：")
    A("  按 `PREREG/B2.md` §A5，模型侧读数须在仲裁冻结**之后**才解封比对；本次判定全程未见其内容。")
    A("  这是让「人机一致率」有意义的前提，也让本回执可被第三方按哈希复核。")
    A("")
    A("## 6. 抽样框与工作簿观察（供生成器维护者）")
    A("")
    A("- `B2-E4-framecheck.json` 与工作簿头一致：stdlib 13203 / 全框 18198，site-packages 4995（27.45%），")
    A("  stdlib 零覆盖 97.62%。工作簿头的「零覆盖 97.6%」与之相符。")
    A("- **截断是渲染产物**：`MAX_SRC_LINES=60` 使 9/100 单元的展示体被截断，")
    A("  其中 #55 的截断点**恰好切在 `eval` 命中行的前一行**。读到截断体就判 `None` 会得到")
    A("  「长函数更不可判」的**展示层伪影**（长函数被系统性截断 → None 系统性堆在长单元上），")
    A("  这正是 `PREREG` §B2 想避免的选择性偏置。建议生成器把截断阈值提高或按需内联。")
    A("- **`本函数调用` 列上限 12 个**（`calls[:12]`），`锚点命中行` 上限 5 个 —— 同为渲染上限，非事实。")
    A("- **`同文件调用者` 是子串匹配**（`\"%s(\" % 函数名`），存在假阳性：例如 `_Globber.compile`")
    A("  的调用者里出现 `_compile_pattern`，`TextIOWrapper.errors` 的调用者里出现兄弟属性")
    A("  `TextIOBase.errors`。判读该列时不能当真实调用图使用。")
    A("")
    A("## 7. 产物与复算")
    A("")
    A("| 文件 | 说明 |")
    A("|---|---|")
    A("| `EXP/B2-E4-adjudication.src.jsonl` | **判定源**（人工/机器写入，seq + 判定字段；不可由脚本再生） |")
    A("| `EXP/B2-E4-adjudication.jsonl` | 自足版（补 unit_id/file/lineno/stratum），每条含 `rule` 字段 |")
    A("| `EXP/B2-E4-sample.csv` | 回写版：`truth`/`defect_type`/`annotator`/`date` 已填；**末尾追加** `note` 列；原 16 列顺序逐字保持 |")
    A("| `EXP/B2-E4-adjudication.md` | 本回执 |")
    A("| `EXP/make_b2_e4_adjudication.py` | 派生脚本（本文件） |")
    A("")
    A("**对生成器产物的改写披露（三处，其余逐字未动）**：")
    A("")
    A("1. `source_layer` 由生成器写的 `%s` 改为 `%s`（依据 `B2-E4-RULE.md` 对本层的重新定性）。" % (SOURCE_LAYER_IN, SOURCE_LAYER_OUT))
    A("2. 填了 `truth`/`defect_type`/`annotator`/`date` 四列（本就是要填的空列）。")
    A("3. 末尾追加 `note` 列；CSV 仍写 UTF-8 **带 BOM**（与在盘原件一致；note 含中文，去 BOM 会让 zh-CN 的 Excel 误判编码）。")
    A("")
    A("**并附带发现（产物与脚本不一致，供维护者核对）**：`make_b2_e4_sample.py` 写 CSV 用的是")
    A("`encoding=\"utf-8\"`（无 BOM），但在盘的 `B2-E4-sample.csv` 带 BOM（`EF BB BF`）——")
    A("即该 CSV 并非由现存的这个脚本逐字生成过，或生成后被别的工具改写过。")
    A("另：靶目录名为 `3.13.12`，而该目录下 `python.exe` 自报 **3.13.14**（`sys.version` = 3.13.14, Jun 11 2026）。")
    A("本次判定读的就是生成器实际抽样的那棵树，但「靶版本 3.13.12」这一标签与树内解释器不一致；")
    A("由于本批无版本门单元，N-VER 仍为 0，此条只作来源登记。")
    A("`B2-E4-RULE.md`、`B2-E4-workbook.md`、`B2-E4-workbook-mixed.md`、`B2-E4-sample-mixed.csv`、")
    A("`make_b2_e4_sample.py`、`topos/calib/gold.py` **一律未修改**；工作簿的 100 处判定空格**未就地填写**")
    A("（保持仪器件字节原样），人读映射即本回执 §4 与本目录 jsonl。")
    A("")
    A("复算：")
    A("")
    A("```")
    A("python -X utf8 EXP/make_b2_e4_adjudication.py <repo_root>")
    A("# 期望输出：JSONL 100 行；CSV 101 行（含表头，17 列 = 原 16 列 + note）；判定分布 1=4 0=96 None=0")
    A("```")
    A("")
    with open(os.path.join(exp, "B2-E4-adjudication.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))

    print("判定源   -> %s（%d 条）" % (src, len(judge)))
    print("JSONL    -> %s（%d 行）" % (out_jsonl, len(lines)))
    print("CSV      -> %s（%d 列 / %d 行数据）" % (out_csv, len(cols) + 1, len(srows)))
    print("回执     -> %s" % os.path.join(exp, "B2-E4-adjudication.md"))
    print("分布: 1=%d 0=%d None=%d" % (truth.get("1", 0), truth.get("0", 0), truth.get("None", 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
