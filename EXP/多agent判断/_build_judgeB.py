"""Build the judgeB L4-control adjudication artifacts.

Inputs : EXP/_adj_batch1.json + EXP/_adj_batch2.json  (my frozen per-unit verdicts)
         EXP/B2-E4-sample.csv @ HEAD blob              (roster; read from the
                                                        COMMITTED blob so a
                                                        concurrent writer cannot
                                                        shift it under us)
Outputs: EXP/B2-E4-adjudication-judgeB-qwen-3.8max.jsonl
         EXP/B2-E4-adjudication-judgeB-qwen-3.8max.csv
         EXP/B2-E4-adjudication-judgeB-qwen-3.8max.md

Deliberately NOT written: EXP/B2-E4-sample.csv, EXP/B2-E4-adjudication.*,
EXP/B2-E4.md -- those are already occupied by a second producer (see report).
Deliberately NOT read  : EXP/B2-E4-modelside.* (PREREG/B2.md A5 seal).
"""
import csv, hashlib, io, json, math, os, re, subprocess, sys, collections

OUT = sys.__stdout__
def say(*a):
    OUT.write(" ".join(str(x) for x in a) + "\n"); OUT.flush()

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATE = "2026-10-10"
# Identity convention in this workspace (see B2-E4-adjudication-PROVENANCE-NOTE.md §4):
#   judgeA -> L4-control:Otto(single-rater,no-kappa)
#   judgeC -> ai:dsh-deepseek-flash
# The FILENAME suffix stays `judgeB` because other producers reference these exact
# paths (_xjudge_compare_judgeC.py, PROVENANCE-NOTE §1/§2/§4, judgeC-crosscheck).
# The MODEL identity travels in `annotator`, which is where the other judges put it.
# Model string supplied by the user 2026-10-10; not self-verified by this agent.
MODEL_TAG = "qwen-3.8max"
ANNOTATOR = "ai:%s(L4-control,judgeB,single-rater,no-kappa)" % MODEL_TAG
# 2026-10-10 user ruling "全改，文件名也要": the model tag now goes in the FILENAME
# too. `judgeB` is KEPT in the name because other producers' prose cites it and
# because it is the workspace's judge index (judgeA=Otto, judgeC=dsh-deepseek-flash).
PRE = "B2-E4-adjudication-judgeB-" + MODEL_TAG

# ---------------------------------------------------------------- roster (HEAD)
head = subprocess.run(["git", "cat-file", "blob", "HEAD:EXP/B2-E4-sample.csv"],
                      capture_output=True, cwd=REPO, check=True).stdout.decode("utf-8")
roster = {int(r["seq"]): r for r in csv.DictReader(head.splitlines())}
assert len(roster) == 100, len(roster)
HEAD_SHA = hashlib.sha256(head.encode()).hexdigest()
say("roster read from HEAD blob: %d rows, sha256=%s" % (len(roster), HEAD_SHA[:16]))

# ---------------------------------------------------------------- verdicts
V = {}
for f in ("_adj_batch1.json", "_adj_batch2.json"):
    for r in json.load(open(os.path.join(HERE, f), encoding="utf-8")):
        assert r["seq"] not in V, "duplicate seq %s" % r["seq"]
        V[r["seq"]] = r
assert sorted(V) == list(range(1, 101)), "verdicts must cover 1..100"
say("loaded verdicts: %d" % len(V))

# ------------------------------------------------- post-hoc revisions (logged)
REV = []   # (seq, field, old, new, why)

def revise(seq, field, new, why):
    old = V[seq].get(field)
    if old != new:
        V[seq][field] = new
        REV.append((seq, field, old, new, why))

