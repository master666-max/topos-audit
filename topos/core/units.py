# -*- coding: utf-8 -*-
"""
topos.core.units —— 代码单元发现（函数/方法粒度，AST 驱动）。
搬迁自 mini-lab/coord_mini.discover_units（selftest 11/11 已验证件），逻辑零改动。
"""
import ast
import os


def discover_units(root):
    """walk 目录 → 每个函数/方法一个 Unit{id,file,name,lineno,end_lineno,loc,src}。"""
    units = []
    for dirpath, _dirs, files in os.walk(root):
        if any(seg in dirpath for seg in (".git", "__pycache__", ".workbuddy")):
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root).replace("\\", "/")
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    src = f.read()
                tree = ast.parse(src)
            except SyntaxError:
                continue
            lines = src.splitlines()
            cls_of = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in ast.walk(node):
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            cls_of[item.lineno] = node.name
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qual = cls_of.get(node.lineno, node.name)
                    if qual == node.name and node.lineno in cls_of:
                        qual = cls_of[node.lineno] + "." + node.name
                    seg = "\n".join(lines[node.lineno - 1: node.end_lineno])
                    units.append({
                        "id": "%s::%s:%d" % (rel, qual, node.lineno),
                        "file": rel, "name": qual,
                        "lineno": node.lineno, "end_lineno": node.end_lineno,
                        "loc": node.end_lineno - node.lineno + 1,
                        "src": seg,
                    })
    return units
