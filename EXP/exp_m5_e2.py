# -*- coding: utf-8 -*-
"""
exp_m5_e2 —— E-M5-2 Joern 离线金标校验（PREREG/M5 §2，D-B 主判据）。

对拍口径（PREREG/M5 §2 逐字）：
  - 边归一化到 (调用方函数, 被调方函数) **无向函数级对**；
  - Joern 侧动态调用/继承产生的边视为**金标超集**，不算 topos 误报（金标超集条款）；
  - CALL 类型边取 callee **已解析**者（Joern unresolved 不强求）；
  - precision 门 ≥0.8（topos 报出的边在金标中可指认），recall 只报数不设门。

topos 侧 = 主链路同一抽取器（space.py 装配的两件，不另造）：
  py : topos.core.units.discover_units + topos.core.layers._extract_layers
  js : topos.core.langjs.discover_units_js + extract_layers_js

映射口径：Joern METHOD(lineNumber) = 声明行，topos unit lineno = def/function
声明行 —— 以 (归一化文件, 声明行) 精确对齐为主，包含判定兜底（最小包含单元）。
金标中映射不到 topos 单元的边 = "单元宇宙差"（Joern 合成 program 方法、
topos 未发现的嵌套函数等），归金标超集，不计入 precision 分母的否决项。

用法：python exp_m5_e2.py [py|js|both]      # 默认 both
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from topos.core import units as units_mod                     # noqa: E402
from topos.core.layers import _extract_layers                 # noqa: E402
from topos.core import langjs                                 # noqa: E402

JOERN_HOME = os.path.join(REPO, "tools", "joern")
DL = os.path.join(REPO, "tools", "joern-dl")
PY_TARGET = os.path.join(REPO, "reference", "bandit", "bandit")
JS_TARGET = os.path.join(REPO, "tools", "repos", "express-master", "lib")
OUT = os.path.join(HERE, "m5_e2")

TBL = "─" * 66
JOERN_VERSION = None


# --------------------------------------------------------------- 环境定位 --

def _find_bat(name):
    """tools/joern 下找 <name>.bat（zip 解包布局未知，glob 兜底）。"""
    for root, _dirs, files in os.walk(JOERN_HOME):
        for f in files:
            if f.lower() == name.lower() + ".bat":
                return os.path.join(root, f)
    return None


def _jre_dir():
    """便携 JRE21 目录（含 bin/java.exe 的最浅目录）。"""
    for root, dirs, files in os.walk(JOERN_HOME):
        if "java.exe" in files and os.path.basename(root) == "bin":
            return os.path.dirname(root)
        # 防止深挖 jre 内部 bin：浅层优先
        if root.count(os.sep) - JOERN_HOME.count(os.sep) > 4:
            dirs[:] = []
    return None


def _joern_env():
    jre = _jre_dir()
    if jre is None:
        return None
    env = dict(os.environ)
    env["JAVA_HOME"] = jre
    env["PATH"] = os.path.join(jre, "bin") + os.pathsep + env.get("PATH", "")
    return env                                    # 按调用注入（T-M5-c）


def _run(cmd, env, timeout, cwd=None):
    """subprocess 包装：超时/异常 → (rc=-9, msg)，不让挂起炸掉实验。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           timeout=timeout, cwd=cwd)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -9, "TIMEOUT after %ss" % timeout
    except OSError as e:
        return -8, "OSERROR %s" % e


