"""Execution verification of every unit I graded truth=1, against the real
Python 3.13.12 stdlib that the E-B2-4 workbook sampled.

Discipline: each test carries a POSITIVE and a NEGATIVE control so that a
broken harness cannot masquerade as "the target is fine" (the exact trap that
produced two false negatives while checking #98).
"""
import io, os, pickle, re, struct, subprocess, sys, sysconfig, tempfile, textwrap

BS = chr(92)
OUT = sys.__stdout__
def say(*a):
    OUT.write(" ".join(str(x) for x in a) + "\n")
    OUT.flush()

say("python =", sys.version.split()[0], "| stdlib =", sysconfig.get_paths()["stdlib"])
say("=" * 78)

# ---------------------------------------------------------------- #12 imaplib
say("\n### #12 imaplib.IMAP4.uid -- does the hardcoded FETCH lose a COPY response?")
import imaplib
cmds = imaplib.Commands
say("  'COPY' in Commands          :", "COPY" in cmds, "| states:", cmds.get("COPY"))
say("  'MOVE' in Commands          :", "MOVE" in cmds, "| states:", cmds.get("MOVE"))
say("  'FETCH' in Commands         :", "FETCH" in cmds)
src = open(imaplib.__file__, encoding="utf-8").read()
m = re.search(r"def uid\(self, command, \*args\):(.*?)\n    def ", src, re.S)
body = m.group(1) if m else ""
say("  uid() hardcodes name='FETCH':", "name = 'FETCH'" in body)
say("  uid() honours COPY/MOVE     :", bool(re.search(r"'COPY'|'MOVE'", body)))
c = re.search(r"def copy\(self.*?\):(.*?)\n    def ", src, re.S)
say("  non-UID copy() uses 'COPY'  :", "'COPY'" in (c.group(1) if c else ""))

# ---------------------------------------------------------------- #20 pickle
say("\n### #20 pickle._Unpickler.load_binbytes -- short reads")
# BINBYTES opcode + declared length 100 but only 3 payload bytes available
stream = pickle.PROTO + bytes([3]) + b"B" + struct.pack("<I", 100) + b"abc" + b"."
try:
    r = pickle.loads(stream)
    say("  truncated BINBYTES -> silently returned:", repr(r), "(NO error raised)")
except Exception as e:
    say("  truncated BINBYTES ->", type(e).__name__ + ":", str(e)[:90])
say("  NEGATIVE CONTROL well-formed BINBYTES:")
good = pickle.PROTO + bytes([3]) + b"B" + struct.pack("<I", 3) + b"abc" + b"."
try:
    say("    ->", repr(pickle.loads(good)), "(must be b'abc')")
except Exception as e:
    say("    -> UNEXPECTED", type(e).__name__, e)
say("  2-byte stream (header itself short):")
try:
    pickle.loads(b"B" + b"\x01")
except Exception as e:
    say("    ->", type(e).__name__ + ":", str(e)[:70],
        "| is UnpicklingError:", isinstance(e, pickle.UnpicklingError))
import pickletools  # noqa
say("  load_binbytes uses _readbytes helper?:",
    "_readbytes" in re.search(r"def load_binbytes.*?\n    dispatch", open(pickle.__file__, encoding="utf-8").read(), re.S).group(0))

# ---------------------------------------------------------------- #25 pyclbr
say("\n### #25 pyclbr -- is __all__ honoured for 'from m import *'?")
import pyclbr
d = tempfile.mkdtemp()
try:
    with open(os.path.join(d, "submod.py"), "w", encoding="utf-8") as f:
        f.write(textwrap.dedent("""
            __all__ = ['A']
            class A: pass
            class B: pass
        """))
    with open(os.path.join(d, "main_mod.py"), "w", encoding="utf-8") as f:
        f.write("from submod import *\n")
    tree = pyclbr.readmodule_ex("main_mod", [d])
    names = sorted(k for k in tree if not k.startswith("__"))
    say("  pyclbr tree names      :", names)
    # runtime ground truth for the same import
    code = ("import sys; sys.path.insert(0,%r);"
            "from submod import *;"
            "print(sorted(n for n in dir() if not n.startswith('__') and n!='sys'))" % d)
    rt = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    say("  runtime bound names    :", rt.stdout.strip() or rt.stderr.strip()[:90])
    say("  => B present in pyclbr but NOT at runtime:",
        "B" in names and "B" not in rt.stdout)
finally:
    import shutil; shutil.rmtree(d, ignore_errors=True)

