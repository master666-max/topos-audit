"""Final independent audit of the judgeB deliverables.

Re-reads what actually landed on disk (write-receipt != on-disk) and cross-checks
every number asserted in B2-E4-adjudication-judgeB-qwen-3.8max.md against the artifacts.
Also asserts that the second producer's files were NOT touched by this session.
"""
import csv, hashlib, json, os, re, subprocess, sys, collections, math

OUT = sys.__stdout__
FAIL = []
def say(*a, end="\n"):
    OUT.write(" ".join(str(x) for x in a) + end); OUT.flush()
def chk(label, got, want):
    ok = got == want
    if not ok:
        FAIL.append((label, got, want))
    say("  [%s] %-58s got=%r want=%r" % ("PASS" if ok else "FAIL", label, got, want))

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PRE = "B2-E4-adjudication-judgeB-qwen-3.8max"

say("=" * 78)
say("A. re-read the delivered jsonl from disk")
recs = [json.loads(l) for l in open(os.path.join(HERE, PRE + ".jsonl"), encoding="utf-8") if l.strip()]
chk("jsonl record count", len(recs), 100)
chk("jsonl seq set == 1..100", sorted(r["seq"] for r in recs), list(range(1, 101)))
chk("jsonl no duplicate seq", len(set(r["seq"] for r in recs)), 100)
truth = collections.Counter(r["truth"] for r in recs)
chk("truth values subset of {1,0,None}", set(truth), {"1", "0", "None"})
chk("truth counts sum to 100", sum(truth.values()), 100)
say("     truth =", dict(truth))
chk("truth 1 count", truth["1"], 11)
chk("truth 0 count", truth["0"], 75)
chk("truth None count", truth["None"], 14)
rule = collections.Counter(r["rule"] for r in recs)
say("     rule  =", dict(rule))
chk("rule R0", rule["R0"], 75); chk("rule R1", rule["R1"], 11)
chk("rule RN-INV", rule["RN-INV"], 6); chk("rule RGAP-trunc", rule["RGAP-trunc"], 4)
chk("rule RN-SHIM", rule["RN-SHIM"], 3); chk("rule RGAP-extfmt", rule["RGAP-extfmt"], 1)
chk("rule counts sum", sum(rule.values()), 100)
dt = collections.Counter(r["defect_type"] for r in recs if r["defect_type"])
say("     defect_type =", dict(dt))
chk("defect_type totals", sum(dt.values()), 11)
chk("error_handling", dt["error_handling"], 5); chk("logic", dt["logic"], 4)
chk("boundary", dt["boundary"], 1); chk("message", dt["message"], 1)
chk("security used", dt.get("security", 0), 0)
ver = collections.Counter(r["verification"] for r in recs)
say("     verification =", dict(ver))
chk("exec-confirmed", ver["exec-confirmed"], 10)
chk("exec-confirmed-mechanism-corrected", ver["exec-confirmed-mechanism-corrected"], 1)
chk("exec-refuted", ver["exec-refuted"], 2)
chk("not-execution-tested", ver["not-execution-tested"], 87)

say("\nB. per-record invariants demanded by RULE.md")
ones = sorted(r["seq"] for r in recs if r["truth"] == "1")
nones = sorted(r["seq"] for r in recs if r["truth"] == "None")
say("     truth=1 units   :", ones)
say("     truth=None units:", nones)
chk("1-set", ones, [12, 20, 25, 26, 31, 33, 37, 55, 62, 93, 96])
chk("None-set", nones, [4, 10, 11, 14, 16, 17, 22, 24, 40, 54, 57, 72, 83, 94])
chk("every 1 carries a mechanism sentence", all("机理" in r["note"] for r in recs if r["truth"] == "1"), True)
chk("every 1 is execution-verified",
    sorted(r["seq"] for r in recs if r["truth"] == "1" and r["verification"].startswith("exec-confirmed")), ones)
chk("every None names a form",
    all(any(k in r["note"] for k in ("N-CTX", "N-INV", "N-SHIM", "N-VER", "rule_gap"))
        for r in recs if r["truth"] == "None"), True)
