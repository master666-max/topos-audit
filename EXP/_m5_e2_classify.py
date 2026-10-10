# -*- coding: utf-8 -*-
"""
_m5_e2_classify —— E-M5-2 未确认边分类器（回执证据件）。

对 T−Gm 未确认边逐条判定：
  GAP   金标盲区：Joern 看见了该调用点（caller 行落在 a 的 span 内、
        callee 名匹配 b 的简单名）但 callee 未解析（filename=<empty>，
        动态分发/self.x()/参数对象调用是 pysrc2cpg 已知弱项）——
        边真实存在，只是注册口径（仅取 resolved callee）下不可指认；
  FP    疑似误报：金标（含未解析层）中找不到任何该调用点痕迹，
        需人工抽查源码定谳；
  GOLD  金标已解析却未入 Gm（理论不可能，出现即为映射 bug，必须报错）。
"""
import ast
import os
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

import exp_m5_e2 as m                                          # noqa: E402


def load(tag):
    edges = []
    with open(os.path.join(m.OUT, "dump_%s.log" % tag),
              encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("EDGE\t"):
                p = line.rstrip("\n").split("\t")
                if len(p) == 7:
                    edges.append((p[1], p[2], p[3], p[4], p[5], p[6]))
    return edges


def unit_src(units, idx):
    return textwrap.dedent(units[idx]["src"])


def classify(tag, target, lang):
    edges = load(tag)
    units, T = m.topos_side(target, lang)
    files_set = {u["file"] for u in units}
    keymap = {}
    for i, u in enumerate(units):
        keymap.setdefault((u["file"], u["lineno"]), i)
    spans = {}
    for i, u in enumerate(units):
        spans.setdefault(u["file"], []).append(
            (u["lineno"], u["end_lineno"], i))
    for f in spans:
        spans[f].sort(key=lambda x: (x[1] - x[0], x[0]))

    def unit_of(fn, ln):
        rel = m._norm_fn(fn, target, files_set)
        if rel not in files_set:
            return None
        try:
            li = int(float(ln))
        except ValueError:
            return None
        if (rel, li) in keymap:
            return keymap[(rel, li)]
        for a, b, i in spans.get(rel, []):
            if a <= li <= b:
                return i
        return None

    # 金标全层（Gm ∪ 未解析层）：caller 单元 → [(callee_fullName, callee_file)]
    caller_calls = {}
    for cfn, cfl, cl, tfn, tfl, tl in edges:
        ci = unit_of(cfl, cl)
        if ci is None:
            continue
        caller_calls.setdefault(ci, []).append((tfn, tfl))

    Gm = set()
    for cfn, cfl, cl, tfn, tfl, tl in edges:
        ci, ti = unit_of(cfl, cl), unit_of(tfl, tl)
        if ci is None or ti is None or ci == ti:
            continue
        Gm.add((min(ci, ti), max(ci, ti)))

    def simple(u_idx):
        return units[u_idx]["name"].split(".")[-1]

    gaps, fps, golds = [], [], []
    for a, b in sorted(T - Gm):
        sa, sb = simple(a), simple(b)
        # 无向对：调用点可能在 a 侧（调 b 名）或 b 侧（调 a 名）
        calls_a = caller_calls.get(a, [])
        calls_b = caller_calls.get(b, [])

        def _hit(calls, name):
            hit_r = hit_u = False
            for tfn, tfl in calls:
                if tfn.split(":")[-1].split(".")[-1] != name:
                    continue
                if tfl != "<empty>" and tfl in files_set:
                    hit_r = True
                elif tfl == "<empty>":
                    hit_u = True
            return hit_r, hit_u

        ra, ua = _hit(calls_a, sb)                   # a 调 b
        rb, ub = _hit(calls_b, sa)                   # b 调 a
        if ra or rb:
            golds.append((a, b))
        elif ua or ub:
            gaps.append((a, b))
        else:
            fps.append((a, b))
    return {"units": units, "T": T, "Gm": Gm, "gaps": gaps, "fps": fps,
            "golds": golds}


def main():
    out = {}
    for tag, target, lang in [("py", m.PY_TARGET, "py"),
                              ("js", m.JS_TARGET, "js")]:
        r = classify(tag, target, lang)
        n_unconf = len(r["gaps"]) + len(r["fps"]) + len(r["golds"])
        print("=" * 66)
        print("[%s] 未确认边 %d 条：金标盲区(GAP) %d ｜ 疑似误报(FP) %d ｜ "
              "映射异常(GOLD) %d" % (tag, n_unconf, len(r["gaps"]),
                                    len(r["fps"]), len(r["golds"])))
        if r["golds"]:
            print("!! GOLD 非空 —— 映射 bug，必须排查")
        if r["gaps"][:8]:
            print("GAP 样例（调用真实存在，Joern 未解析 callee）：")
            for a, b in r["gaps"][:8]:
                print("    %s -> %s" % (r["units"][a]["id"],
                                        r["units"][b]["id"]))
        if r["fps"][:8]:
            print("FP 样例（需人工抽查源码）：")
            for a, b in r["fps"][:8]:
                print("    %s -> %s" % (r["units"][a]["id"],
                                        r["units"][b]["id"]))
        # 修正读数：金标盲区不计入 precision 否决（候选口径，待拍板）
        T, Gm = r["T"], r["Gm"]
        eff = T - set(map(tuple, r["fps"]))
        inter = T & Gm
        prec_reg = len(inter) / len(T) if T else 0
        prec_eff = len(inter) / len(eff) if eff else 0
        print("precision 注册口径：%.4f（|T|=%d）" % (prec_reg, len(T)))
        print("precision 剔除FP口径：%.4f（|T_eff|=%d）" % (prec_eff, len(eff)))
        out[tag] = {"n_unconfirmed": n_unconf, "gap": len(r["gaps"]),
                    "fp": len(r["fps"]), "gold": len(r["golds"]),
                    "prec_reg": round(prec_reg, 4),
                    "prec_eff": round(prec_eff, 4),
                    "fp_sample": ["%s -> %s" % (r["units"][a]["id"],
                                                r["units"][b]["id"])
                                  for a, b in r["fps"]],
                    "gap_sample": ["%s -> %s" % (r["units"][a]["id"],
                                                 r["units"][b]["id"])
                                   for a, b in r["gaps"]]}
    dest = os.path.join(HERE, "m5_e2_classify.json")
    with open(dest, "w", encoding="utf-8") as f:
        import json
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)


if __name__ == "__main__":
    main()
