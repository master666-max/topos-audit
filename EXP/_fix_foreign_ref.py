"""Corrected surgical edit of the ONE foreign functional reference.

Previous attempt failed and auto-rolled back: an inline `#` comment was inserted
mid-expression inside a list literal on line 117, which commented out the rest of
that physical line and left the '[' unclosed. Rule learned and applied here:
never append an inline comment to a replacement that sits inside a multi-item
expression -- markers go on their own line.
"""
import ast, hashlib, os, shutil, sys

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
tgt = os.path.join(HERE, "_xjudge_compare_judgeC.py")
bak = tgt + ".judgeB-edit-backup"

say("=" * 78)
say("0. confirm the previous attempt really did roll back")
chk("target file exists", os.path.exists(tgt), True)
chk("backup exists", os.path.exists(bak), True)
h_t = hashlib.sha256(open(tgt, "rb").read()).hexdigest()
h_b = hashlib.sha256(open(bak, "rb").read()).hexdigest()
chk("target is byte-identical to the pre-edit backup", h_t, h_b)
say("   sha256=%s  size=%d" % (h_t[:24], os.path.getsize(tgt)))
orig = open(tgt, encoding="utf-8").read()
chk("original parses", (lambda: (ast.parse(orig), True)[1])(), True)
chk("original still points at the OLD path", OLD + ".jsonl" in orig, True)

# ---- string replacements ONLY; no inline comments anywhere ----
say("\n1. apply string replacements (no inline comments -- that was the bug)")
t = orig
EDITS = [
    ('os.path.join(exp, "%s.jsonl")' % OLD, 'os.path.join(exp, "%s.jsonl")' % NEW),
    ('("judgeB(qoder)", b)', '("judgeB(qwen-3.8max)", b)'),
    ('`L4-control-judgeB-qoder`', '`ai:qwen-3.8max(L4-control,judgeB,single-rater,no-kappa)`'),
    ('`%s.*`' % OLD, '`%s.*`' % NEW),
]
for a, b in EDITS:
    c = t.count(a)
    chk("found exactly once: %s" % a[:52], c, 1)
    t = t.replace(a, b)

say("\n2. insert ONE standalone marker line above the load_jsonl call")
anchor = '    b = load_jsonl(os.path.join(exp, "%s.jsonl"))' % NEW
marker = ('    # [judgeB edit 2026-10-10] path + annotator + label updated after judgeB\n'
          '    # renamed its deliverables to carry the model tag (user ruling "全改，文件名也要").\n'
          '    # Backup of the pre-edit file: _xjudge_compare_judgeC.py.judgeB-edit-backup\n')
chk("anchor line present exactly once", t.count(anchor), 1)
t = t.replace(anchor, marker + anchor, 1)

say("\n3. syntax gate, then write")
try:
    ast.parse(t)
    chk("edited file parses", True, True)
except SyntaxError as e:
    chk("edited file parses", "SyntaxError line %s: %s" % (e.lineno, e.msg), True)
    say("   !! NOT WRITTEN; target left as the rolled-back original")
    sys.exit(1)
open(tgt, "w", encoding="utf-8", newline="").write(t)

say("\n4. verify on disk (re-read, do not trust the write receipt)")
d = open(tgt, encoding="utf-8").read()
ast.parse(d)
chk("parses after write", True, True)
chk("new path present", NEW + ".jsonl" in d, True)
chk("old exact path gone", 'os.path.join(exp, "%s.jsonl")' % OLD in d, False)
chk("label updated", '("judgeB(qwen-3.8max)", b)' in d, True)
chk("annotator string updated", "ai:qwen-3.8max(L4-control,judgeB,single-rater,no-kappa)" in d, True)
chk("marker line present", "[judgeB edit 2026-10-10]" in d, True)
chk("line count grew by exactly the 3 marker lines",
    len(d.splitlines()) - len(orig.splitlines()), 3)
# everything except my 4 intended edits + 3 marker lines must be untouched
import difflib
diff = [l for l in difflib.unified_diff(orig.splitlines(), d.splitlines(), lineterm="", n=0)
        if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
say("   changed/added lines: %d" % len(diff))
for l in diff:
    say("     " + l[:132])
# Arithmetic: EDITS 1,2 touch one line each; EDITS 3 and 4 both land on the SAME
# line (the A("| judgeB | ... |") emit), so that is 3 changed lines (-3/+3) plus
# the 3 standalone marker lines (+3) = 9 diff entries total.
removed = [l for l in diff if l.startswith("-")]
added = [l for l in diff if l.startswith("+")]
chk("removed lines (3 originals)", len(removed), 3)
chk("added lines (3 rewrites + 3 marker lines)", len(added), 6)
chk("every removed line is one I intended to change",
    all(("judgeB.jsonl" in l) or ("judgeB(qoder)" in l) or ("L4-control-judgeB-qoder" in l)
        for l in removed), True)
# real round-trip proof (not a tautology): undo my edits on the written file and
# require byte-equality with the pre-edit original.
u = d
u = u.replace(marker, "")                      # drop the 3 marker lines
for a, b in EDITS:                             # reverse every string edit
    u = u.replace(b, a)
chk("round-trip: undoing my edits reproduces the original byte-for-byte", u, orig)
chk("file size grew, not shrank", os.path.getsize(tgt) > os.path.getsize(bak), True)

say("\n" + "=" * 78)
if FAIL:
    say("FOREIGN EDIT FAIL: %d" % len(FAIL))
    for f in FAIL:
        say("   ", f)
    say("   rolling back")
    shutil.copy2(bak, tgt)
    sys.exit(1)
say("FOREIGN EDIT PASS: 4 string edits + 3 marker lines, syntax verified before")
say("and after write, backup retained, diff is exactly the intended change.")
