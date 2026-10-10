# -*- coding: utf-8 -*-
"""_l3_check.py —— L3 第三方对照：用 SVEN 已知真值实测仪器链路判别力。

Phase 1 信号层：anchor 正则批在 (vul, fix) 配对上的命中判别（win/tie/loss + 符号检验）。
Phase 2 全链：SVEN 空间（每函数一文件）→ Space → 观测（正池/负池）→ NB 解码
              → 配对 belief 读数 + 混淆读数（按函数名义 truth）。
诚实边界：本对照只测 **anchor 正则信号源** 在 SVEN 4-CWE 函数域的判别力
（几何/时间族在该域不可用——无项目上下文/无 git）；Se/Sp 为假设参数，
读数以「实测（参照标准=SVEN 标注，94% 精度）」名义出现。
"""
import json
import math
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

OUT = os.path.join(HERE, "l3_sven")
SPACE = os.path.join(REPO, "tools", "repos", "sven_space")


def load_all():
    import re
    recs = [json.loads(x) for x in
            open(os.path.join(OUT, "functions.jsonl"), encoding="utf-8")
            if x.strip()]
    pats = [(t, re.compile(rx)) for t, rx in json.load(
        open(os.path.join(REPO, "reference", "anchors-bandit.json"),
             encoding="utf-8"))]
    return recs, pats


def hits_of(src, pats):
    return sorted({t for t, rx in pats if rx.search(src)})