def env_check():
    """D-M5-2a：joern 在便携 JRE21 上跑通（系统 Java 不动）。

    实测（2026-10-10）：joern.bat 不认 --version（掉 REPL 挂起）——
    主路径改用 --script 空脚本 probe（脚本结束进程即退），banner 里抓版本行；
    --version 降为 120s 快试备选。"""
    global JOERN_VERSION
    bat = _find_bat("joern")
    env = _joern_env()
    if bat is None or env is None:
        print("D-M5-2a 环境未就绪：joern.bat=%s jre=%s"
              % (bat, env and env["JAVA_HOME"]))
        return False
    os.makedirs(OUT, exist_ok=True)
    sc = os.path.join(OUT, "_ver.sc")
    with open(sc, "w", encoding="utf-8") as f:
        f.write('println("VER_PROBE_OK")\n')
    rc, out = _run(["cmd", "/c", bat, "--script", sc], env, 480)
    hit = re.findall(r"joern.*?v?\d+\.\d+\.\S*", out, re.I)
    ok = (rc == 0) and ("VER_PROBE_OK" in out)
    if ok:
        JOERN_VERSION = hit[0] if hit else "banner(版本行未解析，probe 通过)"
    else:
        rc2, out2 = _run(["cmd", "/c", bat, "--version"], env, 120)
        if rc2 == 0 and out2.strip():
            ok = True
            JOERN_VERSION = out2.strip().splitlines()[-1]
    print("D-M5-2a（joern 在便携 JRE 跑通，JAVA_HOME 按调用注入）：%s"
          % ("咬合" if ok else "不咬合"))
    if ok:
        print("    version: %s" % JOERN_VERSION.strip())
    else:
        print("    rc=%d out=%r" % (rc, out[:300]))
    return ok


# --------------------------------------------------------------- Joern 侧 --

_DUMP_TMPL = """importCpg("%s")
cpg.call.filter(_.callee.size > 0).foreach { c =>
  c.callee.foreach { ct =>
    println("EDGE\\t" + c.method.fullName + "\\t" + c.method.filename + "\\t" +
      c.method.lineNumber.getOrElse(-1) + "\\t" + ct.fullName + "\\t" +
      ct.filename + "\\t" + ct.lineNumber.getOrElse(-1))
  }
}
println("DUMP_DONE")
"""


def _run_joern(tag, target, cpg_path):
    """joern-parse + 调用边 dump。返回解析后的边列表或 None。"""
    env = _joern_env()
    os.makedirs(OUT, exist_ok=True)
    # ① joern-parse
    bat = _find_bat("joern-parse")
    if bat is None:
        print("[%s] joern-parse.bat 未找到" % tag)
        return None
    r_rc, parse_log = _run(["cmd", "/c", bat, os.path.abspath(target),
                            "--output", cpg_path], env, 3600, cwd=OUT)
    with open(os.path.join(OUT, "parse_%s.log" % tag), "w",
              encoding="utf-8", errors="replace") as f:
        f.write(parse_log)
    if r_rc != 0:
        print("[%s] joern-parse rc=%d（详见 m5_e2/parse_%s.log）"
              % (tag, r_rc, tag))
        return None
    cpg_real = cpg_path                              # 输出名可能被 joern 加 .bin
    if not os.path.isfile(cpg_real):
        if os.path.isfile(cpg_path + ".bin"):
            cpg_real = cpg_path + ".bin"
        else:
            print("[%s] joern-parse 未产出 CPG（详见 m5_e2/parse_%s.log）" % (tag, tag))
            return None
    # ② dump 脚本（cpg 路径烤进脚本，规避 --param API 差异）
    sc = os.path.join(OUT, "dump_%s.sc" % tag)
    with open(sc, "w", encoding="utf-8") as f:
        f.write(_DUMP_TMPL % cpg_real.replace("\\", "/"))
    jbat = _find_bat("joern")
    r_rc2, out2 = _run(["cmd", "/c", jbat, "--script", sc], env, 3600,
                       cwd=OUT)
    with open(os.path.join(OUT, "dump_%s.log" % tag), "w",
              encoding="utf-8", errors="replace") as f:
        f.write(out2)
    edges = []
    for line in out2.splitlines():
        if line.startswith("EDGE\t"):
            p = line.split("\t")
            if len(p) == 7:
                edges.append((p[1], p[2], p[3], p[4], p[5], p[6]))
    done = "DUMP_DONE" in out2
    print("[%s] joern-parse ok ｜ call 边（resolved callee）%d 条 ｜ dump %s"
          % (tag, len(edges), "完整" if done else "**未跑完（截断？）**"))
    return edges if done else None


