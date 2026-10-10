# -*- coding: utf-8 -*-
# B6 §0 S1 复算载荷（草案自带，落盘执行）
import json, os, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from topos.space import Space

LAYERS = ("call", "data", "control", "return", "vardep")

def mf(alpha, path):
    d = {"version": 3, "layers": alpha,
         "fields": [{"name": "forman", "layer": "G", "method": "graph", "params": {}}],
         "slicers": [{"name": "f:low", "field": "forman", "op": "quantile_le", "q": 0.33}],
         "pools": [{"name": "p_f", "expr": "f:low"}],
         "constraints": {"min_pool_size": 1}}
    json.dump(d, open(path, "w", encoding="utf-8"))
    return path

def run(base, tag, alpha):
    p = mf(alpha, os.path.join(tempfile.mkdtemp(prefix="b6s1-"), "mf.json"))
    sp = Space(base, p)
    curv = sp.fields["forman"]
    return {"tag": tag, "edges": len(sp.fused),
            "degsum": sum(len(v) for v in sp.adj.values()),
            "curv_sum": round(sum(v for v in curv.values() if v is not None), 4),
            "pools": [sorted(m) for _n, m in sp.rows],
            "fused_set": sorted(sp.fused)}

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "topos", "core")
    ones = run(base, "all-1.0", {t: 1.0 for t in LAYERS})
    zeros = run(base, "all-0.0", {t: 0.0 for t in LAYERS})
    skew = run(base, "skew", {"call": 1.0, "data": 100.0, "control": 100.0,
                              "return": 100.0, "vardep": 100.0})
    for r in (ones, zeros, skew):
        print(r["tag"], r["edges"], r["degsum"], r["curv_sum"], r["pools"])
    print("edge sets identical?",
          ones["fused_set"] == zeros["fused_set"] == skew["fused_set"])
