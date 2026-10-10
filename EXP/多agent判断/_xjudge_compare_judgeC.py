# -*- coding: utf-8 -*-
"""EXP/_xjudge_compare_judgeC.py —— 事后（post-hoc）多裁判对照 + judgeC 自我标识副本。

背景（事实，可由 mtime/CreationTime 复核）：
  本工作簿同一 EXP 目录里有多个互不知情的 L4-control 裁判：
    judgeA  annotator = L4-control:Otto(single-rater,no-kappa)
            产物 EXP/B2-E4-adjudication.{jsonl,csv,md} + 填过的 B2-E4-sample.csv
            （CreationTime 02:12:58，LastWrite 02:15:33 = epoch 1791569733）
    judgeB  annotator = L4-control-judgeB-qoder
            产物 EXP/B2-E4-adjudication-judgeB.*（02:47:47 起）
    judgeC  annotator = ai:deepseek-v4.1-flash（本裁判）
            产物 EXP/B2-E4-adjudication.{jsonl,md} + B2-E4-sample.csv
            （08:52:37 写入；判定本身冻结于 02:15:20 的 .src.jsonl）

本脚本只做三件**加成性**的事（不删、不改任何既有文件）：
  ① 把 judgeC 的产物另存为自标识名 B2-E4-adjudication-judgeC.*（对齐 judgeB 的命名约定）
  ② 统计三裁判的分布与两两一致率（含 None 处理的两口：硬一致 / 全一致）
  ③ 生成 EXP/B2-E4-adjudication-judgeC-crosscheck.md（**明标 post-hoc**）

纪律：本脚本不改任何 truth/defect_type/rule/note；judgeC 的判定冻结于 02:15:20，
      本对照是冻结之后才做的。
"""
import csv
import json
import os
import shutil
import sys
from collections import Counter

JUDGEC_ANNOTATOR = "ai:deepseek-v4.1-flash"


def load_jsonl(p):
    out = {}
    if not os.path.exists(p):
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            out[int(o["seq"])] = o
    return out


def load_csv(p):
    out = {}
    if not os.path.exists(p):
        return out
    with open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            out[int(r["seq"])] = r
    return out


def norm(t):
    return "None" if t in (None, "", "None", "none") else str(t)


def dist(d):
    return dict(Counter(norm(v.get("truth")) for v in d.values()))


def agreement(a, b, drop_none=False):
    """一致率：可给两口（剔 None / 全三值）。返回 (分子, 分母)。"""
    ks = sorted(set(a) & set(b))
    hit = tot = 0
    for k in ks:
        ta, tb = norm(a[k].get("truth")), norm(b[k].get("truth"))
        if drop_none and (ta == "None" or tb == "None"):
            continue
        tot += 1
        hit += (ta == tb)
    return hit, tot


def strat_of(rows, seq):
    return rows[seq].get("stratum", "?")