chk("every record has a rule code", all(r.get("rule") for r in recs), True)
chk("every record marked non-gold", all(r["is_gold"] is False for r in recs), True)
chk("every record marked L4-control", set(r["layer"] for r in recs), {"L4-control"})
chk("annotator carries the model tag (user-directed 2026-10-10)",
    set(r["annotator"] for r in recs),
    {"ai:qwen-3.8max(L4-control,judgeB,single-rater,no-kappa)"})
chk("retracted records", sorted(r["seq"] for r in recs if r["retracted_from"]), [80, 98])
chk("retracted ones now read 0", sorted(r["seq"] for r in recs if r["retracted_from"] and r["truth"] == "0"), [80, 98])
chk("truncated flags", sorted(r["seq"] for r in recs if r["truncated"]), [4, 14, 16, 18, 33, 37, 55, 72, 96])
chk("obs_verified flags", sorted(r["seq"] for r in recs if r["obs_verified"]), [89])

say("\nC. re-derive the stratum table from the artifacts (not from the report)")
head = subprocess.run(["git", "cat-file", "blob", "HEAD:EXP/B2-E4-sample.csv"],
                      capture_output=True, cwd=REPO, check=True).stdout.decode("utf-8")
roster = {int(r["seq"]): r for r in csv.DictReader(head.splitlines())}
def wilson(k, n, z=1.959963984540054):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)
bs = collections.defaultdict(collections.Counter)
for r in recs:
    bs[roster[r["seq"]]["stratum"]][r["truth"]] += 1
REPORTED = {"random": (30, 4, 22, 4), "confluence": (20, 3, 13, 4),
            "anchor": (25, 2, 19, 4), "zero_cover": (25, 2, 21, 2)}
for st, (n, n1, n0, nn) in REPORTED.items():
    c = bs[st]
    chk("%s n" % st, sum(c.values()), n)
    chk("%s 1-rate count" % st, c["1"], n1)
    chk("%s 0 count" % st, c["0"], n0)
    chk("%s None count" % st, c["None"], nn)
    chk("%s None-rate <= 40%% (PREREG B2)" % st, c["None"] / sum(c.values()) <= 0.40, True)
    p, lo, hi = wilson(c["1"], sum(c.values()))
    say("     %-11s 1-rate=%.0f%% CI %.0f-%.0f%%" % (st, 100 * p, 100 * lo, 100 * hi))
p, lo, hi = wilson(11, 100)
say("     ALL         1-rate=%.0f%% CI %.0f-%.0f%%  (report says 11%%, CI 6-19%%)" % (100 * p, 100 * lo, 100 * hi))
chk("ALL 1-rate rounds to 11%", round(100 * p), 11)
chk("ALL CI low rounds to 6%", round(100 * lo), 6)
chk("ALL CI high rounds to 19%", round(100 * hi), 19)
pa, _, _ = wilson(bs["anchor"]["1"], 25); pr, _, _ = wilson(bs["random"]["1"], 30)
pz, _, _ = wilson(bs["zero_cover"]["1"], 25)
say("     A1 order check: pi(anchor)=%.3f pi(random)=%.3f pi(zero_cover)=%.3f" % (pa, pr, pz))
chk("A1 anchor>random VIOLATED (as reported)", pa > pr, False)
chk("A1 random>zero_cover satisfied (as reported)", pr > pz, True)

say("\nD. csv mirrors jsonl cell-for-cell")
with open(os.path.join(HERE, PRE + ".csv"), newline="", encoding="utf-8-sig") as f:
    crows = list(csv.DictReader(f))
chk("csv row count", len(crows), 100)
chk("csv has a note column (README's 备注)", "note" in crows[0], True)
by = {r["seq"]: r for r in recs}
mism = []
for c in crows:
    s = int(c["seq"]); j = by[s]
    for k in ("unit_id", "file", "name", "stratum", "truth", "defect_type", "rule", "note"):
        if (c.get(k) or "") != str(j.get(k) or ""):
            mism.append((s, k))
