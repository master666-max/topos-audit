"""Verification pass 2: the units whose pass-1 harness was wrong or crashed.

#20  pass 1 called pickle.loads(), which dispatches to the C _pickle module.
     The workbook sampled pickle.py:1387 = the PURE-PYTHON _Unpickler. Retest
     against that class explicitly, and inspect _Unpickler.read for a guard.
#80  pass 1 forced the missing-__spec__ state by deleting the attribute.
     Now ask the real interpreter: under -c / script / -m / interactive, does
     __main__ actually carry __spec__?
#96  pass 1 regex failed to extract addToZip. Now drive the real zipfile CLI
     against a genuine symlink loop with a recursion ceiling.
#26  never ran. Now confirm the bare except and whether it swallows
     KeyboardInterrupt.
"""
import io, os, pickle, re, struct, subprocess, sys, sysconfig, tempfile, textwrap

OUT = sys.__stdout__
def say(*a, end="\n"):
    OUT.write(" ".join(str(x) for x in a) + end); OUT.flush()

STDLIB = sysconfig.get_paths()["stdlib"]
say("python =", sys.version.split()[0], "| stdlib =", STDLIB)
say("=" * 78)

# ---------------------------------------------------------------- #20
say("\n### #20 PURE-PYTHON pickle._Unpickler.load_binbytes (the sampled unit)")
psrc = open(pickle.__file__, encoding="utf-8").read()
m = re.search(r"\n    def read\(self, n\):(.*?)\n    def ", psrc, re.S)
say("  does _Unpickler define its own read(self, n)? :", bool(m))
if m:
    for line in m.group(1).strip().splitlines():
        say("     |", line)
m2 = re.search(r"\n    def load_binbytes\(self\):(.*?)\n    dispatch", psrc, re.S)
say("  real load_binbytes body:")
for line in (m2.group(1).strip().splitlines() if m2 else ["<not found>"]):
    say("     |", line)
say("  how is self.read bound in __init__?")
for mm in re.finditer(r"^.*self\.read\s*=.*$", psrc, re.M):
    say("     |", mm.group(0).strip())

say("\n  -- live test against pickle._Unpickler (NOT the C impl) --")
def pyload(data):
    return pickle._Unpickler(io.BytesIO(data)).load()

good = pickle.PROTO + bytes([3]) + b"B" + struct.pack("<I", 3) + b"abc" + b"."
say("  POSITIVE CONTROL well-formed BINBYTES(3)+b'abc':", end=" ")
try:
    say(repr(pyload(good)))
except Exception as e:
    say("UNEXPECTED", type(e).__name__, e)

trunc = pickle.PROTO + bytes([3]) + b"B" + struct.pack("<I", 100) + b"abc" + b"."
say("  ATTACK BINBYTES declares 100, only 3 available :", end=" ")
try:
    r = pyload(trunc)
    say("SILENTLY RETURNED", repr(r), "<-- short read accepted")
except Exception as e:
    say(type(e).__name__ + ":", str(e)[:60],
        "| is UnpicklingError:", isinstance(e, pickle.UnpicklingError))

say("  ATTACK header itself short (2 bytes)          :", end=" ")
try:
    pyload(b"B\x01")
    say("no error")
except Exception as e:
    say(type(e).__name__ + ":", str(e)[:60],
        "| is UnpicklingError:", isinstance(e, pickle.UnpicklingError),
        "| is struct.error:", isinstance(e, struct.error))
say("  C impl for contrast, same truncated stream     :", end=" ")
try:
    pickle.loads(trunc); say("no error")
except Exception as e:
    say(type(e).__name__ + ":", str(e)[:60])

# ---------------------------------------------------------------- #80
say("\n### #80 does __main__ really lack __spec__ in any real launch mode?")
probe = ("import sys;m=sys.modules['__main__'];"
         "print('has_spec=',hasattr(m,'__spec__'),'val=',repr(getattr(m,'__spec__','<absent>'))[:40])")
d = tempfile.mkdtemp()
try:
    sp = os.path.join(d, "script.py")
    with open(sp, "w", encoding="utf-8") as f:
        f.write("import sys\nprint('has_spec=',hasattr(sys.modules['__main__'],'__spec__'),"
                "'val=',repr(getattr(sys.modules['__main__'],'__spec__','<absent>'))[:40])\n")
    with open(os.path.join(d, "modpkg_probe.py"), "w", encoding="utf-8") as f:
        f.write("import sys\nprint('has_spec=',hasattr(sys.modules['__main__'],'__spec__'),"
                "'val=',repr(getattr(sys.modules['__main__'],'__spec__','<absent>'))[:60])\n")
    for label, argv in [("python -c", [sys.executable, "-c", probe]),
                        ("python script.py", [sys.executable, sp]),
                        ("python -m modpkg_probe", [sys.executable, "-m", "modpkg_probe"]),
                        ("python -I -c (isolated)", [sys.executable, "-I", "-c", probe]),
                        ("python - (stdin)", [sys.executable, "-"])]:
        kw = dict(capture_output=True, text=True, cwd=d, timeout=60)
        if label.endswith("(stdin)"):
            r = subprocess.run(argv, input="import sys\nprint('has_spec=',hasattr(sys.modules['__main__'],'__spec__'))\n", **kw)
        else:
            env = dict(os.environ)
            if "-m" in argv:
                env["PYTHONPATH"] = d
            r = subprocess.run(argv, capture_output=True, text=True, cwd=d, timeout=60, env=env)
        say("  %-24s -> %s" % (label, (r.stdout.strip() or r.stderr.strip())[:96]))