# --- two retractions produced by execution verification against the real stdlib
revise(98, "truth", "0",
       "执行验证证伪：生产路径 find_tzfile(key) 用默认 _base=_TEST_PATH，实测其值为 "
       "'_' + os.sep（2 字符且以分隔符结尾），故 normpath(join(_base,'../x-leaks/y')) 会整体弹出该合成根、"
       "不再以 _base 开头 => 攻击被第三道检查拒掉。实测正对照 Europe/London=ACCEPTED、"
       "负对照 ../etc/passwd=REJECTED、攻击 ../zoneinfo-leaks/secret=REJECTED。"
       "原判 1 是用显式传入的 _base='/usr/share/zoneinfo' 测出来的，而该配置在生产中不存在（_base 是下划线私有的测试钩子，"
       "_TEST_PATH 用后即 del）。前缀无边界这一弱点本身为真，但仅在调用方显式传入不以分隔符结尾的 _base 时才可达"
       "（实测传入不以分隔符结尾的 Windows 型 _base 时攻击被 ACCEPTED，补上尾分隔符后 REJECTED），故降级为加固建议而非缺陷。")
V[98]["defect_type"] = ""
V[98]["rule"] = "R0"
V[98]["verification"] = "exec-refuted"
V[98]["retracted_from"] = "1"
V[98]["note"] = (
    "撤回记录（原判 1/security，经对真 3.13.12 stdlib 执行验证后改判 0）。"
    "原判机理：第三道检查 resolved.startswith(_base) 是裸前缀比较、缺分隔符边界，"
    "故名字以 _base 为前缀的同级目录会被放行（我用 posixpath 与 ntpath 重放均得到 "
    "'../zoneinfo-leaks/secret' -> '/usr/share/zoneinfo-leaks/secret' 通过）。"
    "证伪：生产唯一调用点是 find_tzfile -> _validate_tzfile_path(key)，不传 _base，"
    "默认 _base=_TEST_PATH=normpath(join('_','_'))[:-1]，实测为 '_' + os.sep —— 以分隔符结尾，"
    "startswith 因此天然带边界；且合成根只有一个分量，任何 '..' 都会整体弹出它。"
    "实测（真函数、含正反对照）：Europe/London ACCEPTED（正对照通过，证明尺子有效）、"
    "../etc/passwd REJECTED（负对照通过，证明尺子有分辨力）、../zoneinfo-leaks/secret REJECTED、"
    "../_x/secret REJECTED、a/../../secret 被第二道长度检查 REJECTED。"
    "残留（记为加固建议，非缺陷）：显式传入不以分隔符结尾的 _base 时弱点确实可达——"
    "实测 _base='C:\\tz\\zoneinfo' 放行 '../zoneinfo-leaks/secret'，而 _base='C:\\tz\\zoneinfo\\' 拒绝。"
    "由于 _base 是下划线私有参数、_TEST_PATH 用后即 del、模块内唯一调用点不传该参数，"
    "此状态在生产不可达，故按 RULE:17“可信输入或状态”不成立。"
    "方法论教训（写进报告）：我先后两次用 '/' 型 _base 在 Windows 上测这个函数，"
    "结果连正对照 Europe/London 都被拒——分隔符不一致的尺子会把“靶没问题”与“尺子坏了”混为一谈；"
    "只有带上正对照才分得开。")

revise(80, "truth", "0",
       "执行验证证伪：①实测五种真实启动方式（python -c / python script.py / python -m mod / "
       "python -I -c / python - 标准输入）下 sys.modules['__main__'] 全部 hasattr('__spec__')==True"
       "（取值为 None 或 ModuleSpec），故 main_module.__spec__ 在生产不会抛 AttributeError；"
       "我原来的复现是把属性硬删掉造出来的，不是自然可达状态。②实测 multiprocessing.process.ORIGINAL_DIR "
       "在导入期即为绝对路径字符串（非 None），spawn.py 内唯一赋值点是子进程侧 "
       "process.ORIGINAL_DIR = data['orig_dir']，故 sys_path[i]=None 不可达。")
