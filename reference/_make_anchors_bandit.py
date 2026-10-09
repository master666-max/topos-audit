# -*- coding: utf-8 -*-
"""
_make_anchors_bandit.py —— 从本地 reference/bandit 源码提取黑名单，转成 mini-lab 外置锚点清单。

输出：reference/anchors-bandit.json，格式 = [[tag, regex_str], ...]（与 coord_mini._load_patterns 对齐）。
tag 规则：calls → "sink:<bandit_name>"；imports → "import:<bandit_name>"。
一次转换工具，不进运行时。bandit 数据 SPDX Apache-2.0，转换产物保留其来源注释。
"""
import importlib.util
import json
import os
import re
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "bandit", "bandit")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def shim_bandit():
    # 伪造包壳，绕过会拉 stevedore 的 __init__.py
    for pkg_name, sub in (("bandit", ""), ("bandit.core", "core"),
                          ("bandit.blacklists", "blacklists")):
        m = types.ModuleType(pkg_name)
        m.__path__ = [os.path.join(PKG, sub)] if sub else [PKG]
        sys.modules[pkg_name] = m
    load_mod("bandit.core.constants", os.path.join(PKG, "core", "constants.py"))
    load_mod("bandit.core.utils", os.path.join(PKG, "core", "utils.py"))
    load_mod("bandit.core.issue", os.path.join(PKG, "core", "issue.py"))
    load_mod("bandit.blacklists.utils", os.path.join(PKG, "blacklists", "utils.py"))
    calls = load_mod("bandit.blacklists.calls", os.path.join(PKG, "blacklists", "calls.py"))
    imports = load_mod("bandit.blacklists.imports", os.path.join(PKG, "blacklists", "imports.py"))
    return calls.gen_blacklist()["Call"], imports.gen_blacklist()["Import"]


def qualnames_to_call_rx(qualnames):
    alts = [r"\b" + re.escape(q) + r"\s*\(" for q in qualnames]
    return "(?:%s)" % "|".join(alts)


def qualnames_to_import_rx(qualnames):
    alts = [r"\b" + re.escape(q) + r"\b" for q in qualnames]
    return "(?:%s)" % "|".join(alts)


def main():
    call_bl, import_bl = shim_bandit()
    out = []
    for e in call_bl:
        tag = "sink:%s" % e["name"]
        rx = qualnames_to_call_rx(e["qualnames"])
        re.compile(rx)  # 语法自检
        out.append([tag, rx])
    for e in import_bl:
        tag = "import:%s" % e["name"]
        rx = qualnames_to_import_rx(e["qualnames"])
        re.compile(rx)
        out.append([tag, rx])
    dst = os.path.join(HERE, "anchors-bandit.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("调用黑名单条目:", len(call_bl), " 导入黑名单条目:", len(import_bl))
    print("输出锚点总数:", len(out), "->", dst)
    print("tag 清单:", ", ".join(t for t, _ in out))
    # 与内置 12 类重叠检查
    sys.path.insert(0, os.path.join(HERE, "..", "mini-lab"))
    import coord_mini as cm
    builtin_tags = {t for t, _ in cm.ANCHOR_PATTERNS}
    new_tags = {t for t, _ in out}
    print("内置 12 类:", sorted(builtin_tags))
    print("被 bandit 覆盖的内置 tag:", sorted(builtin_tags & new_tags) or "（命名不同，见对照表）")


if __name__ == "__main__":
    main()
