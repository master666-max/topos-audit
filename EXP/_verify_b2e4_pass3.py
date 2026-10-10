"""Verification pass 3.

(a) SOURCE FIDELITY: for all 100 units, compare the workbook's shown source
    block byte-for-byte against the real 3.13.12 stdlib file at the stated
    lineno. If the workbook does not faithfully render the target, every
    judgment resting on it is unsafe -- this must be checked before trusting
    any verdict.
(b) #26 done properly: pass 2 matched HTMLRepr.repr_instance (the first
    `def repr_instance(self, x, level)` in the file) and called pydoc.text,
    which is a TextDoc. Locate the class the workbook actually names
    (TextRepr, pydoc.py:1259) and test that one.
"""
import json, os, re, sys, csv, subprocess

OUT = sys.__stdout__
def say(*a, end="\n"):
    OUT.write(" ".join(str(x) for x in a) + end); OUT.flush()

ROOT = r"C:\Users\26672\.workbuddy\binaries\python\versions\3.13.12\Lib"
EXP = os.path.dirname(os.path.abspath(__file__))
say("target stdlib root =", ROOT, "| exists:", os.path.isdir(ROOT))
say("=" * 78)

# ---------------------------------------------------------------- (a)
wb = open(os.path.join(EXP, "B2-E4-workbook.md"), encoding="utf-8").read()
parts = re.split(r"^## #(\d+) · (\S+) · `([^`]+)`$", wb, flags=re.M)
U = {}
for i in range(1, len(parts), 4):
    U[int(parts[i])] = {"stratum": parts[i + 1], "qual": parts[i + 2], "body": parts[i + 3]}

# roster from the COMMITTED blob so a concurrent writer cannot shift it under us
head = subprocess.run(["git", "cat-file", "blob", "HEAD:EXP/B2-E4-sample.csv"],
                      capture_output=True, cwd=os.path.dirname(EXP)).stdout.decode("utf-8")
rows = {int(r["seq"]): r for r in csv.DictReader(head.splitlines())}
say("roster from HEAD blob: %d rows" % len(rows))

cache = {}
def real_lines(relpath):
    if relpath not in cache:
        p = os.path.join(ROOT, relpath.replace("/", os.sep))
        cache[relpath] = open(p, encoding="utf-8").read().splitlines() if os.path.exists(p) else None
    return cache[relpath]

exact = 0; mismatch = []; missing = []
for s in sorted(U):
    r = rows[s]
    src = re.search(r"```python\n(.*?)\n```", U[s]["body"], re.S)
    shown = src.group(1).splitlines() if src else []
    rl = real_lines(r["file"])
    if rl is None:
        missing.append((s, r["file"], "file not found under target root")); continue
    ln = int(r["lineno"])
    # workbook shows the unit from its def line; compare against file lines ln..ln+len(shown)-1
    actual = rl[ln - 1: ln - 1 + len(shown)]
    if actual == shown:
        exact += 1
    else:
        # try to locate the shown block elsewhere (lineno drift?) and report the nature
        joined = "\n".join(shown).strip()
        where = None
        for i in range(len(rl)):
            if "\n".join(rl[i:i + len(shown)]).strip() == joined:
                where = i + 1; break
        firstdiff = next((i for i in range(min(len(shown), len(actual)))
                          if shown[i] != actual[i]), None)
        mismatch.append((s, r["file"], r["name"], ln, len(shown), where, firstdiff,
                         shown[firstdiff] if firstdiff is not None and firstdiff < len(shown) else "",
                         actual[firstdiff] if firstdiff is not None and firstdiff < len(actual) else ""))

say("\n(a) SOURCE FIDELITY: %d/%d units match the real file byte-for-byte at the stated lineno"
    % (exact, len(U)))
say("    files not found under target root: %d %s" % (len(missing), missing[:5]))
say("    mismatches: %d" % len(mismatch))
for m in mismatch[:25]:
    s, f, n, ln, nsh, where, fd, wline, aline = m
    say("      #%-3d %s::%s  stated lineno=%d shown=%d  found_elsewhere_at=%s  first_diff_line=%s"
        % (s, f, n, ln, nsh, where, fd))
    say("           workbook: %r" % (wline[:100],))
    say("           real    : %r" % (aline[:100],))

# ---------------------------------------------------------------- (b)
say("\n" + "=" * 78)
say("(b) #26 -- the class the workbook actually names")
r26 = rows[26]
say("    workbook says: %s::%s at line %s (%s lines)" % (r26["file"], r26["name"], r26["lineno"], r26["loc"]))
rl = real_lines(r26["file"])
ln = int(r26["lineno"]); loc = int(r26["loc"])
say("    real file lines %d..%d:" % (ln, ln + loc - 1))
for i in range(ln - 1, min(ln - 1 + loc, len(rl))):
    say("      %4d| %s" % (i + 1, rl[i]))
# which class encloses that line?
cls = None
for i in range(ln - 1, -1, -1):
    m = re.match(r"^class (\w+)", rl[i])
    if m:
        cls = m.group(1); say("    enclosing class (real file): %s  (line %d)" % (cls, i + 1)); break
say("    workbook header names class  : %s" % r26["name"].split(".")[0])
say("    => class name agrees: %s" % (cls == r26["name"].split(".")[0]))

src26 = re.search(r"```python\n(.*?)\n```", U[26]["body"], re.S).group(1).splitlines()
real26 = rl[ln - 1: ln - 1 + len(src26)]
say("    workbook source == real source: %s" % (src26 == real26))
for a, b in zip(src26, real26):
    if a != b:
        say("      DIFF workbook=%r" % a); say("      DIFF real   =%r" % b)

say("\n    -- live behaviour of THAT class --")
want_cls = r26["name"].split(".")[0]
probe = os.path.join(EXP, "_probe26.py")
with open(probe, "w", encoding="utf-8") as fh:
    fh.write(
        "import pydoc as P\n"
        "want = " + repr(want_cls) + "\n"
        "cls = getattr(P, want, None)\n"
        "print('resolved class:', cls)\n"
        "inst = cls()\n"
        "class BoomKI:\n"
        "    def __repr__(self): raise KeyboardInterrupt('ctrl-c')\n"
        "class BoomSE:\n"
        "    def __repr__(self): raise SystemExit(3)\n"
        "class BoomPlain:\n"
        "    def __repr__(self): raise ValueError('nope')\n"
        "cases = [('POSITIVE CONTROL plain object', object()),\n"
        "         ('NEGATIVE CONTROL repr raises ValueError', BoomPlain()),\n"
        "         ('ATTACK repr raises KeyboardInterrupt', BoomKI()),\n"
        "         ('ATTACK repr raises SystemExit', BoomSE())]\n"
        "for label, obj in cases:\n"
        "    try:\n"
        "        r = inst.repr_instance(obj, 0)\n"
        "        print('  ' + label.ljust(42) + ' -> SWALLOWED, returned ' + repr(r))\n"
        "    except BaseException as e:\n"
        "        print('  ' + label.ljust(42) + ' -> propagated ' + type(e).__name__)\n"
    )
r = subprocess.run([sys.executable, probe], capture_output=True, text=True)
say(r.stdout.rstrip() or r.stderr.rstrip()[:600])
say("=" * 78)
say("pass 3 done")