# --------------------------------------------------------------- 映射与读数 --

def _norm_fn(fn, target, files_set):
    """Joern filename → 相对 target 的 posix 路径（绝对剥前缀 + 后缀对齐宇宙）。"""
    fn = (fn or "").replace("\\", "/")
    t = os.path.abspath(target).replace("\\", "/").rstrip("/") + "/"
    rel = fn[len(t):] if fn.startswith(t) else fn
    if rel in files_set:
        return rel
    for f in sorted(files_set, key=len, reverse=True):
        if rel.endswith("/" + f):
            return f                            # Joern 多带目录前缀的情况
    return rel


def topos_side(root, lang):
    """主链路同一抽取器（space.py 装配件，禁另造）。返回 (units, call_set)。"""
    if lang == "py":
        us = units_mod.discover_units(root)
        ly = _extract_layers(root, us)
    else:
        us = langjs.discover_units_js(root)
        ly = langjs.extract_layers_js(root, us)
    return us, set(ly["call"])


def crosscheck(tag, target, joern_edges, root, lang):
    """映射 → precision/recall 读数。返回 dict。"""
    units, T = topos_side(root, lang)
    files_set = {u["file"] for u in units}
    keymap = {}
    for i, u in enumerate(units):
        keymap.setdefault((u["file"], u["lineno"]), i)
    spans = {}                                       # file → [(a,b,idx)]
    for i, u in enumerate(units):
        spans.setdefault(u["file"], []).append(
            (u["lineno"], u["end_lineno"], i))
    for f in spans:
        spans[f].sort(key=lambda x: (x[1] - x[0], x[0]))
    n_exact = n_contain = 0

    def unit_of(fn, ln):
        """Joern 方法声明点 → topos 单元 idx（精确行 → 最小包含）或 None。"""
        nonlocal n_exact, n_contain
        rel = _norm_fn(fn, target, files_set)
        if rel not in files_set:
            return None
        try:
            ln_i = int(float(ln))
        except ValueError:
            return None
        if (rel, ln_i) in keymap:
            n_exact += 1
            return keymap[(rel, ln_i)]
        for a, b, i in spans.get(rel, []):           # 已按跨度升序 → 首个包含即最小
            if a <= ln_i <= b:
                n_contain += 1
                return i
        return None

    Gm, n_unmapped = set(), 0                        # Gm = 可映射金标
    seen_caller = {}
    for cf, cfl, cl, tf, tfl, tl in joern_edges:
        ci, ti = unit_of(cfl, cl), unit_of(tfl, tl)
        if ci is None or ti is None:
            n_unmapped += 1
            continue
        seen_caller[ci] = seen_caller.get(ci, 0) + 1
        if ci == ti:
            continue                                 # 递归自环：topos 边语言无自环
        Gm.add((min(ci, ti), max(ci, ti)))
    inter = T & Gm
    prec = (len(inter) / len(T)) if T else 0.0
    rec = (len(inter) / len(Gm)) if Gm else 0.0
    if os.environ.get("M5E2_DEBUG"):
        print("[debug] Gm 成员：")
        for a, b in sorted(Gm):
            print("    %s -> %s" % (units[a]["id"], units[b]["id"]))
    miss = sorted(Gm - T)
    miss_sample = ["%s -> %s" % (units[a]["id"], units[b]["id"])
                   for a, b in miss[:12]]
    res = {
        "target": os.path.basename(os.path.normpath(target)),
        "lang": lang, "n_units_topos": len(units),
        "n_joern_edges_resolved": len(joern_edges),
        "n_gold_mapped": len(Gm), "n_gold_unmapped": n_unmapped,
        "n_topos_edges": len(T), "n_intersect": len(inter),
        "gold_pairs": ["%s -> %s" % (units[a]["id"], units[b]["id"])
                       for a, b in sorted(Gm)],
        "precision": round(prec, 4), "recall": round(rec, 4),
        "map_exact": n_exact, "map_contain": n_contain,
        "miss_in_universe": len(miss), "miss_sample": miss_sample,
    }
    print(TBL)
    print("E-M5-2[%s] ｜ %s（%s 后端）" % (tag, res["target"], lang.upper()))
    print(TBL)
    print("topos 单元 %d ｜ topos call 边 %d ｜ Joern 金标(resolved) %d ｜ "
          "可映射金标 %d ｜ 宇宙差边 %d"
          % (len(units), len(T), len(joern_edges), len(Gm), n_unmapped))
    print("映射：精确行 %d ｜ 包含兜底 %d" % (n_exact, n_contain))
    print("→ precision（topos 边可指认率，门 ≥0.80）：%.4f ｜ "
          "recall（报数不设门）：%.4f" % (prec, rec))
    if miss_sample:
        print("金标独有（前 %d 条，喂 v0.2 召回迭代）：" % len(miss_sample))
        for s in miss_sample:
            print("    - %s" % s)
    return res


