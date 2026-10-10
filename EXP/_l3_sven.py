# -*- coding: utf-8 -*-
"""_l3_sven.py —— L3 SVEN 转换器（PREREG/L3.md 判据执行件）。

流程：遍历 sven_data JSONL → .py 筛选 → AST 验证 → 成对入库
（before→1 / after→0）→ gold CSV + functions.jsonl 快照。
"""
import ast
import json
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from topos.calib.gold import GoldStandard                       # noqa: E402

DATA = os.path.join(REPO, "tools", "repos", "sven_data", "data_train_val")
OUT = os.path.join(HERE, "l3_sven")
GOLD = os.path.join(REPO, "calib", "gold_l3_sven.csv")


def main():
    os.makedirs(OUT, exist_ok=True)
    gold = GoldStandard(GOLD)
    n_rows = n_py = n_parse_fail = 0
    parse_fail = []
    cwe_dist = {}
    split_dist = {}
    funcs = []
    seen_ids = set()
    dup = 0
    for split in ("train", "val"):
        d = os.path.join(DATA, split)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".jsonl"):
                continue
            cwe = fn[:-6]
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    n_rows += 1
                    r = json.loads(line)
                    fname = r.get("file_name", "")
                    if not fname.endswith(".py"):
                        continue
                    n_py += 1
                    src = r.get("func_src_before", "")
                    try:
                        ast.parse(src)
                    except SyntaxError:
                        # SVEN 的类方法切片带缩进（F1 同病）——dedent 兜底
                        try:
                            ast.parse(textwrap.dedent(src))
                        except SyntaxError as e:
                            n_parse_fail += 1
                            parse_fail.append((split, cwe, fname,
                                               r.get("func_name"),
                                               str(e)[:60]))
                            continue
                    cwe_dist[cwe] = cwe_dist.get(cwe, 0) + 1
                    split_dist[split] = split_dist.get(split, 0) + 1
                    base = "sven/%s/%s/%s::%s" % (
                        split, cwe, fname, r.get("func_name", "?"))
                    uid_v, uid_f = base + "@vul", base + "@fix"
                    for u in (uid_v, uid_f):
                        if u in seen_ids:
                            dup += 1
                    seen_ids.update((uid_v, uid_f))
                    evidence = "%s | %s" % (r.get("commit_link", ""),
                                            fname)
                    try:
                        gold.add(uid_v, "1", cwe, evidence,
                                 annotator="SVEN CCS'23 (He&Vechev), MIT",
                                 source_layer="L3")
                        gold.add(uid_f, "0", cwe, evidence + " | 修复版",
                                 annotator="SVEN CCS'23 (He&Vechev), MIT",
                                 source_layer="L3")
                    except ValueError:
                        # PREREG E-L3-4：数据集内跨 CWE/重复标注——计数登记，
                        # gold append-only 拒绝（保留首标）
                        dup += 1
                        continue
                    funcs.append({"unit_id": uid_v, "truth": 1, "cwe": cwe,
                                  "split": split, "file_name": fname,
                                  "func_name": r.get("func_name", ""),
                                  "commit_link": r.get("commit_link", ""),
                                  "src": src})
                    funcs.append({"unit_id": uid_f, "truth": 0, "cwe": cwe,
                                  "split": split, "file_name": fname,
                                  "func_name": r.get("func_name", ""),
                                  "commit_link": r.get("commit_link", ""),
                                  "src": r.get("func_src_after", "")})

    gold_path = gold.save()
    with open(os.path.join(OUT, "functions.jsonl"), "w",
              encoding="utf-8") as f:
        for x in funcs:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    st = gold.stats()
    print("① 总行数 %d ｜ Python 子集 %d ｜ AST 解析失败 %d（如实）"
          % (n_rows, n_py, n_parse_fail))
    print("② gold 入库：%s ｜ %s" % (gold_path, st))
    print("③ 重复 unit_id：%d ｜ 成对记录：%d" % (dup, len(funcs)))
    print("④ CWE 分布：%s" % dict(sorted(cwe_dist.items())))
    print("⑤ split 分布：%s" % split_dist)
    if parse_fail:
        print("   解析失败样例：", parse_fail[:3])
    with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
        json.dump({"rows": n_rows, "py": n_py, "parse_fail": n_parse_fail,
                   "gold": st, "dup": dup, "cwe_dist": cwe_dist,
                   "split_dist": split_dist}, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
