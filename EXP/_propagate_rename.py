"""Propagate the filename rename to every reference.

Three groups, treated differently on purpose:
  MINE (mechanical global replace)   : _build_judgeB.py, _audit_judgeB.py,
                                       B2-E4-adjudication-judgeB-qwen-3.8max.md
  FOREIGN + FUNCTIONAL (surgical,    : _xjudge_compare_judgeC.py -- backed up
    backed up, each edit marked)       first, 3 lines, each with an inline marker
  FOREIGN + HISTORICAL (left alone)  : PROVENANCE-NOTE.md, judgeC-crosscheck.md,
                                       _restore_judgeA_names.py, B2-E4-adjudication.md
                                       -- these narrate what happened at a point in
                                       time; rewriting them would falsify a record.
"""
import os, re, shutil, sys, hashlib

OUT = sys.__stdout__
FAIL = []
def say(*a):
    OUT.write(" ".join(str(x) for x in a) + "\n"); OUT.flush()
def chk(label, got, want):
    ok = got == want
    if not ok:
        FAIL.append((label, got, want))
    say("  [%s] %-58s got=%r want=%r" % ("PASS" if ok else "FAIL", label, got, want))

HERE = os.path.dirname(os.path.abspath(__file__))
OLD, NEW = "B2-E4-adjudication-judgeB", "B2-E4-adjudication-judgeB-qwen-3.8max"
# order matters: longest/most specific first so `-stats.json` is not clobbered by `.md`
PAIRS = [(OLD + "-stats.json", NEW + "-stats.json"),
         (OLD + ".jsonl", NEW + ".jsonl"),
         (OLD + ".csv", NEW + ".csv"),
         (OLD + ".md", NEW + ".md"),
         (OLD + ".*", NEW + ".*"),
         (OLD + ".{jsonl,csv,md,stats.json}", NEW + ".{jsonl,csv,md,stats.json}")]

say("=" * 78)
say("1. MINE -- mechanical replace (pretag archive names must NOT be touched)")
for f in ["_build_judgeB.py", "_audit_judgeB.py", NEW + ".md"]:
    p = os.path.join(HERE, f)
    t = open(p, encoding="utf-8").read()
    before_pretag = t.count("pretag")
    n = 0
    for a, b in PAIRS:
        c = t.count(a); n += c; t = t.replace(a, b)
    chk("%s: pretag occurrences preserved" % f, t.count("pretag"), before_pretag)
    open(p, "w", encoding="utf-8", newline="").write(t)
    left = sum(t.count(a) for a, _ in PAIRS)
    say("   %-46s replacements=%d  stale-refs-left=%d" % (f, n, left))
    if left:
        FAIL.append(("stale-refs:" + f, left, 0))

# the audit script's bare PRE constant carries no suffix, so PAIRS cannot match it
p = os.path.join(HERE, "_audit_judgeB.py")
t = open(p, encoding="utf-8").read()
a, b = 'PRE = "%s"' % OLD, 'PRE = "%s"' % NEW
chk("audit PRE constant found before fix", a in t, True)
t = t.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(t)

# the audit script also hardcodes the deliverable hashes -- those did not change
# (byte-identical rename), but its PRE constant must match the new name.
p = os.path.join(HERE, "_audit_judgeB.py")
t = open(p, encoding="utf-8").read()
chk("audit PRE updated", 'PRE = "%s"' % NEW in t, True)
chk("audit still asserts the same jsonl sha", '"aa68ef385b137dc0"' in t, True)

say("\n2. FOREIGN + FUNCTIONAL -- _xjudge_compare_judgeC.py (backed up, then surgical)")
tgt = os.path.join(HERE, "_xjudge_compare_judgeC.py")
bak = tgt + ".judgeB-edit-backup"
shutil.copy2(tgt, bak)
say("   backup: %s (%d B, sha=%s)" % (os.path.basename(bak), os.path.getsize(bak), hashlib.sha256(open(bak, "rb").read()).hexdigest()[:16]))
t = open(tgt, encoding="utf-8").read()
EDITS = [
    ('b = load_jsonl(os.path.join(exp, "%s.jsonl"))' % OLD,
     'b = load_jsonl(os.path.join(exp, "%s.jsonl"))  # judgeB 2026-10-10: renamed to carry the model tag (user ruling)' % NEW),
    ('("judgeB(qoder)", b)',
     '("judgeB(qwen-3.8max)", b)  # judgeB 2026-10-10: model tag per user ruling'),
    ('`L4-control-judgeB-qoder`',
     '`ai:qwen-3.8max(L4-control,judgeB,single-rater,no-kappa)`'),
    ('`%s.*`' % OLD, '`%s.*`' % NEW),
]
for a, b in EDITS:
    c = t.count(a)
    say("   %-64s occurrences=%d" % (a[:62], c))
    if c == 0:
        FAIL.append(("foreign-edit-not-found:" + a[:40], 0, ">=1"))
    t = t.replace(a, b)
open(tgt, "w", encoding="utf-8", newline="").write(t)
import ast
try:
    ast.parse(open(tgt, encoding="utf-8").read())
    chk("foreign script still parses after my edit", True, True)
except SyntaxError as e:
    chk("foreign script still parses after my edit", "SyntaxError: %s" % e, True)
    shutil.copy2(bak, tgt)
    say("   !! ROLLED BACK from backup")
chk("foreign script now points at the new path", '%s.jsonl' % NEW in open(tgt, encoding="utf-8").read(), True)

say("\n3. FOREIGN + HISTORICAL -- deliberately NOT rewritten")
for f in ["B2-E4-adjudication-PROVENANCE-NOTE.md", "B2-E4-adjudication-judgeC-crosscheck.md",
          "_restore_judgeA_names.py", "B2-E4-adjudication.md"]:
    p = os.path.join(HERE, f)
    if not os.path.exists(p):
        say("   [SKIP] %s absent" % f); continue
    t = open(p, encoding="utf-8").read()
    say("   [LEFT AS-IS] %-46s mentions judgeB %2d time(s), old exact filenames %d"
        % (f, t.count("judgeB"), sum(t.count(a) for a, _ in PAIRS)))

say("\n4. repo-wide sweep for stale exact references to the old names")
stale = []
for root, dirs, files in os.walk(os.path.dirname(HERE)):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
    for fn in files:
        if not fn.endswith((".py", ".md", ".json", ".jsonl", ".csv", ".stdout", ".txt")):
            continue
        p = os.path.join(root, fn)
        if p == bak or os.path.basename(p).startswith(OLD + ".pretag"):
            continue
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for a, _ in PAIRS:
            if a.endswith(".*") or "{" in a:
                continue
            if a in t:
                stale.append((os.path.relpath(p, os.path.dirname(HERE)), a))
for s in sorted(set(stale)):
    say("   STALE %s  ->  %s" % s)
chk("stale exact-name references outside historical docs and the backup",
    sorted(set(f for f, a in stale if "PROVENANCE" not in f and "crosscheck" not in f
               and "_restore_judgeA" not in f and not f.endswith("B2-E4-adjudication.md")
               and ".stdout" not in f)), [])

say("\n" + "=" * 78)
if FAIL:
    say("PROPAGATE FAIL: %d" % len(FAIL))
    for f in FAIL:
        say("   ", f)
    sys.exit(1)
say("PROPAGATE PASS: my files updated, the one foreign functional reference")
say("updated in place (backup kept, edit marked, syntax re-checked), historical")
say("narrative documents left byte-identical.")
