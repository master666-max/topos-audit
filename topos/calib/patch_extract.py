# -*- coding: utf-8 -*-
"""
topos.calib.patch_extract —— L1 执行正样本：修复补丁 → 函数级正样本。
管线：bug_patch.txt (unified diff) → (file, 旧文件改动行区间) → 抓 bug 版单文件源码
      → AST 定位"包含改动行的函数" → 正样本 (unit_id, file, func, lines)。
执行验证证据：BugsInPy 官方 <project>-pass/fail.txt 中该 bug 的记录（上游执行，本机未复跑）。

诚实条款：
  - 测试文件（path 含 test）的改动**不算**正样本（那是测试代码不是被测代码）；
  - 未改动函数 = 未标注（None），禁止标 0；
  - 抓取失败的 patch 计入 fetch_fail，不静默吞掉。
"""
import ast
import os
import re
import urllib.request

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
TIMEOUT = 25


def parse_patch_hunks(text):
    """→ [(path, [old_line_no, ...])]，只取**被删除行（-）**在旧文件（bug 版）中的行号。
    精度条款（ADR）：不取整个 hunk 行范围（含上下文），否则会过度标记——
    v1.0 实现曾把 hunk 上下文行所属的函数全部误标为正样本（black bugs/15 抽核发现）。"""
    res = []
    cur_path = None
    old_ln = None
    dels = []
    for line in text.splitlines():
        if line.startswith("+++ "):
            _flush(res, cur_path, dels)
            cur_path = line[4:].strip()
            if cur_path.startswith("b/"):
                cur_path = cur_path[2:]
            old_ln = None
            dels = []
            continue
        m = HUNK.match(line)
        if m and cur_path:
            old_ln = int(m.group(1))
            continue
        if old_ln is None or cur_path is None:
            continue
        if line.startswith("-") and not line.startswith("---"):
            dels.append(old_ln)
            old_ln += 1
        elif line.startswith("+") or line.startswith("\\"):
            pass                      # 新增行 / "\ No newline" 不推进旧文件行号
        else:
            old_ln += 1               # 上下文行：两侧同步推进
    _flush(res, cur_path, dels)
    return res


def _flush(res, path, dels):
    if path and dels:
        res.append((path, sorted(set(dels))))


def fetch_source(github_url, commit, path, cache=None, retries=2):
    """抓 bug 版单文件源码（raw.githubusercontent，走 gh-proxy）。
    retries：网络抖动超时默认重试 2 次（E-B2-2 实测单文件抓取偶发 read timeout）。"""
    key = (github_url, commit, path)
    if cache is not None and key in cache:
        return cache[key]
    raw = (github_url.replace("https://github.com/", "https://raw.githubusercontent.com/")
           + "/%s/%s" % (commit, path))
    url = "https://gh-proxy.com/" + raw
    last_err = "unknown"
    for _ in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
                src = r.read().decode("utf-8", errors="replace")
            res = (src, None)
            if cache is not None:
                cache[key] = res
            return res
        except Exception as e:
            last_err = str(e)
    res = (None, last_err)
    if cache is not None:
        cache[key] = res
    return res


def funcs_covering(src, lines):
    """AST 定位：返回 [{"name","lineno","end_lineno"}]，其行范围覆盖任一被删除行。"""
    if not src:
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    cls_of = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in ast.walk(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cls_of[item.lineno] = node.name
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            hit = any(node.lineno <= ln <= node.end_lineno for ln in lines)
            if hit:
                qual = node.name
                c = cls_of.get(node.lineno)
                if c:
                    qual = "%s.%s" % (c, node.name)
                out.append({"name": qual, "lineno": node.lineno,
                            "end_lineno": node.end_lineno})
    return out


def is_test_path(path):
    low = path.lower()
    return any(s in low for s in ("test", "tests/", "conftest", "_test"))


def extract_bug(project_dir, bug_id, github_url, cache=None):
    """单个 bug → {"functions": [...], "fetch_fail": [...], "files": [...] }。"""
    bug_dir = os.path.join(project_dir, "bugs", str(bug_id))
    pfile = os.path.join(bug_dir, "bug_patch.txt")
    if not os.path.exists(pfile):
        return None
    with open(pfile, encoding="utf-8", errors="replace") as f:
        text = f.read()
    info = {}
    ipath = os.path.join(bug_dir, "bug.info")
    if os.path.exists(ipath):
        with open(ipath, encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    info[k] = v.strip('"')
    commit = info.get("buggy_commit_id", "")
    hunks = parse_patch_hunks(text)
    by_file = {}
    for path, lns in hunks:          # lns = 该文件被删除行的行号列表（展平）
        by_file.setdefault(path, []).extend(lns)
    funcs, fails, files = [], [], []
    for path, rngs in by_file.items():
        if is_test_path(path):
            continue
        src, err = fetch_source(github_url, commit, path, cache=cache)
        files.append(path)
        if src is None:
            fails.append({"path": path, "error": err})
            continue
        for fn in funcs_covering(src, rngs):
            fn = dict(fn)
            fn["file"] = path
            fn["unit_id"] = "%s::%s:%d" % (path, fn["name"], fn["lineno"])
            fn["commit"] = commit
            fn["ranges"] = rngs
            funcs.append(fn)
    return {"bug_id": bug_id, "commit": commit, "test_file": info.get("test_file", ""),
            "functions": funcs, "fetch_fail": fails, "files": files}