finally:
    import shutil; shutil.rmtree(d, ignore_errors=True)

say("  -- and the ORIGINAL_DIR=None leg of my original claim --")
import multiprocessing.process as mpp
src = open(mpp.__file__, encoding="utf-8").read()
for mm in re.finditer(r"^ORIGINAL_DIR.*$", src, re.M):
    say("     process.py |", mm.group(0).strip())
say("     runtime value:", repr(getattr(mpp, "ORIGINAL_DIR", "<absent>")))
sp2 = open(os.path.join(STDLIB, "multiprocessing", "spawn.py"), encoding="utf-8").read()
for mm in re.finditer(r".*ORIGINAL_DIR.*", sp2):
    say("     spawn.py   |", mm.group(0).strip()[:110])

# ---------------------------------------------------------------- #96
say("\n### #96 real zipfile CLI against a genuine symlink loop")
zpath = os.path.join(STDLIB, "zipfile", "__init__.py")
zsrc = open(zpath, encoding="utf-8").read()
i = zsrc.index("def addToZip(")
frag = zsrc[i:i + 700]
say("  addToZip source fragment:")
for line in frag.splitlines()[:16]:
    say("     |", line)
say("  mentions islink   :", "islink" in frag)
say("  mentions realpath :", "realpath" in frag)
say("  has visited set   :", bool(re.search(r"seen|visited", frag)))

d = tempfile.mkdtemp()
try:
    sub = os.path.join(d, "sub")
    os.makedirs(sub)
    try:
        os.symlink(sub, os.path.join(sub, "loop"))
        made = True
    except OSError as e:
        made = False
        say("  (cannot create symlink on this host:", e, ")")
    if made:
        say("  os.path.isdir(sub/loop) =", os.path.isdir(os.path.join(sub, "loop")),
            "(follows the link)")
        out = os.path.join(d, "out.zip")
        code = ("import sys,zipfile;"
                "sys.setrecursionlimit(300);"
                "zipfile.main(['-c',%r,%r])" % (out, sub))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
        tail = (r.stderr.strip().splitlines() or ["<no stderr>"])[-1]
        say("  run with recursionlimit=300 -> rc=%d" % r.returncode)
        say("  last stderr line:", tail[:120])
        say("  zip size bytes  :", os.path.getsize(out) if os.path.exists(out) else "<not created>")
        say("  => recursion is unbounded (no islink guard):",
            r.returncode != 0 and "RecursionError" in r.stderr)
finally:
    import shutil; shutil.rmtree(d, ignore_errors=True)

# ---------------------------------------------------------------- #26
say("\n### #26 pydoc TextRepr.repr_instance -- bare except")
import pydoc
psrc2 = open(pydoc.__file__, encoding="utf-8").read()
m = re.search(r"\n    def repr_instance\(self, x, level\):(.*?)\n    def ", psrc2, re.S)
frag = m.group(1) if m else ""
say("  source:")
for line in frag.strip().splitlines():
    say("     |", line)
say("  bare 'except:' present  :", bool(re.search(r"except\s*:", frag)))
say("  'except Exception' used :", "except Exception" in frag)

class BoomKI:
    def __repr__(self):
        raise KeyboardInterrupt("user pressed Ctrl-C")

class BoomSE:
    def __repr__(self):
        raise SystemExit(3)

class BoomClass:
    @property
    def __class__(self):
        raise RuntimeError("cannot even name my class")
    def __repr__(self):
        raise ValueError("repr failed")

for label, obj in [("repr raises KeyboardInterrupt", BoomKI()),
                   ("repr raises SystemExit", BoomSE()),
                   ("repr AND __class__ both raise", BoomClass())]:
    say("  ATTACK %-32s ->" % label, end=" ")
    try:
        say("SWALLOWED, returned %r" % (pydoc.text.repr_instance(obj, 0),))
    except BaseException as e:
        say("propagated %s: %s" % (type(e).__name__, str(e)[:40]))
say("  POSITIVE CONTROL normal object:", repr(pydoc.text.repr_instance(object(), 0))[:60])
say("  NEGATIVE CONTROL plain failing repr falls back:", end=" ")
class BoomPlain:
    def __repr__(self):
        raise ValueError("nope")
say(repr(pydoc.text.repr_instance(BoomPlain(), 0)))

say("\n" + "=" * 78)
say("pass 2 done")