# ---------------------------------------------------------------- #31 tarfile
say("\n### #31 tarfile._proc_gnusparse_01 -- odd-length GNU.sparse.map")
import tarfile
ti = tarfile.TarInfo()
nxt = tarfile.TarInfo()
for label, val in [("POSITIVE CONTROL even (3 pairs)", "0,10,20,30,40,50"),
                   ("ATTACK odd (5 values)", "0,10,20,30,40"),
                   ("ATTACK single value", "7")]:
    try:
        ti._proc_gnusparse_01(nxt, {"GNU.sparse.map": val})
        say("  %-32s -> sparse=%r  (input had %d values)" % (label, nxt.sparse, len(val.split(","))))
    except Exception as e:
        say("  %-32s -> %s: %s" % (label, type(e).__name__, e))
try:
    ti._proc_gnusparse_01(nxt, {"GNU.sparse.map": "abc"})
    say("  ATTACK non-numeric                 -> NO error")
except Exception as e:
    say("  ATTACK non-numeric                 -> %s (not a TarError: %s)"
        % (type(e).__name__, isinstance(e, tarfile.TarError)))
try:
    ti._proc_gnusparse_01(nxt, {})
except Exception as e:
    say("  ATTACK missing key                 -> %s (not a TarError: %s)"
        % (type(e).__name__, isinstance(e, tarfile.TarError)))

# ---------------------------------------------------------------- #33 tokenize
say("\n### #33 tokenize.main -- does Ctrl-C exit 0?")
import tokenize
tsrc = open(tokenize.__file__, encoding="utf-8").read()
m = re.search(r"except KeyboardInterrupt:\n(.*?)(?=\n    except |\Z)", tsrc, re.S)
say("  KeyboardInterrupt handler body:", repr(m.group(1).strip()) if m else "NOT FOUND")
say("  contains sys.exit / raise     :", bool(m and re.search(r"sys\.exit|raise", m.group(1))))
say("  NEGATIVE CONTROL error() does exit(1):",
    "sys.exit(1)" in re.search(r"def error\(message.*?\n\n", tsrc, re.S).group(0))

# ---------------------------------------------------------------- #37 webbrowser
say("\n### #37 webbrowser.register_standard_browsers -- decode gap")
import webbrowser
wsrc = open(webbrowser.__file__, encoding="utf-8").read()
m = re.search(r"raw_result = subprocess\.check_output.*?\n(\s*)except \((.*?)\):", wsrc, re.S)
say("  except tuple:", re.sub(r"\s+", " ", m.group(2)) if m else "NOT FOUND")
say("  UnicodeDecodeError covered:", bool(m and "UnicodeDecodeError" in m.group(2)))
say("  .decode() called without errors=:",
    bool(re.search(r"raw_result\.decode\(\)", wsrc)))

# ---------------------------------------------------------------- #55 namedtuple
say("\n### #55 collections.namedtuple -- is the declared TypeError reachable?")
import collections
for label, args, kw in [("non-str field names", ("P", [1, 2]), {}),
                        ("non-str typename", (123, "x y"), {}),
                        ("POSITIVE CONTROL valid", ("P", ["x", "y"]), {}),
                        ("NEGATIVE CONTROL keyword field", ("P", ["class"]), {})]:
    try:
        r = collections.namedtuple(*args, **kw)
        say("  %-30s -> OK %s" % (label, r._fields if hasattr(r, "_fields") else ""))
    except Exception as e:
        say("  %-30s -> %s: %s" % (label, type(e).__name__, str(e)[:60]))
csrc = open(collections.__file__, encoding="utf-8").read()
nt = re.search(r"def namedtuple\(typename.*?\n\ndef ", csrc, re.S)
say("  source does map(str, field_names) BEFORE the type check:",
    bool(nt and nt.group(0).index("map(str,") < nt.group(0).index("must be strings")))

# ---------------------------------------------------------------- #62 email
say("\n### #62 email._header_value_parser.get_local_part -- message text")
import email._header_value_parser as hvp
hsrc = open(hvp.__file__, encoding="utf-8").read()
for m in re.finditer(r'NonASCIILocalPartDefect\(\s*\n?\s*("(?:[^"\\]|\\.)*")', hsrc):
    say("  literal in source:", m.group(1))
say("  unbalanced ')' present:", "characters)\"" in hsrc)
# trigger it for real
try:
    lp, rest = hvp.get_local_part("caf\u00e9@example.com".split("@")[0])
    say("  live defects:", [ (type(d).__name__, str(d)) for d in lp.defects ])
except Exception as e:
    say("  live call ->", type(e).__name__, e)

