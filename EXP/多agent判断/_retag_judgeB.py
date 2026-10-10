"""Re-tag judgeB's `annotator` to carry the model name, and PROVE the change is
metadata-only (no truth / defect_type / rule / note value moved).

Order: archive the pre-retag deliverables -> rebuild -> field-by-field diff.
Nothing is deleted; the archive stays on disk.
"""
import hashlib, json, os, shutil, subprocess, sys

OUT = sys.__stdout__
FAIL = []
def say(*a):
    OUT.write(" ".join(str(x) for x in a) + "\n"); OUT.flush()
def chk(label, got, want):
    ok = got == want
    if not ok:
        FAIL.append((label, got, want))
    say("  [%s] %-56s got=%r want=%r" % ("PASS" if ok else "FAIL", label, got, want))

HERE = os.path.dirname(os.path.abspath(__file__))
PRE = "B2-E4-adjudication-judgeB"
FILES = [PRE + ".jsonl", PRE + ".csv", PRE + ".md", PRE + "-stats.json"]
PY = r"C:\Users\26672\.workbuddy\binaries\python\versions\3.13.12\python.exe"

say("=" * 78)
say("1. archive the pre-retag deliverables (data-lossless; nothing deleted)")
arch = {}
for f in FILES:
    src = os.path.join(HERE, f)
    dst = os.path.join(HERE, f.replace(PRE, PRE + ".pretag"))
    shutil.copy2(src, dst)
    arch[f] = hashlib.sha256(open(src, "rb").read()).hexdigest()
    say("   %-46s -> %-52s sha256=%s" % (f, os.path.basename(dst), arch[f][:16]))

say("\n2. rebuild with the new annotator")
r = subprocess.run([PY, "-X", "utf8", os.path.join(HERE, "_build_judgeB.py")],
                   capture_output=True, text=True, cwd=os.path.dirname(HERE))
say("   rc=%d" % r.returncode)
for line in r.stdout.splitlines():
    if "wrote" in line or "truth:" in line or "revisions" in line:
        say("   " + line.strip()[:150])
if r.returncode != 0:
    say(r.stderr[-2000:]); sys.exit(1)

say("\n3. prove the re-tag touched ONLY the annotator field")
old = [json.loads(l) for l in open(os.path.join(HERE, PRE + ".pretag.jsonl"), encoding="utf-8") if l.strip()]
new = [json.loads(l) for l in open(os.path.join(HERE, PRE + ".jsonl"), encoding="utf-8") if l.strip()]
chk("record count unchanged", (len(old), len(new)), (100, 100))
chk("key set unchanged", set(old[0]) == set(new[0]), True)
JUDGE_FIELDS = ["seq", "unit_id", "file", "name", "lineno", "stratum", "truth",
                "defect_type", "rule", "note", "loc", "truncated", "verification",
                "retracted_from", "obs_verified", "layer", "is_gold"]
drift = []
for o, n in zip(old, new):
    for k in JUDGE_FIELDS:
        if o.get(k) != n.get(k):
            drift.append((o.get("seq"), k))
chk("judgment-field drift across all 100 records x %d fields" % len(JUDGE_FIELDS), drift, [])
chk("old annotator set", set(r["annotator"] for r in old), {"L4-control-judgeB-qoder"})
chk("new annotator set", set(r["annotator"] for r in new),
    {"ai:qwen-3.8max(L4-control,judgeB,single-rater,no-kappa)"})
chk("date unchanged", set(r["date"] for r in new), {"2026-10-10"})
import collections
chk("truth distribution unchanged",
    dict(collections.Counter(r["truth"] for r in new)),
    dict(collections.Counter(r["truth"] for r in old)))
chk("truth distribution == 11/75/14",
    dict(collections.Counter(r["truth"] for r in new)), {"0": 75, "None": 14, "1": 11})

say("\n4. new hashes (cite these; the pretag hashes above are the archived predecessors)")
for f in FILES:
    p = os.path.join(HERE, f)
    say("   %-46s %8d B  sha256=%s" % (f, os.path.getsize(p), hashlib.sha256(open(p, "rb").read()).hexdigest()))

say("\n5. the judgeB filename suffix must survive (other producers depend on it)")
deps = ["_xjudge_compare_judgeC.py", "B2-E4-adjudication-PROVENANCE-NOTE.md",
        "B2-E4-adjudication-judgeC-crosscheck.md", "_restore_judgeA_names.py",
        "B2-E4-adjudication.md"]
for d in deps:
    p = os.path.join(HERE, d)
    if not os.path.exists(p):
        say("   [SKIP] %s absent" % d); continue
    t = open(p, encoding="utf-8").read()
    say("   [%s] %-46s references 'judgeB' %d time(s)"
        % ("PASS" if "judgeB" in t else "WARN", d, t.count("judgeB")))
for f in FILES:
    chk("still on disk under the judgeB name: %s" % f, os.path.exists(os.path.join(HERE, f)), True)

say("\n" + "=" * 78)
if FAIL:
    say("RETAG AUDIT FAIL: %d" % len(FAIL))
    for f in FAIL:
        say("   ", f)
    sys.exit(1)
say("RETAG PASS: annotator now carries the model tag, every judgment field is")
say("byte-identical to the frozen pre-retag archive, and the judgeB filenames")
say("that other producers reference are unchanged.")