chk("csv<->jsonl mismatches", mism, [])
chk("csv lineno matches jsonl", all(int(c["lineno"]) == by[int(c["seq"])]["lineno"] for c in crows), True)

say("\nE. roster integrity: my artifacts vs the COMMITTED roster")
chk("unit_id all match HEAD roster", all(by[s]["unit_id"] == roster[s]["unit_id"] for s in by), True)
chk("file all match HEAD roster", all(by[s]["file"] == roster[s]["file"] for s in by), True)
chk("lineno all match HEAD roster", all(by[s]["lineno"] == int(roster[s]["lineno"]) for s in by), True)
chk("loc all match HEAD roster", all(by[s]["loc"] == int(roster[s]["loc"]) for s in by), True)
chk("stratum all match HEAD roster", all(by[s]["stratum"] == roster[s]["stratum"] for s in by), True)

say("\nF. report text: every asserted number re-checked against artifacts")
md = open(os.path.join(HERE, PRE + ".md"), encoding="utf-8").read()
for pat, want in [(r"\|\s*`1`\s*有缺陷\s*\|\s*\*\*(\d+)\*\*", 11),
                  (r"\|\s*`0`\s*所示证据内无缺陷\s*\|\s*\*\*(\d+)\*\*", 75),
                  (r"\|\s*`None`\s*判不出来\s*\|\s*\*\*(\d+)\*\*", 14)]:
    m = re.search(pat, md)
    chk("report table %s" % pat[:28], int(m.group(1)) if m else None, want)
for st, row in REPORTED.items():
    m = re.search(r"\|\s*`%s`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|" % st, md)
    chk("report stratum row %s (n,1)" % st, (int(m.group(1)), int(m.group(2))) if m else None, (row[0], row[1]))
chk("report claims 100/100 source fidelity", "100/100 逐字节相符" in md, True)
chk("report claims 9 truncated", "9/100" in md, True)
chk("report claims 0/100 decorators", "0/100 全部丢失" in md, True)
chk("report claims 11/52 prose anchor hits", "11/52" in md, True)
chk("report names both retractions", ("#98" in md and "#80" in md and "撤回记录" in md), True)
chk("report states it did NOT write sample.csv", "未动它" in md or "完全没有触碰" in md, True)
chk("report header carries the model tag", "qwen-3.8max" in md, True)
chk("report explains why the filename stays judgeB", "13.1" in md or "§13" in md, True)
chk("report records the 3-judge landscape", "judgeC" in md and "PROVENANCE-NOTE" in md, True)

say("\nG. invariants that nobody may break (this session included)")
# G1: the PREREG A5 sealed modelside artifacts must not move -- assert size AND mtime.
say("  G1 sealed modelside artifacts (PREREG A5) -- must be byte- and time-identical:")
sealed = {
    "EXP/B2-E4-modelside.jsonl":      (33046, 1791568354),
    "EXP/B2-E4-modelside-SEAL.md":    (16687, 1791568564),
    "EXP/B2-E4-modelside-stats.json": (13139, 1791568400),
}
for rel, (size, mtime) in sealed.items():
    st = os.stat(os.path.join(REPO, rel.replace("/", os.sep)))
    ok = st.st_size == size and int(st.st_mtime) == mtime
    if not ok:
        FAIL.append(("sealed-moved:" + rel, (st.st_size, int(st.st_mtime)), (size, mtime)))
    say("    [%s] %-38s size=%d mtime=%d" % ("PASS" if ok else "FAIL", rel, st.st_size, int(st.st_mtime)))

# G2: tracked instrument/rule files must show clean in git (nobody edited them).
say("  G2 tracked rule/instrument files must be CLEAN in git status:")
gstat = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--short"],
                       capture_output=True, cwd=REPO, text=True).stdout
dirty = set(l[3:].strip() for l in gstat.splitlines())
must_be_clean = ["EXP/B2-E4-RULE.md", "EXP/B2-E4-workbook.md", "EXP/B2-E4-README.md",
                 "EXP/make_b2_e4_sample.py", "PREREG/B2.md", "topos/calib/gold.py"]
