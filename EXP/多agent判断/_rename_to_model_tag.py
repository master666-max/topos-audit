"""Rename the judgeB deliverables so the FILENAME carries the model tag.

Sequence (each step verified before the next; nothing deleted until byte-equality
against the replacement is proven):
  1. re-run the builder with the new PRE  -> new-named .jsonl/.csv/-stats.json
  2. move the hand-written .md to the new name
  3. prove old .jsonl/.csv/-stats.json are BYTE-IDENTICAL to the new ones
  4. only then remove the old-named trio (identical content survives twice:
     under the new name, and in the *.pretag.* archive)
  5. re-verify the pretag archive and the sealed/invariant files
"""
import hashlib, os, shutil, subprocess, sys

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
REPO = os.path.dirname(HERE)
PY = r"C:\Users\26672\.workbuddy\binaries\python\versions\3.13.12\python.exe"
OLD = "B2-E4-adjudication-judgeB"
NEW = "B2-E4-adjudication-judgeB-qwen-3.8max"
def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

say("=" * 78)
say("0. before: what exists under the old name")
for suf in [".jsonl", ".csv", ".md", "-stats.json"]:
    p = os.path.join(HERE, OLD + suf)
    say("   %-52s %s" % (OLD + suf, ("%d B sha=%s" % (os.path.getsize(p), sha(p)[:16])) if os.path.exists(p) else "ABSENT"))

say("\n1. re-run builder with PRE = %r" % NEW)
r = subprocess.run([PY, "-X", "utf8", os.path.join(HERE, "_build_judgeB.py")],
                   capture_output=True, text=True, cwd=REPO)
chk("builder rc", r.returncode, 0)
for line in r.stdout.splitlines():
    if line.startswith("wrote") or line.startswith("truth:"):
        say("   " + line.strip()[:130])
if r.returncode != 0:
    say(r.stderr[-1500:]); sys.exit(1)

say("\n2. move the hand-written report to the new name")
src, dst = os.path.join(HERE, OLD + ".md"), os.path.join(HERE, NEW + ".md")
shutil.move(src, dst)
chk("report moved", (os.path.exists(dst), os.path.exists(src)), (True, False))
say("   %s -> %s (%d B)" % (os.path.basename(src), os.path.basename(dst), os.path.getsize(dst)))

say("\n3. prove the old machine files are byte-identical to the new ones")
identical = True
for suf in [".jsonl", ".csv", "-stats.json"]:
    o, n = os.path.join(HERE, OLD + suf), os.path.join(HERE, NEW + suf)
    if not os.path.exists(n):
        chk("new file exists: " + suf, False, True); identical = False; continue
    if not os.path.exists(o):
        say("   [INFO] %s already gone" % (OLD + suf)); continue
    same = sha(o) == sha(n)
    identical = identical and same
    chk("byte-identical %s" % suf, same, True)
    say("        old sha=%s  new sha=%s  sizes %d/%d" % (sha(o)[:16], sha(n)[:16], os.path.getsize(o), os.path.getsize(n)))

say("\n4. remove the superseded old-named trio (only because step 3 passed)")
if identical:
    for suf in [".jsonl", ".csv", "-stats.json"]:
        o = os.path.join(HERE, OLD + suf)
        if os.path.exists(o):
            os.remove(o)
            say("   removed %s" % (OLD + suf))
else:
    say("   SKIPPED -- byte-equality not proven, nothing removed")
    FAIL.append(("refused-to-remove", identical, True))

say("\n5. invariants re-checked after the rename")
for f, sz, s in [("B2-E4-adjudication-judgeB.pretag.jsonl", 106134, "a8086e68bec6dedf"),
                 ("B2-E4-adjudication-judgeB.pretag.csv", 79531, "04241219e16ef2ae"),
                 ("B2-E4-adjudication-judgeB.pretag.md", None, None),
                 ("B2-E4-adjudication-judgeB.pretag-stats.json", 3715, "ea3de12d726a120f")]:
    p = os.path.join(HERE, f)
    ok = os.path.exists(p) and (sz is None or os.path.getsize(p) == sz) and (s is None or sha(p).startswith(s))
    if not ok:
        FAIL.append(("archive:" + f, os.path.exists(p), True))
    say("   [%s] archive intact: %-52s %s" % ("PASS" if ok else "FAIL", f,
        ("%d B" % os.path.getsize(p)) if os.path.exists(p) else "MISSING"))
for rel, sz, mt in [("EXP/B2-E4-modelside.jsonl", 33046, 1791568354),
                    ("EXP/B2-E4-modelside-SEAL.md", 16687, 1791568564),
                    ("EXP/B2-E4-modelside-stats.json", 13139, 1791568400)]:
    st = os.stat(os.path.join(REPO, rel.replace("/", os.sep)))
    ok = st.st_size == sz and int(st.st_mtime) == mt
    if not ok:
        FAIL.append(("sealed:" + rel, (st.st_size, int(st.st_mtime)), (sz, mt)))
    say("   [%s] sealed untouched: %-38s %d B" % ("PASS" if ok else "FAIL", rel, st.st_size))

say("\n6. final state under the new name")
for suf in [".jsonl", ".csv", ".md", "-stats.json"]:
    p = os.path.join(HERE, NEW + suf)
    say("   %-56s %8d B  sha256=%s" % (NEW + suf, os.path.getsize(p), sha(p)))
leftovers = sorted(f for f in os.listdir(HERE) if f.startswith(OLD) and "pretag" not in f and not f.startswith(NEW))
chk("no old-named deliverable left behind (pretag archive excluded)", leftovers, [])

say("\n" + "=" * 78)
if FAIL:
    say("RENAME FAIL: %d" % len(FAIL))
    for f in FAIL:
        say("   ", f)
    sys.exit(1)
say("RENAME PASS: filenames now carry the model tag, content byte-identical,")
say("pretag archive and the sealed modelside files untouched.")