def _load_dump(tag):
    """M5E2_REUSE=1：复用已有 dump 日志（Joern 侧产物与 topos 抽取器解耦）。"""
    log = os.path.join(OUT, "dump_%s.log" % tag)
    if not os.path.isfile(log):
        return None
    edges = []
    with open(log, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("EDGE\t"):
                p = line.rstrip("\n").split("\t")
                if len(p) == 7:
                    edges.append((p[1], p[2], p[3], p[4], p[5], p[6]))
    if not edges:
        return None
    print("[%s] 复用已有 dump：%d 条边" % (tag, len(edges)))
    return edges


def run_target(tag, target, lang):
    if os.environ.get("M5E2_REUSE"):
        joern_edges = _load_dump(tag)
        if joern_edges is not None:
            return crosscheck(tag, target, joern_edges, target, lang)
    cpg = os.path.join(OUT, "%s.cpg" % tag)
    joern_edges = _run_joern(tag, target, cpg)
    if joern_edges is None:
        return None
    return crosscheck(tag, target, joern_edges, target, lang)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    print("E-M5-2 Joern 离线金标校验（PREREG/M5 §2，对拍口径 v1.1）")
    print("=" * 66)
    a_ok = env_check()
    results, verdicts = {}, {}
    if mode in ("py", "both") and a_ok:
        results["py"] = run_target("py", PY_TARGET, "py")
    if mode in ("js", "both") and a_ok:
        results["js"] = run_target("js", JS_TARGET, "js")
    for k in ("py", "js"):
        r = results.get(k)
        if r is None:
            verdicts[k] = None
            continue
        verdicts[k] = r["precision"] >= 0.8
    print(TBL)
    if "py" in verdicts:
        print("D-M5-2b（Python 靶 precision ≥0.8，recall 报数）：%s"
              % ("咬合" if verdicts["py"] else "不咬合")
              + ("" if verdicts["py"] is None else
                 "  precision=%.4f recall=%.4f" % (results["py"]["precision"],
                                                   results["py"]["recall"])
                 if results["py"] else "（Joern 侧失败）"))
    if "js" in verdicts:
        print("D-M5-2c（JS 靶 precision ≥0.8，recall 报数）：%s"
              % ("咬合" if verdicts["js"] else "不咬合")
              + ("" if verdicts["js"] is None else
                 "  precision=%.4f recall=%.4f" % (results["js"]["precision"],
                                                   results["js"]["recall"])
                 if results["js"] else "（Joern 侧失败）"))
    dest = os.path.join(HERE, "m5_e2.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump({"schema": "m5-e2/1", "joern_version": JOERN_VERSION,
                   "results": {k: v for k, v in results.items() if v},
                   "judged": {"D_M5_2a": a_ok, "D_M5_2b": verdicts.get("py"),
                              "D_M5_2c": verdicts.get("js")}},
                  f, ensure_ascii=False, indent=1)
    print("→ %s" % dest)
    all_ok = a_ok and all(v is True for v in verdicts.values()) \
        and len(verdicts) == 2
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