V[80]["defect_type"] = ""
V[80]["rule"] = "R0"
V[80]["verification"] = "exec-refuted"
V[80]["retracted_from"] = "1"
V[80]["note"] = (
    "撤回记录（原判 1/logic，经执行验证后改判 0）。原判两条机理均被证伪。"
    "①未守卫的 main_module.__spec__：实测 python -c / script.py / -m / -I -c / stdin 五种启动方式下 "
    "__main__ 恒有 __spec__ 属性（值为 None 或 ModuleSpec），故 AttributeError 不可达；"
    "我原先的复现靠 delattr 硬造，属夹具造出来的状态而非靶上真实存在的状态。"
    "②sys_path[i] = process.ORIGINAL_DIR 可能写入 None：实测 ORIGINAL_DIR 在 multiprocessing.process "
    "导入期就是绝对路径字符串，spawn.py 内唯一赋值点在子进程侧 prepare()，父进程路径上不会为 None，故不可达。"
    "残留观察（不升格）：同一函数对两个同类 dunder 一个用 getattr(...,'__file__',None) 守卫、"
    "对 __spec__ 直接取属性，风格上不对称；以及 'process.ORIGINAL_DIR is not None' 这句守卫在当前实现下恒真，"
    "属防御性冗余。两者都不产生行为偏离。")

# --- two shim reclassifications (interpretive rule stated in the report)
SHIM_WHY = ("N-SHIM 解释性判据（写进报告）：仅当委托对象的契约无法从工作簿得知时才记 N-SHIM。"
            "os.spawnv 是内建（实测 type=builtin_function_or_method，os.py 从 nt 导入）、"
            "socket.socket.accept 的文档串实测为 'accept() -> (socket object, address info)'，"
            "两者契约均为已知，故“这次委托是否兑现了本单元自己的文档串”是可判的，应给 0 而非 None。")
revise(19, "truth", "0", SHIM_WHY)
V[19]["rule"] = "R0"
V[19]["note"] = ("全源可见（8/8）。文档串承诺 spawnl(mode, file, *args) 用子进程执行 file 并返回 pid/退出码/-SIG，"
                 "实现为 return spawnv(mode, file, args)——把可变参数收成元组后交给 spawnv，正是 spawnl 与 spawnv "
                 "的唯一语义差别，委托正确。委托对象 os.spawnv 是内建（已实测），契约已知，故本单元可判、给 0。"
                 "改判说明：初判 None/N-SHIM，按“委托契约可知则照常判定”的解释性判据改为 0（N-SHIM 保留给 "
                 "#10/#22/#24 这类委托对象是项目内部逻辑、契约无法从工作簿得知的情形）。"
                 "锚点命中行 L4 是文档串散文里的 subprocess 一词，按 RULE:32 不作定向。")
revise(28, "truth", "0", SHIM_WHY)
V[28]["rule"] = "R0"
V[28]["note"] = ("全源可见（7/7）。文档串“Get the request and client address from the socket. May be overridden.”"
                 "所描述的返回形状，正是 socket.socket.accept 的文档契约（实测其 doc 首行为 "
                 "'accept() -> (socket object, address info)'），故委托正确、契约兑现。"
                 "文档串自称可被覆盖，UDPServer.get_request 确实是覆盖者。"
                 "改判说明：初判 None/N-SHIM，按同一解释性判据改为 0——委托对象是契约已知的标准库原语，"
                 "“这次委托对不对”可判。")

