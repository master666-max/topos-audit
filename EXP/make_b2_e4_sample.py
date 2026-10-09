# -*- coding: utf-8 -*-
"""
EXP/make_b2_e4_sample.py —— 生成 E-B2-4 参照标准定向清单（100 单元）。

产出两件：
  ① EXP/B2-E4-sample.csv    机器可读清单（truth 列留空）
  ② EXP/B2-E4-workbook.md   **仲裁工作簿**：每个单元一节，含完整源码 + 调用上下文
                            + 锚点命中行 + 结构量 + 判定填空区（这才是人能用的形态）

抽样规则（PREREG/B2 E-B2-4）：按池分层，**零覆盖单元强制入样**（E-X1 教训）。
"""
import ast
import csv
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topos.space import Space  # noqa: E402
from topos.axis.methods.regex import _load_patterns  # noqa: E402

TARGET = r"C:\Users\26672\.workbuddy\binaries\python\versions\3.13.12\Lib"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV_OUT = os.path.join(HERE, "B2-E4-sample.csv")
WB_OUT = os.path.join(HERE, "B2-E4-workbook.md")
SEED = 20261009
QUOTA = {"zero_cover": 25, "anchor": 25, "confluence": 20, "random": 30}
MAX_SRC_LINES = 60


def callees_of(src):
    """本函数体内出现的调用（简单名/属性名）。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                out.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                out.append(node.func.attr)
    return sorted(set(out))


def anchor_lines(src, pats):
    """逐行扫描锚点命中 → [(行号, 行内容, [tag])]。"""
    hits = []
    for i, line in enumerate(src.splitlines(), start=1):
        tags = [t for t, p in pats if p.search(line)]
        if tags:
            hits.append((i, line.strip()[:100], tags))
    return hits


def main():
    if not os.path.isdir(TARGET):
        print("目标目录不存在: %s" % TARGET)
        return 1
    sp = Space(TARGET)
    n = sp.n
    if n == 0:
        print("目标仓 0 单元——中止")
        return 1

    covered, pool_of = set(), {}
    for name, members in sp.rows:
        for i in members:
            covered.add(i)
            pool_of.setdefault(i, []).append(name)
    zero = [i for i in range(n) if i not in covered]

    anchor_field = sp.fields.get("anchor", {})
    anchor_hit = [i for i in range(n) if anchor_field.get(i)]
    curv = sp.fields.get("forman", {})
    cv = sorted(v for v in curv.values() if v is not None)
    thr = cv[len(cv) // 3] if cv else None
    confluence = [i for i in range(n)
                  if curv.get(i) is not None and thr is not None and curv[i] <= thr]

    rng = random.Random(SEED)
    picked = {}
    for i in rng.sample(zero, min(QUOTA["zero_cover"], len(zero))):
        picked[i] = "zero_cover"
    for i in rng.sample(anchor_hit, min(QUOTA["anchor"], len(anchor_hit))):
        picked.setdefault(i, "anchor")
    for i in rng.sample(confluence, min(QUOTA["confluence"], len(confluence))):
        picked.setdefault(i, "confluence")
    rest = [i for i in range(n) if i not in picked]
    for i in rng.sample(rest, min(100 - len(picked), len(rest))):
        picked.setdefault(i, "random")

    pats = _load_patterns({"patterns_file": "reference/anchors-bandit.json"},
                          base_dir=ROOT)
    same_file = defaultdict(list)
    for i, u in enumerate(sp.units):
        same_file[u["file"]].append(i)

    csv_rows, wb = [], []
    for idx, (i, stratum) in enumerate(sorted(picked.items()), start=1):
        u = sp.units[i]
        src_lines = u["src"].splitlines()
        truncated = len(src_lines) > MAX_SRC_LINES
        shown = src_lines[:MAX_SRC_LINES]
        calls = callees_of(u["src"])
        simple = u["name"].split(".")[-1]
        callers = [sp.units[j]["name"] for j in same_file.get(u["file"], [])
                   if j != i and ("%s(" % simple) in sp.units[j]["src"]]
        a_lines = anchor_lines(u["src"], pats)
        tags = anchor_field.get(i) or []
        hint = ("零覆盖：不在任何池内（盲区核查）" if stratum == "zero_cover"
                else "锚点命中 %s" % (", ".join(tags) or "-") if stratum == "anchor"
                else "曲率汇合点 forman=%s" % curv.get(i) if stratum == "confluence"
                else "随机层（无偏基线）")
        csv_rows.append({
            "seq": idx, "unit_id": u["id"], "file": u["file"], "name": u["name"],
            "lineno": u["lineno"], "loc": u["loc"], "stratum": stratum,
            "in_pools": "|".join(pool_of.get(i, [])),
            "anchor_tags": "|".join(tags), "forman": curv.get(i),
            "evidence_hint": hint,
            "truth": "", "defect_type": "", "annotator": "", "date": "",
            "source_layer": "L4-reference",
        })
        wb.append("## #%d · %s · `%s`\n" % (idx, stratum, u["name"]))
        wb.append("- **位置**：`%s:%d`（%d 行）" % (u["file"], u["lineno"], u["loc"]))
        wb.append("- **层**：%s ｜ %s" % (stratum, hint))
        wb.append("- **结构量**：Forman=%s ｜ 池：%s"
                  % (curv.get(i), ", ".join(pool_of.get(i, [])) or "（不在任何池内）"))
        if calls:
            wb.append("- **本函数调用**：`%s`" % "`, `".join(calls[:12]))
        if callers:
            wb.append("- **同文件调用者**：`%s`（跨文件调用者未扫描）"
                      % "`, `".join(callers[:8]))
        if a_lines:
            wb.append("- **锚点命中行**：")
            for ln, text, tg in a_lines[:5]:
                wb.append("  - L%d `%s` → %s" % (ln, text, ", ".join(tg)))
        wb.append("\n**源码**：\n")
        wb.append("```python\n" + "\n".join(shown) + "\n```")
        if truncated:
            wb.append("\n> 已截断（共 %d 行），完整见 `%s:%d`"
                      % (len(src_lines), u["file"], u["lineno"]))
        wb.append("\n**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**）"
                  " ｜ defect_type = `___` ｜ 备注 = `___`\n")
        wb.append("---\n")

    with open(CSV_OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        w.writeheader()
        w.writerows(csv_rows)
    head = [
        "# E-B2-4 参照标准定向工作簿（100 单元）\n",
        "> 靶仓：Python 标准库（N=%d 单元）｜池 %d 个｜零覆盖 %.1f%%"
        % (n, len(sp.rows), 100.0 * len(zero) / max(n, 1)),
        "> **这份工作簿不是让你标真值**——人不是真值（Devign 4 专家 × 600 人时 × 两轮交叉，",
        "> 复测正确率仅 24%）。它的作用是 **定向**（打破 Hui–Walter 镜像等价解）、",
        "> **一致性量化**（双盲 → Cohen's κ，κ<0.60 则该轴标称作废）、**误差棒**。",
        "> 判不出来填 `None`——None 比猜一个 0/1 有价值得多。",
        "> 分层分布：%s" % dict(Counter(r["stratum"] for r in csv_rows)),
        "",
        "---",
        "",
    ]
    with open(WB_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(head) + "\n".join(wb))

    print("单元 N=%d  池=%d  零覆盖 %.1f%%" % (n, len(sp.rows),
                                            100.0 * len(zero) / max(n, 1)))
    print("分层: %s" % dict(Counter(r["stratum"] for r in csv_rows)))
    print("CSV    -> %s (%d 行)" % (CSV_OUT, len(csv_rows)))
    print("工作簿 -> %s" % WB_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