def sign_test(wins, losses):
    """双侧精确二项符号检验。"""
    n = wins + losses
    if n == 0:
        return None
    k = max(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def phase1(recs, pats):
    pairs = {}
    for r in recs:
        base = r["unit_id"].rsplit("@", 1)[0]
        pairs.setdefault(base, {})[r["truth"]] = r
    w = l = t = 0
    tag_diff = {}
    per_cwe = {}
    for base, d in pairs.items():
        if 1 not in d or 0 not in d:
            continue
        hv = hits_of(d[1]["src"], pats)
        hf = hits_of(d[0]["src"], pats)
        cwe = d[1]["cwe"]
        pc = per_cwe.setdefault(cwe, {"win": 0, "tie": 0, "loss": 0})
        if len(hv) > len(hf):
            w += 1
            pc["win"] += 1
        elif len(hv) == len(hf):
            t += 1
            pc["tie"] += 1
        else:
            l += 1
            pc["loss"] += 1
        for tg in set(hv) - set(hf):
            tag_diff[tg] = tag_diff.get(tg, 0) + 1
    p = sign_test(w, l)
    # loss 对深挖：fix 命中 > vul 命中的配对明细（反向信号的本质）
    losses = []
    for base, d in pairs.items():
        if 1 not in d or 0 not in d:
            continue
        hv = hits_of(d[1]["src"], pats)
        hf = hits_of(d[0]["src"], pats)
        if len(hf) > len(hv):
            losses.append({"base": base, "cwe": d[1]["cwe"],
                           "vul_tags": hv, "fix_tags": hf,
                           "file": d[1]["file_name"],
                           "commit": d[1]["commit_link"]})
    return {"pairs": len(pairs), "win": w, "tie": t, "loss": l,
            "win_rate": round(w / (w + l), 4) if (w + l) else None,
            "sign_test_p": p, "tag_diff": tag_diff, "per_cwe": per_cwe,
            "loss_detail": losses}


def phase2(recs, pats):
    """全链：写 sven_space → Space → obs（正池/负池）→ decode → 配对 belief。"""
    os.makedirs(SPACE, exist_ok=True)
    for f in os.listdir(SPACE):
        os.remove(os.path.join(SPACE, f))
    mapping = {}
    for i, r in enumerate(recs):
        fn = "u%05d.py" % i
        with open(os.path.join(SPACE, fn), "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(r["src"]).lstrip())  # F1 同药：写入前 dedent
        mapping[fn] = r["unit_id"]
    mf = {"version": 3, "layers": {"call": 1.0},
          "fields": [
              {"name": "anchor", "method": "regex",
               "params": {"patterns_file": "../../reference/anchors-bandit.json"}},
              {"name": "loc", "method": "ast", "params": {"metric": "lines"}}],
          "slicers": [{"name": "anchor:*", "field": "anchor", "op": "expand"},
                      {"name": "anchor:any", "field": "anchor", "op": "notnull"}],
          "pools": [{"name": "p_anchor_breadth", "expr": "anchor:*"},
                    {"name": "p_no_anchor", "expr": {"not": "anchor:any"}}],
          "constraints": {"min_pool_size": 1, "max_width": 100000,
                          "max_width_pct": 1.0, "max_pools": 128},
          "exclude_tests": False}
    mf_path = os.path.join(OUT, "sven_manifest.json")
    with open(mf_path, "w", encoding="utf-8") as f:
        json.dump(mf, f, ensure_ascii=False, indent=1)

    from topos.space import Space
    from topos.report.json_out import build_report, write
    sp = Space(SPACE, manifest_path=mf_path)
    rep = build_report(sp)
    sj = write(rep, os.path.join(OUT, "sven_space.json"))
    alpha = sp.manifest.get("layers", {})
    from topos.core.fuse import fuse
    from topos.core.layers import to_adj
    adj = to_adj(fuse(sp.layers, alpha))
    with open(os.path.join(OUT, "sven_adj.json"), "w", encoding="utf-8") as f:
        json.dump({str(i): sorted(v) for i, v in adj.items()}, f)

    # 观测：正池=有 anchor 命中的单元集合；负池=无命中的单元集合（信号本身）
    anchor = sp.fields["anchor"]
    pos = [i for i in range(len(sp.units)) if anchor.get(i)]
    neg = [i for i in range(len(sp.units)) if not anchor.get(i)]
    obs = {"p_anchor_breadth": 1, "p_no_anchor": 0}
    with open(os.path.join(OUT, "sven_obs.json"), "w", encoding="utf-8") as f:
        json.dump(obs, f)
    with open(os.path.join(OUT, "sven_pools.json"), "w", encoding="utf-8") as f:
        json.dump({"p_anchor_breadth": pos, "p_no_anchor": neg}, f)

    from topos.cli import main as cli_main
    rc = cli_main(["decode", sj, "--obs", os.path.join(OUT, "sven_obs.json"),
                   "--decoder", "nb", "--adj",
                   os.path.join(OUT, "sven_adj.json"),
                   "-o", os.path.join(OUT, "sven_belief.json")])
    with open(os.path.join(OUT, "sven_belief.json"), encoding="utf-8") as f:
        bel = json.load(f)["belief"]

    # 文件 → 单元号（space.json 的 units 顺序）→ belief
    with open(sj, encoding="utf-8") as f:
        unit_ids = json.load(f)["units"]
    idx_by_file = {}
    for i, uid in enumerate(unit_ids):
        idx_by_file[uid.split("::")[0]] = i
    return {"n_units": len(sp.units), "decode_rc": rc, "obs": obs,
            "mapping": mapping, "bel": bel,
            "idx_by_file": idx_by_file,
            "pos_n": len(pos), "neg_n": len(neg)}


def paired_belief(recs, mapping, bel, idx_by_file):
    pairs = {}
    for r in recs:
        base = r["unit_id"].rsplit("@", 1)[0]
        pairs.setdefault(base, {})[r["truth"]] = r
    w = l = t = 0
    for base, d in pairs.items():
        bv = bf = None
        for truth, r in d.items():
            fname = None
            for f, uid in mapping.items():
                if uid == r["unit_id"]:
                    fname = f
                    break
            if fname is None or fname not in idx_by_file:
                continue
            b = bel.get(str(idx_by_file[fname]))
            if r["truth"] == 1:
                bv = b
            else:
                bf = b
        if bv is None or bf is None:
            continue
        if bv > bf:
            w += 1
        elif bv == bf:
            t += 1
        else:
            l += 1
    return {"win": w, "tie": t, "loss": l}


def main():
    recs, pats = load_all()
    p1 = phase1(recs, pats)
    print("=== Phase 1 信号层配对判别 ===")
    print("对数 %d ｜ win %d / tie %d / loss %d ｜ 胜率 %s ｜ 符号检验 p=%s"
          % (p1["pairs"], p1["win"], p1["tie"], p1["loss"],
             p1["win_rate"], p1["sign_test_p"]))
    print("vul 独有命中 tag top：", sorted(p1["tag_diff"].items(),
                                           key=lambda x: -x[1])[:8])
    for cwe, d in sorted(p1["per_cwe"].items()):
        print("   %s: win %d / tie %d / loss %d" % (cwe, d["win"],
                                                    d["tie"], d["loss"]))
    print("=== loss 对深挖（fix 命中 > vul 命中）===")
    for x in p1["loss_detail"]:
        print("  %s ｜ %s" % (x["cwe"], x["file"]))
        print("    vul tags: %s" % x["vul_tags"])
        print("    fix tags: %s" % x["fix_tags"])
        print("    commit: %s" % x["commit"])
    p2 = phase2(recs, pats)
    print("=== Phase 2 全链（sven_space %d 单元）===" % p2["n_units"])
    print("obs:", p2["obs"], "｜ pos=%d neg=%d" % (p2["pos_n"], p2["neg_n"]))
    pb = paired_belief(recs, p2["mapping"], p2["bel"], p2["idx_by_file"])
    print("配对 belief：win %d / tie %d / loss %d" % (pb["win"], pb["tie"],
                                                      pb["loss"]))
    out = {"phase1": {k: v for k, v in p1.items()},
           "phase2": {"n_units": p2["n_units"], "pos_n": p2["pos_n"],
                      "neg_n": p2["neg_n"], "obs": p2["obs"],
                      "paired": pb}}
    with open(os.path.join(OUT, "check.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % os.path.join(OUT, "check.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