# --- three 1s whose mechanism was corrected / strengthened by execution
V[20]["defect_type"] = "error_handling"
V[20]["verification"] = "exec-confirmed-mechanism-corrected"
V[20]["note"] = (
    "机理经对真 pickle._Unpickler（工作簿采样的正是 pickle.py:1387 这个纯 Python 实现，"
    "不是 pickle.loads 默认走的 C 实现）执行验证后修正如下。"
    "确认成立：①头部短读泄漏非本族异常——实测给 _Unpickler 喂 2 字节流，抛的是 "
    "struct.error('unpack requires a buffer of 4 bytes')，不是 UnpicklingError；"
    "而 C 实现对同一条截断流抛的是 UnpicklingError('pickle data was truncated')，"
    "两个实现对同一畸形输入给出不同异常类型，纯 Python 侧泄漏了非 pickle 族异常，"
    "按 pickle 文档捕获 UnpicklingError/PickleError 的调用方会漏接。"
    "②载荷短读确实不校验长度——真源码为 self.append(self.read(len))，且实测 load_binbytes "
    "并未使用 pickle 里现成的 _readbytes 长度守卫；实测声明 100 字节而只给 3 字节时，"
    "load_binbytes 把 3 字节静默 append 了进去。"
    "修正（原判措辞不准，特此更正）：我原先写“静默存成截断对象、不报任何错”，这不准确——"
    "短读吃掉了流尾的 STOP 操作码，随后 load() 主循环 read(1) 得空而抛 EOFError，"
    "所以整体仍会失败，只是失败点是 EOFError 而非 UnpicklingError，且失败原因与真实原因（长度不足）无关。"
    "正对照已跑：良构 BINBYTES(3)+b'abc' 返回 b'abc'。"
    "综合：缺陷成立，性质是异常契约违背 + 纯 Python/C 两实现分歧，而非“完全无错”。")

V[26]["verification"] = "exec-confirmed"
V[26]["note"] = V[26]["note"] + (
    " 【执行验证已确认】实测 pydoc.TextRepr（真类，pydoc.py:1233；被测方法在 1259 行，"
    "工作簿源码与真文件逐字节相同）：正对照 object() -> '<object object>'；"
    "负对照 __repr__ 抛 ValueError -> 被吞并回落 '<BoomPlain instance>'（这是设计意图）；"
    "攻击 __repr__ 抛 KeyboardInterrupt -> 被吞，返回 '<BoomKI instance>'；"
    "攻击 __repr__ 抛 SystemExit -> 被吞，返回 '<BoomSE instance>'。"
    "即裸 except 确实把 BaseException 一并吃掉，Ctrl-C 与 sys.exit 都会被转成一段看起来正常的输出。")

V[96]["verification"] = "exec-confirmed"
V[96]["note"] = V[96]["note"] + (
    " 【执行验证已确认，并修正终末症状】真源码 addToZip 片段实测不含 islink、不含 realpath、"
    "不含 seen/visited 集合，且确实递归调用自身；实测 os.path.isdir(sub/loop)=True（跟随符号链接）。"
    "用真 CLI 跑 zipfile.main(['-c', out.zip, sub]) 于一个含 sub/loop -> sub 环的目录树、"
    "并把递归上限压到 300：进程 rc=1，终端症状不是 RecursionError 而是 "
    "FileNotFoundError [WinError 3]（路径 sub\\loop\\loop\\loop... 撞到 Windows MAX_PATH），"
    "且此时已留下一个 12,664 字节的半成品 zip。故原判“无限递归”成立，"
    "但我原先预测的 RecursionError 是错的终末症状：Windows 上先撞路径长度墙抛未捕获的 "
    "FileNotFoundError（裸 traceback、半成品归档），POSIX/深栈情形下才会是 RecursionError。"
    "两种终末症状都是未处理的异常从面向用户的 CLI 里裸奔出来。")

for s in (12, 25, 31, 33, 37, 55, 62, 93):
    V[s]["verification"] = "exec-confirmed"
V[12]["note"] += (" 【执行验证已确认】实测 imaplib.Commands 含 'COPY'（states=('SELECTED',)）与 'MOVE'，"
                  "uid() 源码确实硬编码 name='FETCH' 且不含 COPY/MOVE 分支，而非 UID 的 copy() 用的是 'COPY'。"
                  "原判所依赖的“Commands 含非 FETCH 响应命令”这一前提由外部知识变为实测事实。")
