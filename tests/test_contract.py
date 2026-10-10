# -*- coding: utf-8 -*-
"""tests/test_contract.py —— 契约自检 pytest 入口（2026-10-10 落位修正）。

工单 W2 原文要求「合成仓断言搬进 tests/」；B1 实际落在 topos/selftest.py
（功能等价）。本 shim 提供标准 pytest 入口：`pytest tests/` 等价于
`python -m topos.selftest`。断言本体仍单源在 topos/selftest.py（禁止平行实现）。
"""
import contextlib
import io

from topos.selftest import run_all


def test_contract_selftest():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok, total = run_all(verbose=False)
    assert ok == total, "selftest %d/%d\n%s" % (ok, total, buf.getvalue())