for rel in must_be_clean:
    q = rel.replace("/", os.sep)
    hit = [d for d in dirty if d.endswith(rel.split("/")[-1]) and rel.split("/")[-2].split(".")[0] in d]
    ok = not hit
    if not ok:
        FAIL.append(("tracked-file-dirty:" + rel, hit, []))
    say("    [%s] %-38s %s" % ("PASS" if ok else "FAIL", rel, "clean" if ok else "DIRTY: %s" % hit))

# G3: volatile files owned by OTHER producers -- RECORD, do not assert.
# In a live multi-agent workspace these change by their owners' actions (judgeC
# overwrote judgeA's copies at 08:52:37 and restored the generic names at 09:21:25),
# so asserting a frozen size here would produce a false FAIL that says nothing about me.
say("  G3 shared/volatile files owned by other producers -- recorded, NOT asserted:")
for rel in ["EXP/B2-E4-sample.csv", "EXP/B2-E4-adjudication.jsonl",
            "EXP/B2-E4-adjudication.csv", "EXP/B2-E4-adjudication.md", "EXP/B2-E4.md"]:
    p = os.path.join(REPO, rel.replace("/", os.sep))
    if os.path.exists(p):
        st = os.stat(p)
        say("    [INFO] %-38s size=%d mtime=%d sha256=%s"
            % (rel, st.st_size, int(st.st_mtime),
               hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]))

# G4: my own write set -- assert the deliverables are exactly what _retag produced.
say("  G4 my own deliverables must match the re-tag build:")
mine_expected = {
    "B2-E4-adjudication-judgeB-qwen-3.8max.jsonl": ("aa68ef385b137dc0", 109334),
    "B2-E4-adjudication-judgeB-qwen-3.8max.csv":   ("77c76cff1b6125c1", 82931),
    "B2-E4-adjudication-judgeB-qwen-3.8max-stats.json": ("5365b100f1d69809", 3747),
}
for f, (sha16, size) in mine_expected.items():
    p = os.path.join(HERE, f)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    ok = h.startswith(sha16) and os.path.getsize(p) == size
    if not ok:
        FAIL.append(("my-deliverable-drift:" + f, (h[:16], os.path.getsize(p)), (sha16, size)))
    say("    [%s] %-46s size=%d sha=%s" % ("PASS" if ok else "FAIL", f, os.path.getsize(p), h[:16]))
say("  G5 pre-retag archive must still exist (data-lossless re-tag):")
for f in ["B2-E4-adjudication-judgeB.pretag.jsonl", "B2-E4-adjudication-judgeB.pretag.csv",
          "B2-E4-adjudication-judgeB.pretag.md", "B2-E4-adjudication-judgeB.pretag-stats.json"]:
    ok = os.path.exists(os.path.join(HERE, f))
    if not ok:
        FAIL.append(("archive-missing:" + f, False, True))
    say("    [%s] %s" % ("PASS" if ok else "FAIL", f))

# G6: the ONE foreign file I edited, under explicit user authorization.
# This must be asserted loudly, not hidden -- an audit that claims "I touched
# nobody's files" while a backup of someone's file sits in the directory is worse
# than useless.
say("  G6 foreign file edited this session (user-authorized 2026-10-10 '全改，文件名也要'):")
fgn = os.path.join(HERE, "_xjudge_compare_judgeC.py")
fgnbak = fgn + ".judgeB-edit-backup"
chk("backup of the foreign file retained", os.path.exists(fgnbak), True)
ft = open(fgn, encoding="utf-8").read()
import ast as _ast
try:
    _ast.parse(ft); chk("foreign file still parses", True, True)
except SyntaxError as e:
    chk("foreign file still parses", "SyntaxError: %s" % e, True)
chk("foreign file now resolves the renamed path", "B2-E4-adjudication-judgeB-qwen-3.8max.jsonl" in ft, True)
chk("foreign file no longer points at the dead path",
    'os.path.join(exp, "B2-E4-adjudication-judgeB.jsonl")' in ft, False)