V[25]["note"] += (" 【执行验证已确认】临时造一个 submod.py 定义 __all__=['A'] 与 class A/class B，"
                  "再让 main_mod.py 写 from submod import *：pyclbr.readmodule_ex 的树给出 ['A','B']，"
                  "而同一导入在真运行时 dir() 只给出 ['A']。即 pyclbr 多报了一个运行时并不会绑定的名字，"
                  "机理与原判一致（只用 startswith('_') 这条“无 __all__ 时的回落规则”，没有 __all__ 分支）。")
V[31]["note"] += (" 【执行验证已确认】实调 TarInfo._proc_gnusparse_01：正对照 6 值 -> [(0,10),(20,30),(40,50)]；"
                  "攻击 5 值 '0,10,20,30,40' -> [(0,10),(20,30)]，第 5 个值 40 被静默丢弃且无报错；"
                  "攻击单值 '7' -> []；非数字 'abc' -> ValueError（isinstance(e, tarfile.TarError)=False）；"
                  "缺键 -> KeyError（同样不是 TarError）。")
V[33]["note"] += (" 【执行验证已确认】真源码里 except KeyboardInterrupt 的处理体实测就是 print(\"interrupted\\n\") 一句，"
                  "不含 sys.exit 也不含 raise；负对照 error() 确实以 sys.exit(1) 收尾。故中断走的是退出码 0 的正常收尾路径。")
V[37]["note"] += (" 【执行验证已确认】真源码的 except 元组实测为 (FileNotFoundError, subprocess.CalledProcessError, "
                  "PermissionError, NotADirectoryError)，不含 UnicodeDecodeError；且 raw_result.decode() 确实未带 errors= 参数。")
V[55]["note"] += (" 【执行验证已确认】实测 namedtuple('P',[1,2]) 抛 ValueError(\"...must be valid identifiers: '1'\")、"
                  "namedtuple(123,'x y') 抛 ValueError(\"...'123'\")，都不是代码自己声明的 TypeError；"
                  "正对照 namedtuple('P',['x','y']) 正常；负对照 namedtuple('P',['class']) 抛的是 keyword 那条 ValueError。"
                  "并已核实源码中 map(str, field_names) 的位置在 'must be strings' 检查之前，故该 TypeError 分支恒不可达。")
V[62]["note"] += (" 【执行验证已确认】真源码字面量实测为 \"local-part contains non-ASCII characters)\"，"
                  "且实调 get_local_part('café') 产出的 defects 里带着这条畸形文本："
                  "NonASCIILocalPartDefect('local-part contains non-ASCII characters)')。")
V[93]["note"] += (" 【执行验证已确认】实调 ElementTree.ElementInclude.include() 处理不带 href 的 "
                  "<xi:include parse='text'/>，抛的是 TypeError('expected str, bytes or os.PathLike object, "
                  "not NoneType')，不是 FatalIncludeError；负对照 parse='bogus' 则如契约所写抛 "
                  "FatalIncludeError(\"unknown parse type in xi:include tag ('bogus')\")。两相对照正是原判的机理。")

# --- N-SHIM interpretive rule recorded on the three retained shims
for s in (10, 22, 24):
    V[s]["note"] += (" 【N-SHIM 判据说明】本轮把 N-SHIM 限定为“委托对象是本仓内部逻辑、其契约无法从工作簿得知”；"
                     "若委托对象是契约已知的语言/标准库原语（如 #19 os.spawnv、#28 socket.accept、"
                     "#59 deque.extend、#75 map+str.strip、#79 Event.wait），则照常判定，因为"
                     "“这次委托是否兑现本单元自己的契约”是可判的。本单元属前者。")

# ---------------------------------------------------------------- stats
def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))

truth = collections.Counter(V[s]["truth"] for s in V)
by_stratum = collections.defaultdict(collections.Counter)
for s in V:
    by_stratum[roster[s]["stratum"]][V[s]["truth"]] += 1
rule_ct = collections.Counter(V[s]["rule"] for s in V)
dt_ct = collections.Counter(V[s]["defect_type"] for s in V if V[s]["defect_type"])
ver_ct = collections.Counter(V[s].get("verification", "not-execution-tested") for s in V)