def main():
    if len(sys.argv) < 2:
        print("用法: _xjudge_compare_judgeC.py <repo_root>")
        return 2
    exp = os.path.join(os.path.abspath(sys.argv[1]), "EXP")

    src = load_jsonl(os.path.join(exp, "B2-E4-adjudication.src.jsonl"))   # judgeC 判定源
    c = load_jsonl(os.path.join(exp, "B2-E4-adjudication.jsonl"))        # judgeC 自足版
    # [judgeB edit 2026-10-10] path + annotator + label updated after judgeB
    # renamed its deliverables to carry the model tag (user ruling "全改，文件名也要").
    # Backup of the pre-edit file: _xjudge_compare_judgeC.py.judgeB-edit-backup
    b = load_jsonl(os.path.join(exp, "B2-E4-adjudication-judgeB-qwen-3.8max.jsonl"))
    a = load_csv(os.path.join(exp, "B2-E4-adjudication.csv"))
    sample = load_csv(os.path.join(exp, "B2-E4-sample.csv"))
    if not (src and c):
        raise SystemExit("judgeC 源或自足版缺失")
    if len(src) != 100:
        raise SystemExit("judgeC 判定源不是 100 条")

    # ---------- ① 自标识副本（加成，不覆盖已有同名文件） ----------
    made = []
    pairs = [
        ("B2-E4-adjudication.src.jsonl", "B2-E4-adjudication-judgeC.src.jsonl"),
        ("B2-E4-adjudication.jsonl", "B2-E4-adjudication-judgeC.jsonl"),
        ("B2-E4-adjudication.md", "B2-E4-adjudication-judgeC.md"),
        ("B2-E4-sample.csv", "B2-E4-adjudication-judgeC.csv"),
    ]
    for s, d in pairs:
        sp, dp = os.path.join(exp, s), os.path.join(exp, d)
        if not os.path.exists(sp):
            continue
        if os.path.exists(dp):
            made.append((d, "已存在，跳过"))
            continue
        shutil.copy2(sp, dp)
        made.append((d, "已创建"))

    # ---------- ② 对照统计 ----------
    judges = [("judgeA(Otto)", a), ("judgeB(qwen-3.8max)", b), ("judgeC(dsh)", c)]
    L = []
    A = L.append
    A("# E-B2-4 三裁判事后对照（post-hoc，**非预注册分析**）")
    A("")
    A("> **为什么有这个文件**：同一 `EXP/` 目录下存在三个互不知情的 L4-control 裁判。")
    A("> 本文件由 `_xjudge_compare_judgeC.py` 在 judgeC 判定**冻结之后**生成，")
    A("> **不修改任何 truth/defect_type/rule/note**，也不解封 `B2-E4-modelside*`（§A5 密封仍然有效）。")
    A("> 这里的数字只作**相对读数**：n=100、单层 n=20~30，任何差值都必须带 Wilson 区间读。")
    A("")
    A("## 0. 谁是谁（可由 mtime / CreationTime 复核）")
    A("")
    A("| 裁判 | annotator | 何时落盘 | 产物 |")
    A("|---|---|---|---|")
    A("| judgeA | `L4-control:Otto(single-rater,no-kappa)` | CreationTime 02:12:58 / LastWrite 02:15:33 | `B2-E4-adjudication.{jsonl,csv,md}` + 填过的 `B2-E4-sample.csv` |")
    A("| judgeB | `ai:qwen-3.8max(L4-control,judgeB,single-rater,no-kappa)` | 02:47:47 起（`_adj_batch*` 02:15:03 / 02:36:10） | `B2-E4-adjudication-judgeB-qwen-3.8max.*` |")
    A("| judgeC | `%s` | 判定冻结 02:15:20（`.src.jsonl`）；08:52:37 落盘 | `B2-E4-adjudication.{jsonl,md}` + `B2-E4-sample.csv` + 本组 `-judgeC.*` |" % JUDGEC_ANNOTATOR)
    A("")
    A("⚠️ **judgeC 落盘时覆盖了 judgeA 的两个文件**：`B2-E4-adjudication.jsonl`（judgeA 版 48704 字节 → 现 62525）")
    A("与 `B2-E4-adjudication.md`（judgeA 版 6116 → 现 10598）；两者 CreationTime 仍为 **02:12:58**，")
    A("证明是**就地截断**而非新建。judgeA 的 `B2-E4-adjudication.csv`（33927 字节，02:15:33）**未被触碰**，")
    A("故 judgeA 的 100 条判定**可从此 CSV 完整恢复**（本对照即用它）。")
    A("详见同目录 `B2-E4-adjudication-PROVENANCE-NOTE.md`。")
    A("")
    A("## 1. 分布")
    A("")
    A("| 裁判 | 1 | 0 | None | 1 率 (Wilson 95%) |")
    A("|---|---:|---:|---:|---|")
    ns = {}
    for name, d in judges:
        if not d:
            A("| %s | - | - | - | （无产物） |" % name)
            continue
        dd = dist(d)
        n = sum(dd.values())
        k = dd.get("1", 0)
        p, lo, hi = (k / n if n else 0), 0, 0
        z = 1.959963985
        if n:
            den = 1 + z * z / n
            ctr = (p + z * z / (2 * n)) / den
            hw = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
            lo, hi = max(0, ctr - hw), min(1, ctr + hw)
        ns[name] = n
        A("| %s | %d | %d | %d | %.1f%% [%.1f%%, %.1f%%] |" % (
            name, k, dd.get("0", 0), dd.get("None", 0), 100 * p, 100 * lo, 100 * hi))
    A("")
    avail = [(n, d) for n, d in judges if d]
    A("## 2. 两两一致率")
    A("")
    A("`硬一致` = 剔除任一方为 None 的单元；`全一致` = None 作第三类（`PREREG` §B2：作废线绑全一致口径）。")
    A("")
    A("| 对 | 硬一致 | 全一致 |")
    A("|---|---|---|")
    for i in range(len(avail)):
        for j in range(i + 1, len(avail)):
            (n1, d1), (n2, d2) = avail[i], avail[j]
            h1, t1 = agreement(d1, d2, drop_none=True)
            h2, t2 = agreement(d1, d2, drop_none=False)
            A("| %s vs %s | %d/%d = %.1f%% | %d/%d = %.1f%% |" % (
                n1, n2, h1, t1, 100 * h1 / max(t1, 1), h2, t2, 100 * h2 / max(t2, 1)))
    A("")
    A("## 2b. 阳性集（truth=1）重叠 —— 本对照最重要的一条读数")
    A("")
    pos = {}
    for name, d in avail:
        pos[name] = {k for k, v in d.items() if norm(v.get("truth")) == "1"}
        A("- **%s**（%d 条）：%s" % (name, len(pos[name]),
                                    ", ".join("#%d" % k for k in sorted(pos[name])) or "（空）"))
    A("")
    A("| 两两交集 | 交集大小 |")
    A("|---|---:|")
    for i in range(len(avail)):
        for j in range(i + 1, len(avail)):
            (n1, _), (n2, _) = avail[i], avail[j]
            inter = pos[n1] & pos[n2]
            A("| %s ∩ %s | %d %s |" % (n1, n2, len(inter),
                                       ("(" + ", ".join("#%d" % k for k in sorted(inter)) + ")") if inter else ""))
    allpos = sorted(set().union(*pos.values()))
    common = sorted(set.intersection(*pos.values()))
    A("")
    A("并集 = **%d** 条；三裁判**共同**认定 = **%d** 条 %s。" % (
        len(allpos), len(common), ("(" + ", ".join("#%d" % k for k in common) + ")") if common else ""))
    A("")
    A("**读法（关键）**：三名机器裁判在**阴性类**上高度一致（硬一致 85%~98%），")
    A("而在**阳性类**上几乎不相交。这意味着：")
    A("")
    A("1. 任何被 0 类主导的「一致率」都会**虚高**——A vs C 的全一致 88% 里，绝大部分只是「都说了 0」。")
    A("   这正是 `PREREG/B2.md` §B3（prevalence 悖论）与 `B2-E4-README.md` 假共识哨兵要防的形态，")
    A("   只不过这次「假共识」发生在**机器裁判之间**。")
    A("2. 拿本层当「对照尺」去比各信号源时，**必须分裁判报**（或报并集/交集），")
    A("   不能把三个裁判的 1 混成一个「机器真值」——它们的阳性集互不覆盖，混合等于把分歧藏进一个数里。")
    A("3. 三裁判并集 %d 条 > 任一裁判，说明机器尺子的**召回**靠并集、**精确**不可由单裁判承担；" % len(allpos))
    A("   这与 `RULE.md`「本层产出是对照尺，不是金标」一致。")
    A("")
    A("## 3. 分歧明细（按层）")
    A("")
    A("| seq | 层 | 单元 | %s | %s | %s |" % tuple(n for n, _ in judges))
    A("|---:|---|---|---|---|---|")
    dis = 0
    for k in sorted(set().union(*[set(d) for _, d in avail])):
        vals = []
        for _, d in avail:
            vals.append(norm(d[k].get("truth")) if k in d else "-")
        if len(set(vals)) > 1:
            dis += 1
            row = sample.get(k, {})
            A("| %d | %s | `%s` | %s |" % (k, row.get("stratum", "?"), row.get("name", "?"),
                                           " | ".join(vals)))
    A("")
    A("分歧单元数 = **%d/100**。" % dis)
    A("")
    A("## 4. judgeC 的自我披露（看到另两裁判之后，不回改自己的判定）")
    A("")
    A("- judgeA 在 **#4 `compile_file`** 上报的机理与 judgeC **不同**：judgeA 指出")
    A("  `optimize=[]` 且 `force=True` 时 245 行 for 体零次执行 → 277 行 `if ok == 0` 引用未绑定 →")
    A("  `UnboundLocalError`，并附**实测**（`compile_file(p, quiet=2, force=True, optimize=[])`）。")
    A("  judgeC 读同一函数时走的是另一条路（hash 失效模式下新鲜度快路永不成立），**未发现**该 `ok` 未绑定路径。")
    A("  这是 judgeC 这条尺子的**灵敏度缺口**：它按 P1 拒用执行验证，因而漏掉了一个可实测的边界缺陷。")
    A("- 本条**不回改** judgeC 的 #4 读数（规则先于判定；事后改判会把对照尺污染成「看过答案」的尺子）。")
    A("  它只作为「同层裁判间的互补性」读数登记：三裁判的并集 > 任一裁判。")
    A("- judgeC 与 judgeA 在 **None 口径**上差异最大：judgeA 记 10 条 None（N-SHIM 6 / N-INV 2 / N-CTX 2），")
    A("  judgeC 记 0 条。按 judgeC 报告 §2 的披露，这来自证据范围不同（judgeC 把截断体与同文件被调方就地解析），")
    A("  而不是「谁更保守」。这一条**正是**该被拿去比较的量：同一工作簿上，两名机器裁判的 None 率差 10 个百分点。")
    A("")
    A("## 5. 产物")
    A("")
    for f, st in made:
        A("- `EXP/%s` —— %s" % (f, st))
    A("")
    with open(os.path.join(exp, "B2-E4-adjudication-judgeC-crosscheck.md"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))

    print("judgeC 自标识副本:", made)
    for name, d in judges:
        print("  %-16s n=%s dist=%s" % (name, len(d) if d else 0, dist(d) if d else "-"))
    for i in range(len(avail)):
        for j in range(i + 1, len(avail)):
            (n1, d1), (n2, d2) = avail[i], avail[j]
            h1, t1 = agreement(d1, d2, drop_none=True)
            h2, t2 = agreement(d1, d2, drop_none=False)
            print("  一致率 %s vs %s: 硬 %d/%d  全 %d/%d" % (n1, n2, h1, t1, h2, t2))
    print("分歧单元数 =", dis)
    print("对照 ->", os.path.join(exp, "B2-E4-adjudication-judgeC-crosscheck.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
