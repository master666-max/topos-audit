# -*- coding: utf-8 -*-
"""_l4_field.py —— L4 实战采集（PREREG/L4-field.md 判据执行件）。

① RUN1 开池审查 24 单元回填 calib/gold_l4_field.csv（truth=0 确认良性，
   source_layer=RUN1-pool，unit_id 钉靶 commit 1885de1）；
② 负域抽查清单：从 v1.3 空间的池外（零覆盖区）分层随机抽 10 单元，
   生成 EXP/l4_field/spotcheck.md（用户人工裁决后另行入库）。
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from topos.calib.gold import GoldStandard                       # noqa: E402
from topos.core.units import is_test_unit                       # noqa: E402

COMMIT = "1885de1"
TARGET = "dsh-launcher"
GOLD = os.path.join(REPO, "calib", "gold_l4_field.csv")
SPACE = os.path.join(HERE, "run1_dsh", "d", "space.json")
OUT = os.path.join(HERE, "l4_field")

# RUN1 开池审查裁决（EXP/RUN1-dsh-findings.md / RUN1-dsh-final.md §3，源码级）
RUN1_ADJ = [
    ("dsh-accept.py", "run_py", 22, "良性（TOOLS 常量路径）"),
    ("dsh-fallback-heal.py", "kill_node", 87, "正面：PID 复用防误杀双复核"),
    ("dsh-fallback-heal.py", "heal_profile", 118, "正面：cmd_arg_safe 元字符闸"),
    ("dsh-fallback-heal.py", "clean_pnpm_leftovers", 226, "良性（守卫到位）"),
    ("dsh-fallback-heal.py", "scan", 240, "良性（守卫到位）"),
    ("dsh-launcher.py", "kill_leftover", 163, "正面：同款双复核"),
    ("dsh-launcher.py", "run_heal", 193, "良性（TOOLS 常量）"),
    ("dsh-launcher.py", "_spawn_bg_and_wait", 467, "信任边界注记（config 驱动，设计功能）"),
    ("dsh-launcher.py", "run_plugins", 654, "良性（TOOLS 常量）"),
    ("dsh-launcher.py", "action_check", 746, "良性（600s 超时守卫）"),
    ("dsh-plugins.py", "run_heal", 741, "良性（TOOLS 常量）"),
    ("dsh_env.py", "_run", 66, "良性（永不抛封装，设计正面）"),
    ("dsh_env.py", "image_names", 251, "良性"),
    ("dsh_env.py", "pid_alive", 288, "良性"),
    ("dsh_env.py", "port_excluded", 862, "良性"),
    ("dsh_tests.py", "expect", 58, "测试代码（forman 深点，无生产影响）"),
    ("dsh_tests.py", "t_run_heal", 536, "测试代码"),
    ("dsh_tests.py", "_load_launcher", 851, "测试代码"),
    ("dsh_tests.py", "t_safemode_roundtrip", 1200, "测试代码"),
    ("dsh_tests.py", "t_safemode_guards", 1237, "测试代码"),
    ("dsh_tests.py", "t_update_cli_update", 1722, "测试代码"),
    ("dsh-launcher.py", "_action_start_impl", 251, "可维护性注记（170 行编排）"),
    ("dsh-plugins.py", "main", 837, "可维护性注记（185 行 CLI 分发）"),
    ("dsh_env.py", "discover_start_cmds", 903, "信任链节点（discover→Popen）"),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    # ① RUN1 回填
    gold = GoldStandard(GOLD)
    dup = 0
    for fname, func, ln, verdict in RUN1_ADJ:
        uid = "%s@%s/%s::%s:%d" % (TARGET, COMMIT, fname, func, ln)
        try:
            gold.add(uid, "0", "", "RUN1 开池审查：" + verdict,
                     annotator="AI 预审+用户督导（RUN1 会话）",
                     source_layer="RUN1-pool")
        except ValueError:
            dup += 1
    gp = gold.save()
    st = gold.stats()
    print("① 回填：%s ｜ %s ｜ 重复拒绝 %d" % (gp, st, dup))

    # ② 负域抽查清单：v1.3 空间的池外单元，分层（按文件）随机 10 个
    with open(SPACE, encoding="utf-8") as f:
        d = json.load(f)
    units = d["units"]
    in_pool = set()
    for _nm, ms in d["pool_members"]:
        in_pool |= {int(i) for i in ms}
    outside = [i for i in range(len(units)) if i not in in_pool]
    by_file = {}
    for i in outside:
        by_file.setdefault(units[i].split("::")[0], []).append(i)
    rng = random.Random(20261010)
    picks = []
    files = sorted(by_file)
    while len(picks) < 10 and by_file:
        for f in list(files):
            if len(picks) >= 10:
                break
            if by_file.get(f):
                picks.append((f, by_file[f].pop(rng.randint(0,
                              len(by_file[f]) - 1))))
            else:
                files.remove(f)
    md = ["# L4 负域抽查清单（RUN1 池外零覆盖区，分层随机 n=%d）" % len(picks),
          "",
          "> 每单元 ~1–2 分钟：读源码，判「有无缺陷」→ 填 0/1/无法判定。",
          "> 裁决后交回，入库 gold_l4_field.csv（source_layer=RUN1-spot）。",
          ""]
    for f, i in picks:
        md.append("## %s" % units[i])
        md.append("```python")
        md.append("(源码见 tools/repos/dsh-launcher@%s)" % COMMIT)
        md.append("```")
        md.append("- 判定：[ ] 良性(0)  [ ] 缺陷(1)  [ ] 无法判定")
        md.append("")
    with open(os.path.join(OUT, "spotcheck.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("② 负域抽查清单：EXP/l4_field/spotcheck.md（%d 单元，池外共 %d）"
          % (len(picks), len(outside)))
    return 0


if __name__ == "__main__":
    import json
    import random
    raise SystemExit(main())