say("\n=== FINAL judgeB distribution ===")
say("truth:", dict(truth), " total:", sum(truth.values()))
say("rule :", dict(rule_ct))
say("defect_type:", dict(dt_ct))
say("verification:", dict(ver_ct))
say("revisions applied: %d" % len(REV))
for r in REV:
    say("   #%d %s: %r -> %r" % (r[0], r[1], r[2], r[3]))

# ---------------------------------------------------------------- jsonl
recs = []
for s in range(1, 101):
    r = roster[s]; v = V[s]
    recs.append({
        "seq": s, "unit_id": r["unit_id"], "file": r["file"], "name": r["name"],
        "lineno": int(r["lineno"]), "stratum": r["stratum"],
        "truth": v["truth"], "defect_type": v["defect_type"], "rule": v["rule"],
        "note": v["note"], "annotator": ANNOTATOR, "date": DATE,
        "loc": int(r["loc"]), "truncated": bool(v.get("truncated")),
        "verification": v.get("verification", "not-execution-tested"),
        "retracted_from": v.get("retracted_from", ""),
        "obs_verified": bool(v.get("obs_verified", False)),
        "layer": "L4-control",
        "is_gold": False,
    })
jp = os.path.join(HERE, PRE + ".jsonl")
with open(jp, "w", encoding="utf-8", newline="\n") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
say("\nwrote %s (%d records, %d bytes, sha256=%s)"
    % (jp, len(recs), os.path.getsize(jp), hashlib.sha256(open(jp, "rb").read()).hexdigest()[:16]))

# ---------------------------------------------------------------- csv
cp = os.path.join(HERE, PRE + ".csv")
cols = ["seq", "unit_id", "file", "name", "lineno", "loc", "stratum", "truth",
        "defect_type", "rule", "verification", "retracted_from", "truncated",
        "obs_verified", "annotator", "date", "note"]
with open(cp, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in recs:
        w.writerow(r)
say("wrote %s (%d bytes)" % (cp, os.path.getsize(cp)))
json.dump({"revisions": [{"seq": a, "field": b, "old": c, "new": d, "why": e} for a, b, c, d, e in REV],
           "truth": dict(truth), "rule": dict(rule_ct), "defect_type": dict(dt_ct),
           "verification": dict(ver_ct),
           "by_stratum": {k: dict(v) for k, v in by_stratum.items()},
           "roster_head_sha256": HEAD_SHA, "annotator": ANNOTATOR, "date": DATE},
          open(os.path.join(HERE, PRE + "-stats.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
say("wrote %s-stats.json" % PRE)
say("\nper-stratum truth + Wilson 95% CI on the 1-rate:")
for st in ["random", "confluence", "anchor", "zero_cover"]:
    c = by_stratum[st]; n = sum(c.values())
    p, lo, hi = wilson(c["1"], n)
    pn, ln_, hn = wilson(c["None"], n)
    say("  %-11s n=%2d  1=%2d (%.0f%%, CI %.0f-%.0f%%)  0=%2d  None=%2d (%.0f%%, CI %.0f-%.0f%%)%s"
        % (st, n, c["1"], 100 * p, 100 * lo, 100 * hi, c["0"], c["None"], 100 * pn, 100 * ln_, 100 * hn,
           "  <-- None>40%% 可判性不足" if pn > 0.40 else ""))
n = 100
p, lo, hi = wilson(truth["1"], n); pn, ln_, hn = wilson(truth["None"], n)
say("  %-11s n=%2d  1=%2d (%.0f%%, CI %.0f-%.0f%%)  0=%2d  None=%2d (%.0f%%, CI %.0f-%.0f%%)"
    % ("ALL", n, truth["1"], 100 * p, 100 * lo, 100 * hi, truth["0"], truth["None"], 100 * pn, 100 * ln_, 100 * hn))
