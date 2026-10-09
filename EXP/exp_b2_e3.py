# -*- coding: utf-8 -*-
"""
EXP/exp_b2_e3.py —— E-B2-3 变异注入召回下界（L2）。
判据（PREREG/B2 v1.0）：①mutation score 可复算 ②干净版零误杀
③至少 3 类算子的变异体可被 ≥1 个信号源捕获（否则该算子登记盲区）。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topos.calib.mutate import OPS, mutant, count_sites, run_tests  # noqa: E402
from topos.calib.mutate import DROP_CALL_WHITELIST  # noqa: E402

# ---- 合成目标仓（含可变异位点） ----
TARGET = '''\
LIMIT = 10


def validate(x):
    return 0 <= x <= LIMIT


def clamp(x, lo=0, hi=LIMIT):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def scale(values, factor=2):
    out = []
    for v in values:
        out.append(v * factor)
    return out


def normalize(items):
    total = 0
    for it in items:
        total += it
    if total <= 0:
        return []
    return [it / total for it in items]


def safe_take(seq, n):
    if n > len(seq):
        return seq[:]
    return seq[:n]


def pipeline(values):
    for v in values:
        validate(v)
    return scale(values)
'''

TESTS = [
    ("clamp", (-1,), 0),
    ("clamp", (25,), 10),
    ("clamp", (5,), 5),
    ("scale", ([1, 2],), [2, 4]),
    ("normalize", ([1, 1],), [0.5, 0.5]),
    ("normalize", ([0, 0],), []),
    ("safe_take", ([1, 2, 3], 5), [1, 2, 3]),
    ("safe_take", ([1, 2, 3], 2), [1, 2]),
    ("validate", (5,), True),
    ("pipeline", ([1, 2],), [2, 4]),
]

HERE = os.path.dirname(os.path.abspath(__file__))
ANCHORS = os.path.join(os.path.dirname(HERE), "reference", "anchors-bandit.json")


def src_call_count(src, names):
    """信号源 S3：安全校验函数名在源码中的调用计数（结构型信号，非正则）。"""
    try:
        import ast
        tree = ast.parse(src)
    except SyntaxError:
        return 0
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            nm = getattr(fn, "id", None) or getattr(fn, "attr", None)
            if nm in names:
                n += 1
    return n


def load_anchor_patterns():
    import json
    with open(ANCHORS, encoding="utf-8") as f:
        return [(t, re.compile(rx)) for t, rx in json.load(f)]


def main():
    print("=== E-B2-3 变异注入召回下界 ===")
    ok, fails = run_tests(TARGET, TESTS)
    print("  干净版: 通过 %d/%d  失败=%s" % (ok, len(TESTS), fails))
    clean_ok = (ok == len(TESTS) and not fails)

    sites = count_sites(TARGET)
    print("  可变异位点: %s" % sites)
    pats = load_anchor_patterns()
    base_calls = src_call_count(TARGET, DROP_CALL_WHITELIST)

    rows = []
    total = killed = 0
    for op in OPS:
        n = sites[op]
        k = killed_by_anchor = killed_by_call = 0
        for i in range(n):
            src, hit = mutant(TARGET, op, nth=i)
            if not hit:
                continue
            total += 1
            passed, _f = run_tests(src, TESTS)
            if passed < len(TESTS):
                k += 1
            if any(p.search(src) for _t, p in pats):
                killed_by_anchor += 1
            if op == "drop_call" and src_call_count(src, DROP_CALL_WHITELIST) < base_calls:
                killed_by_call += 1
        killed += k
        rows.append((op, n, k, killed_by_anchor, killed_by_call))

    print("  %-17s %6s %6s %10s %12s" % ("算子", "变异体", "被杀", "锚点捕获", "调用计数捕获"))
    for op, n, k, ka, kc in rows:
        print("  %-17s %6d %6d %10d %12d" % (op, n, k, ka, kc))
    score = killed / total if total else 0.0
    print("  mutation score = %d/%d = %.3f（只作召回**下界**）" % (killed, total, score))

    caught_ops = sum(1 for op, n, k, ka, kc in rows if k > 0)
    print("  被测试执行（真值锚）杀到的算子类: %d/5" % caught_ops)
    print("  被静态信号源看见的算子类: 锚点正则=%d, 调用计数=%d"
          % (sum(1 for r in rows if r[3] > 0), sum(1 for r in rows if r[4] > 0)))

    ok1 = total > 0 and isinstance(score, float)
    ok2 = clean_ok
    ok3 = caught_ops >= 3
    print("=" * 62)
    print("判据① score 可复算: %s  ② 干净版零误杀: %s  ③ ≥3 类算子可被捕获: %s"
          % (ok1, ok2, ok3))
    verdict = ok1 and ok2 and ok3
    print("E-B2-3 判定: %s" % ("咬合" if verdict else "不咬合"))
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