# ---------------------------------------------------------------- #80 multiprocessing
say("\n### #80 multiprocessing.spawn.get_preparation_data")
import multiprocessing.spawn as sp
ssrc = open(sp.__file__, encoding="utf-8").read()
say("  uses main_module.__spec__ unguarded :", "main_module.__spec__" in ssrc)
say("  uses getattr(main_module,'__file__'):", "getattr(main_module, '__file__', None)" in ssrc)
say("  sys_path[i] = process.ORIGINAL_DIR  :", "sys_path[i] = process.ORIGINAL_DIR" in ssrc)
say("  guards ORIGINAL_DIR is not None     :", "process.ORIGINAL_DIR is not None" in ssrc)
import multiprocessing.process as mp
say("  process.ORIGINAL_DIR default value  :", repr(getattr(mp, "ORIGINAL_DIR", "<absent>")))
# reproduce the AttributeError with a __main__ that lacks __spec__
import types, importlib
fake = types.ModuleType("__main__")
say("  fresh ModuleType has __spec__ attr  :", hasattr(fake, "__spec__"))
if hasattr(fake, "__spec__"):
    try:
        delattr(fake, "__spec__")
    except AttributeError as e:
        say("  could not delete __spec__:", e)
say("  after removal, has __spec__         :", hasattr(fake, "__spec__"))
saved = sys.modules.get("__main__")
try:
    sys.modules["__main__"] = fake
    try:
        sp.get_preparation_data("child")
        say("  with __main__ lacking __spec__      -> NO error")
    except AttributeError as e:
        say("  with __main__ lacking __spec__      -> AttributeError:", e)
    except Exception as e:
        say("  with __main__ lacking __spec__      -> %s: %s" % (type(e).__name__, str(e)[:70]))
finally:
    if saved is not None:
        sys.modules["__main__"] = saved

# ---------------------------------------------------------------- #93 ElementInclude
say("\n### #93 xml.etree.ElementInclude._include -- xi:include without href")
import xml.etree.ElementTree as ET
import xml.etree.ElementInclude as EI
doc = ET.fromstring('<root xmlns:xi="http://www.w3.org/2001/XInclude">'
                    '<xi:include parse="text"/></root>')
try:
    EI.include(doc)
    say("  no-href include -> NO error")
except EI.FatalIncludeError as e:
    say("  no-href include -> FatalIncludeError (contract honoured):", str(e)[:70])
except Exception as e:
    say("  no-href include -> %s (NOT FatalIncludeError): %s" % (type(e).__name__, str(e)[:80]))
say("  NEGATIVE CONTROL unknown parse attr:")
doc2 = ET.fromstring('<root xmlns:xi="http://www.w3.org/2001/XInclude">'
                     '<xi:include href="x" parse="bogus"/></root>')
try:
    EI.include(doc2)
except EI.FatalIncludeError as e:
    say("    -> FatalIncludeError:", str(e)[:60])
except Exception as e:
    say("    ->", type(e).__name__, str(e)[:60])

# ---------------------------------------------------------------- #96 zipfile
say("\n### #96 zipfile.main addToZip -- symlink recursion guard?")
zsrc = open(os.path.join(sysconfig.get_paths()["stdlib"], "zipfile", "__init__.py"), encoding="utf-8").read()
mm = re.search(r"def addToZip\(zf, path, zippath\):(.*?)\n        # else|\n        with ZipFile", zsrc, re.S)
frag = mm.group(1) if mm else zsrc[zsrc.index("def addToZip"):][:420]
say("  addToZip body mentions os.path.islink :", "islink" in frag)
say("  addToZip body has a visited/seen set  :", bool(re.search(r"seen|visited|realpath", frag)))
say("  addToZip recurses into isdir branch   :", "addToZip(zf," in frag)
say("  fragment:")
for line in frag.strip().splitlines():
    say("     |", line)

# ---------------------------------------------------------------- #26 pydoc
say("\n### #26 pydoc TextRepr.repr_instance -- bare except?")
import pydoc
psrc = open(pydoc.__file__, encoding="utf-8").read()
m = re.search(r"def repr_instance\(self, x, level\):(.*?)\n    def ", psrc, re.S)
frag = m.group(1) if m else ""
say("  uses bare 'except:'        :", bool(re.search(r"except\s*:", frag)))
say("  uses 'except Exception'    :", "except Exception" in frag)
class Boom:
    def __repr__(self):
        raise KeyboardInterrupt
say("  live: repr_instance(obj whose __repr__ raises KeyboardInterrupt)")
try:
    r = pydoc.text.repr_instance(Boom(), 0)
    say("    -> SWALLOWED, returned:", repr(r))
except KeyboardInterrupt:
    say("    -> KeyboardInterrupt propagated (not swallowed)")
say("  fragment:")
for line in frag.strip().splitlines():
    say("     |", line)

say("\n" + "=" * 78)
say("done")