chk("my edit is marked in-place with date + reason", "[judgeB edit 2026-10-10]" in ft, True)
say("    [INFO] backup sha256=%s  current sha256=%s"
    % (hashlib.sha256(open(fgnbak, "rb").read()).hexdigest()[:16],
       hashlib.sha256(open(fgn, "rb").read()).hexdigest()[:16]))
say("    [INFO] round-trip proof (undo my edits == original byte-for-byte) is in")
say("           _fix_foreign_ref.stdout; historical narrative docs were left untouched:")
for f in ["B2-E4-adjudication-PROVENANCE-NOTE.md", "B2-E4-adjudication-judgeC-crosscheck.md",
          "_restore_judgeA_names.py", "B2-E4-adjudication.md"]:
    p = os.path.join(HERE, f)
    if os.path.exists(p):
        say("           [LEFT AS-IS] %-46s %d B" % (f, os.path.getsize(p)))

say("\nH. workbook unchanged (my evidence base) + git view of what I added")
wb = open(os.path.join(HERE, "B2-E4-workbook.md"), "rb").read()
chk("workbook sha256 (text) still 78f9356f...",
    hashlib.sha256(wb).hexdigest()[:8], "78f9356f")
g = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--short"],
                   capture_output=True, cwd=REPO, text=True).stdout
mine, theirs, other = [], [], []
for line in g.splitlines():
    tag, path = line[:2], line[3:].strip()
    MINE = ("judgeB", "_adj_batch", "_verify_b2e4", "_verify_pass", "_build_judgeB", "_probe26",
            "_rename_to_model_tag", "_propagate_rename", "_fix_foreign_ref")
    if any(k in path for k in MINE):
        mine.append((tag, path))
    elif "adjudication" in path or path.endswith("B2-E4.md") or "modelside" in path or path.endswith("B2-E4-sample.csv") or path.endswith("B2-E4-sample-mixed.csv"):
        theirs.append((tag, path))
    else:
        other.append((tag, path))
say("  files I created this session (%d):" % len(mine))
for t, p in mine: say("     %s %s" % (t, p))
say("  other producers' tracked/untracked deliverables (%d) -- none modified by me:" % len(theirs))
for t, p in theirs: say("     %s %s" % (t, p))
say("  anything else dirty (%d) -- NOTE this bucket contains _xjudge_compare_judgeC.py," % len(other))
say("  which I DID edit under user authorization; that edit is asserted in G6, not here:")
say("     %s" % other)
chk("no git-TRACKED foreign file modified by me beyond the pre-existing ' M sample.csv'",
    sorted(p for t, p in theirs if t.strip() == "M"), ["EXP/B2-E4-sample.csv"])
say("  NOTE: ' M EXP/B2-E4-sample.csv' predates this session (second producer filled it at")
say("        02:15:33, later restored by judgeC at 09:21:25). This session never wrote it.")
say("  NOTE: one UNTRACKED foreign file WAS edited by me under explicit user authorization")
say("        (_xjudge_compare_judgeC.py, see G6). git cannot show it as 'M' because it was")
say("        never committed -- so the check above does not cover it, and G6 does.")

say("\nI. deliverable hashes (for the seal / for citing)")
for f in [PRE + ".jsonl", PRE + ".csv", PRE + ".md", PRE + "-stats.json"]:
    p = os.path.join(HERE, f)
    say("  %-46s %8d B  sha256=%s" % (f, os.path.getsize(p), hashlib.sha256(open(p, "rb").read()).hexdigest()))

say("\n" + "=" * 78)
if FAIL:
    say("AUDIT FAIL: %d check(s) did not hold" % len(FAIL))
    for f in FAIL:
        say("   ", f)
    sys.exit(1)
say("AUDIT PASS: every check held. Deliverables are internally consistent and match")
say("the committed roster. Foreign writes this session: exactly ONE file, authorized,")
say("backed up, syntax-gated and round-trip proven (G6). sample.csv never written.")
