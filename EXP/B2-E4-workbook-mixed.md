# E-B2-4 参照标准定向工作簿（100 单元）

> 靶仓：Python 标准库（N=18198 单元）｜池 4 个｜零覆盖 97.8%
> **这份工作簿不是让你标真值**——人不是真值（Devign 4 专家 × 600 人时 × 两轮交叉，
> 复测正确率仅 24%）。它的作用是 **定向**（打破 Hui–Walter 镜像等价解）、
> **一致性量化**（双盲 → Cohen's κ，κ<0.60 则该轴标称作废）、**误差棒**。
> 判不出来填 `None`——None 比猜一个 0/1 有价值得多。
> 分层分布：{'random': 30, 'confluence': 20, 'zero_cover': 25, 'anchor': 25}

---
## #1 · random · `_dims_setter`

- **位置**：`ast.py:681`（2 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def _dims_setter(self, value):
        self.elts = value
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #2 · random · `StreamReaderWriter.readline`

- **位置**：`codecs.py:712`（3 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`StreamReader.readline`, `StreamReader.__next__`, `StreamRecoder.readline`（跨文件调用者未扫描）

**源码**：

```python
    def readline(self, size=None, keepends=True):

        return self.reader.readline(size, keepends)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #3 · confluence · `_maybe_compile`

- **位置**：`codeop.py:50`（26 行）
- **层**：confluence ｜ 曲率汇合点 forman=-224
- **结构量**：Forman=-224 ｜ 池：（不在任何池内）
- **本函数调用**：`catch_warnings`, `compiler`, `simplefilter`, `split`, `strip`
- **同文件调用者**：`compile_command`, `CommandCompiler.__call__`（跨文件调用者未扫描）

**源码**：

```python
def _maybe_compile(compiler, source, filename, symbol):
    # Check for source consisting of only blank lines and comments.
    for line in source.split("\n"):
        line = line.strip()
        if line and line[0] != '#':
            break               # Leave it alone.
    else:
        if symbol != "eval":
            source = "pass"     # Replace it with a 'pass' statement

    # Disable compiler warnings when checking for incomplete input.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", (SyntaxWarning, DeprecationWarning))
        try:
            compiler(source, filename, symbol)
        except SyntaxError:  # Let other compile() errors propagate.
            try:
                compiler(source + "\n", filename, symbol)
                return None
            except _IncompleteInputError as e:
                return None
            except SyntaxError as e:
                pass
                # fallthrough

    return compiler(source, filename, symbol, incomplete_input=False)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #4 · confluence · `_update_func_cell_for__class__`

- **位置**：`dataclasses.py:1222`（27 行）
- **层**：confluence ｜ 曲率汇合点 forman=-183
- **结构量**：Forman=-183 ｜ 池：（不在任何池内）
- **本函数调用**：`index`
- **同文件调用者**：`_add_slots`（跨文件调用者未扫描）

**源码**：

```python
def _update_func_cell_for__class__(f, oldcls, newcls):
    # Returns True if we update a cell, else False.
    if f is None:
        # f will be None in the case of a property where not all of
        # fget, fset, and fdel are used.  Nothing to do in that case.
        return False
    try:
        idx = f.__code__.co_freevars.index("__class__")
    except ValueError:
        # This function doesn't reference __class__, so nothing to do.
        return False
    # Fix the cell to point to the new class, if it's already pointing
    # at the old class.
    closure = f.__closure__[idx]

    try:
        contents = closure.cell_contents
    except ValueError:
        # Cell is empty
        return False

    # This check makes it so we avoid updating an incorrect cell if the
    # class body contains a function that was defined in a different class.
    if contents is oldcls:
        closure.cell_contents = newcls
        return True
    return False
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #5 · zero_cover · `_is_internal_class`

- **位置**：`enum.py:69`（8 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=-94 ｜ 池：（不在任何池内）
- **本函数调用**：`endswith`, `getattr`, `isinstance`
- **同文件调用者**：`EnumDict.__setitem__`（跨文件调用者未扫描）

**源码**：

```python
def _is_internal_class(cls_name, obj):
    # do not use `re` as `re` imports `enum`
    if not isinstance(obj, type):
        return False
    qualname = getattr(obj, '__qualname__', '')
    s_pattern = cls_name + '.' + getattr(obj, '__name__', '')
    e_pattern = '.' + s_pattern
    return qualname == s_pattern or qualname.endswith(e_pattern)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #6 · random · `_round_to_figures`

- **位置**：`fractions.py:103`（37 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-171 ｜ 池：（不在任何池内）
- **本函数调用**：`_round_to_exponent`, `abs`, `len`, `str`
- **同文件调用者**：`Fraction._format_float_style`（跨文件调用者未扫描）

**源码**：

```python
def _round_to_figures(n, d, figures):
    """Round a rational number to a given number of significant figures.

    Rounds the rational number n/d to the given number of significant figures
    using the round-ties-to-even rule, and returns a triple
    (sign: bool, significand: int, exponent: int) representing the rounded
    value (-1)**sign * significand * 10**exponent.

    In the special case where n = 0, returns a significand of zero and
    an exponent of 1 - figures, for compatibility with formatting.
    Otherwise, the returned significand satisfies
    10**(figures - 1) <= significand < 10**figures.

    d must be positive, but n and d need not be relatively prime.
    figures must be positive.
    """
    # Special case for n == 0.
    if n == 0:
        return False, 0, 1 - figures

    # Find integer m satisfying 10**(m - 1) <= abs(n)/d <= 10**m. (If abs(n)/d
    # is a power of 10, either of the two possible values for m is fine.)
    str_n, str_d = str(abs(n)), str(d)
    m = len(str_n) - len(str_d) + (str_d <= str_n)

    # Round to a multiple of 10**(m - figures). The significand we get
    # satisfies 10**(figures - 1) <= significand <= 10**figures.
    exponent = m - figures
    sign, significand = _round_to_exponent(n, d, exponent)

    # Adjust in the case where significand == 10**figures, to ensure that
    # 10**(figures - 1) <= significand < 10**figures.
    if len(str(significand)) == figures + 1:
        significand //= 10
        exponent += 1

    return sign, significand, exponent
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #7 · confluence · `getfile`

- **位置**：`inspect.py:923`（27 行）
- **层**：confluence ｜ 曲率汇合点 forman=-239
- **结构量**：Forman=-239 ｜ 池：（不在任何池内）
- **本函数调用**：`OSError`, `TypeError`, `format`, `get`, `getattr`, `hasattr`, `isclass`, `iscode`, `isframe`, `isfunction`, `ismethod`, `ismodule`
- **同文件调用者**：`getsourcefile`, `getabsfile`, `findsource`, `getframeinfo`（跨文件调用者未扫描）

**源码**：

```python
def getfile(object):
    """Work out which source or compiled file an object was defined in."""
    if ismodule(object):
        if getattr(object, '__file__', None):
            return object.__file__
        raise TypeError('{!r} is a built-in module'.format(object))
    if isclass(object):
        if hasattr(object, '__module__'):
            module = sys.modules.get(object.__module__)
            if getattr(module, '__file__', None):
                return module.__file__
            if object.__module__ == '__main__':
                raise OSError('source code not available')
        raise TypeError('{!r} is a built-in class'.format(object))
    if ismethod(object):
        object = object.__func__
    if isfunction(object):
        object = object.__code__
    if istraceback(object):
        object = object.tb_frame
    if isframe(object):
        object = object.f_code
    if iscode(object):
        return object.co_filename
    raise TypeError('module, class, method, function, traceback, frame, or '
                    'code object was expected, got {}'.format(
                    type(object).__name__))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #8 · confluence · `getfullargspec`

- **位置**：`inspect.py:1340`（91 行）
- **层**：confluence ｜ 曲率汇合点 forman=-381
- **结构量**：Forman=-381 ｜ 池：（不在任何池内）
- **本函数调用**：`FullArgSpec`, `TypeError`, `_signature_from_callable`, `append`, `values`
- **同文件调用者**：`getcallargs`（跨文件调用者未扫描）

**源码**：

```python
def getfullargspec(func):
    """Get the names and default values of a callable object's parameters.

    A tuple of seven things is returned:
    (args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations).
    'args' is a list of the parameter names.
    'varargs' and 'varkw' are the names of the * and ** parameters or None.
    'defaults' is an n-tuple of the default values of the last n parameters.
    'kwonlyargs' is a list of keyword-only parameter names.
    'kwonlydefaults' is a dictionary mapping names from kwonlyargs to defaults.
    'annotations' is a dictionary mapping parameter names to annotations.

    Notable differences from inspect.signature():
      - the "self" parameter is always reported, even for bound methods
      - wrapper chains defined by __wrapped__ *not* unwrapped automatically
    """
    try:
        # Re: `skip_bound_arg=False`
        #
        # There is a notable difference in behaviour between getfullargspec
        # and Signature: the former always returns 'self' parameter for bound
        # methods, whereas the Signature always shows the actual calling
        # signature of the passed object.
        #
        # To simulate this behaviour, we "unbind" bound methods, to trick
        # inspect.signature to always return their first parameter ("self",
        # usually)

        # Re: `follow_wrapper_chains=False`
        #
        # getfullargspec() historically ignored __wrapped__ attributes,
        # so we ensure that remains the case in 3.3+

        sig = _signature_from_callable(func,
                                       follow_wrapper_chains=False,
                                       skip_bound_arg=False,
                                       sigcls=Signature,
                                       eval_str=False)
    except Exception as ex:
        # Most of the times 'signature' will raise ValueError.
        # But, it can also raise AttributeError, and, maybe something
        # else. So to be fully backwards compatible, we catch all
        # possible exceptions here, and reraise a TypeError.
        raise TypeError('unsupported callable') from ex

    args = []
    varargs = None
    varkw = None
    posonlyargs = []
    kwonlyargs = []
    annotations = {}
    defaults = ()
    kwdefaults = {}

    if sig.return_annotation is not sig.empty:
        annotations['return'] = sig.return_annotation

    for param in sig.parameters.values():
        kind = param.kind
        name = param.name
```

> 已截断（共 91 行），完整见 `inspect.py:1340`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #9 · confluence · `normalize`

- **位置**：`locale.py:381`（82 行）
- **层**：confluence ｜ 曲率汇合点 forman=-393
- **结构量**：Forman=-393 ｜ 池：p_hot, p_deep_conf
- **本函数调用**：`_append_modifier`, `_replace_encoding`, `get`, `lower`, `replace`, `split`
- **同文件调用者**：`_parse_localename`, `setlocale`（跨文件调用者未扫描）

**源码**：

```python
def normalize(localename):

    """ Returns a normalized locale code for the given locale
        name.

        The returned locale code is formatted for use with
        setlocale().

        If normalization fails, the original name is returned
        unchanged.

        If the given encoding is not known, the function defaults to
        the default encoding for the locale code just like setlocale()
        does.

    """
    # Normalize the locale name and extract the encoding and modifier
    code = localename.lower()
    if ':' in code:
        # ':' is sometimes used as encoding delimiter.
        code = code.replace(':', '.')
    if '@' in code:
        code, modifier = code.split('@', 1)
    else:
        modifier = ''
    if '.' in code:
        langname, encoding = code.split('.')[:2]
    else:
        langname = code
        encoding = ''

    # First lookup: fullname (possibly with encoding and modifier)
    lang_enc = langname
    if encoding:
        norm_encoding = encoding.replace('-', '')
        norm_encoding = norm_encoding.replace('_', '')
        lang_enc += '.' + norm_encoding
    lookup_name = lang_enc
    if modifier:
        lookup_name += '@' + modifier
    code = locale_alias.get(lookup_name, None)
    if code is not None:
        return code
    #print('first lookup failed')

    if modifier:
        # Second try: fullname without modifier (possibly with encoding)
        code = locale_alias.get(lang_enc, None)
        if code is not None:
            #print('lookup without modifier succeeded')
            if '@' not in code:
                return _append_modifier(code, modifier)
            if code.split('@', 1)[1].lower() == modifier:
                return code
        #print('second lookup failed')

    if encoding:
        # Third try: langname (without encoding, possibly with modifier)
        lookup_name = langname
        if modifier:
```

> 已截断（共 82 行），完整见 `locale.py:381`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #10 · random · `ixor`

- **位置**：`operator.py:407`（4 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
def ixor(a, b):
    "Same as a ^= b."
    a ^= b
    return a
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #11 · anchor · `spawnl`

- **位置**：`os.py:961`（8 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L4 `Execute file with arguments from args in a subprocess.` → import:import_subprocess

**源码**：

```python
    def spawnl(mode, file, *args):
        """spawnl(mode, file, *args) -> integer

Execute file with arguments from args in a subprocess.
If mode == P_NOWAIT return the pid of the process.
If mode == P_WAIT return the process's exit code if it exits normally;
otherwise return -SIG, where SIG is the signal that killed it. """
        return spawnv(mode, file, args)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #12 · random · `Pdb._hold_exceptions`

- **位置**：`pdb.py:602`（19 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Pdb.interaction`（跨文件调用者未扫描）

**源码**：

```python
    def _hold_exceptions(self, exceptions):
        """
        Context manager to ensure proper cleaning of exceptions references

        When given a chained exception instead of a traceback,
        pdb may hold references to many objects which may leak memory.

        We use this context manager to make sure everything is properly cleaned

        """
        try:
            self._chained_exceptions = exceptions
            self._chained_exception_index = len(exceptions) - 1
            yield
        finally:
            # we can't put those in forget as otherwise they would
            # be cleared on exception change
            self._chained_exceptions = tuple()
            self._chained_exception_index = 0
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #13 · random · `Pdb._help_message_from_doc`

- **位置**：`pdb.py:2287`（21 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Pdb.do_help`, `Pdb._print_invalid_arg`（跨文件调用者未扫描）

**源码**：

```python
    def _help_message_from_doc(self, doc, usage_only=False):
        lines = [line.strip() for line in doc.rstrip().splitlines()]
        if not lines:
            return "No help message found."
        if "" in lines:
            usage_end = lines.index("")
        else:
            usage_end = 1
        formatted = []
        indent = " " * len(self.prompt)
        for i, line in enumerate(lines):
            if i == 0:
                prefix = "Usage: "
            elif i < usage_end:
                prefix = "       "
            else:
                if usage_only:
                    break
                prefix = ""
            formatted.append(indent + prefix + line)
        return "\n".join(formatted)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #14 · zero_cover · `_Unframer.load_frame`

- **位置**：`pickle.py:307`（5 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_Unpickler.load_frame`（跨文件调用者未扫描）

**源码**：

```python
    def load_frame(self, frame_size):
        if self.current_frame and self.current_frame.read() != b'':
            raise UnpicklingError(
                "beginning of a new frame before end of current frame")
        self.current_frame = io.BytesIO(self.file_read(frame_size))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #15 · anchor · `_Unpickler.find_class`

- **位置**：`pickle.py:1608`（13 行）
- **层**：anchor ｜ 锚点命中 import:import_pickle
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`_Unpickler.load_inst`, `_Unpickler.load_global`, `_Unpickler.load_stack_global`, `_Unpickler.get_extension`（跨文件调用者未扫描）
- **锚点命中行**：
  - L3 `sys.audit('pickle.find_class', module, name)` → import:import_pickle

**源码**：

```python
    def find_class(self, module, name):
        # Subclasses may override this.
        sys.audit('pickle.find_class', module, name)
        if self.proto < 3 and self.fix_imports:
            if (module, name) in _compat_pickle.NAME_MAPPING:
                module, name = _compat_pickle.NAME_MAPPING[(module, name)]
            elif module in _compat_pickle.IMPORT_MAPPING:
                module = _compat_pickle.IMPORT_MAPPING[module]
        __import__(module, level=0)
        if self.proto >= 4:
            return _getattribute(sys.modules[module], name)[0]
        else:
            return getattr(sys.modules[module], name)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #16 · anchor · `OpcodeInfo.__init__`

- **位置**：`pickletools.py:1124`（27 行）
- **层**：anchor ｜ 锚点命中 import:import_pickle
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`ArgumentDescriptor.__init__`, `StackObject.__init__`, `_Example.__init__`（跨文件调用者未扫描）
- **锚点命中行**：
  - L23 `assert isinstance(proto, int) and 0 <= proto <= pickle.HIGHEST_PROTOCOL` → import:import_pickle

**源码**：

```python
    def __init__(self, name, code, arg,
                 stack_before, stack_after, proto, doc):
        assert isinstance(name, str)
        self.name = name

        assert isinstance(code, str)
        assert len(code) == 1
        self.code = code

        assert arg is None or isinstance(arg, ArgumentDescriptor)
        self.arg = arg

        assert isinstance(stack_before, list)
        for x in stack_before:
            assert isinstance(x, StackObject)
        self.stack_before = stack_before

        assert isinstance(stack_after, list)
        for x in stack_after:
            assert isinstance(x, StackObject)
        self.stack_after = stack_after

        assert isinstance(proto, int) and 0 <= proto <= pickle.HIGHEST_PROTOCOL
        self.proto = proto

        assert isinstance(doc, str)
        self.doc = doc
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #17 · zero_cover · `Profile.create_stats`

- **位置**：`profile.py:399`（3 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Profile.dump_stats`（跨文件调用者未扫描）

**源码**：

```python
    def create_stats(self):
        self.simulate_cmd_complete()
        self.snapshot_stats()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #18 · random · `TextRepr.__init__`

- **位置**：`pydoc.py:1235`（5 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_start_server`, `ErrorDuringImport.__init__`, `HTMLRepr.__init__`, `HTMLDoc.docclass`, `TextDoc.docclass`, `Helper.__init__`, `DocServer.__init__`, `ServerThread.__init__`（跨文件调用者未扫描）

**源码**：

```python
    def __init__(self):
        Repr.__init__(self)
        self.maxlist = self.maxtuple = 20
        self.maxdict = 10
        self.maxstring = self.maxother = 100
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #19 · confluence · `_rmtree_unsafe`

- **位置**：`shutil.py:608`（28 行）
- **层**：confluence ｜ 曲率汇合点 forman=-367
- **结构量**：Forman=-367 ｜ 池：（不在任何池内）
- **本函数调用**：`isinstance`, `join`, `onexc`, `rmdir`, `unlink`, `walk`
- **同文件调用者**：`rmtree`（跨文件调用者未扫描）

**源码**：

```python
def _rmtree_unsafe(path, onexc):
    def onerror(err):
        if not isinstance(err, FileNotFoundError):
            onexc(os.scandir, err.filename, err)
    results = os.walk(path, topdown=False, onerror=onerror, followlinks=os._walk_symlinks_as_files)
    for dirpath, dirnames, filenames in results:
        for name in dirnames:
            fullname = os.path.join(dirpath, name)
            try:
                os.rmdir(fullname)
            except FileNotFoundError:
                continue
            except OSError as err:
                onexc(os.rmdir, fullname, err)
        for name in filenames:
            fullname = os.path.join(dirpath, name)
            try:
                os.unlink(fullname)
            except FileNotFoundError:
                continue
            except OSError as err:
                onexc(os.unlink, fullname, err)
    try:
        os.rmdir(path)
    except FileNotFoundError:
        pass
    except OSError as err:
        onexc(os.rmdir, path, err)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #20 · random · `_SocketWriter.writable`

- **位置**：`socketserver.py:841`（2 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def writable(self):
        return True
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #21 · anchor · `check_output`

- **位置**：`subprocess.py:423`（51 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=-217 ｜ 池：p_anchor_breadth
- **本函数调用**：`ValueError`, `get`, `run`
- **同文件调用者**：`getstatusoutput`（跨文件调用者未扫描）
- **锚点命中行**：
  - L22 `pass a string to the subprocess's stdin.  If you use this argument` → import:import_subprocess

**源码**：

```python
def check_output(*popenargs, timeout=None, **kwargs):
    r"""Run command with arguments and return its output.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute and output in the output attribute.

    The arguments are the same as for the Popen constructor.  Example:

    >>> check_output(["ls", "-l", "/dev/null"])
    b'crw-rw-rw- 1 root root 1, 3 Oct 18  2007 /dev/null\n'

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use stderr=STDOUT.

    >>> check_output(["/bin/sh", "-c",
    ...               "ls -l non_existent_file ; exit 0"],
    ...              stderr=STDOUT)
    b'ls: non_existent_file: No such file or directory\n'

    There is an additional optional argument, "input", allowing you to
    pass a string to the subprocess's stdin.  If you use this argument
    you may not also use the Popen constructor's "stdin" argument, as
    it too will be used internally.  Example:

    >>> check_output(["sed", "-e", "s/foo/bar/"],
    ...              input=b"when in the course of fooman events\n")
    b'when in the course of barman events\n'

    By default, all communication is in bytes, and therefore any "input"
    should be bytes, and the return value will be bytes.  If in text mode,
    any "input" should be a string, and the return value will be a string
    decoded according to locale encoding, or by "encoding" if set. Text mode
    is triggered by setting any of text, encoding, errors or universal_newlines.
    """
    for kw in ('stdout', 'check'):
        if kw in kwargs:
            raise ValueError(f'{kw} argument not allowed, it will be overridden.')

    if 'input' in kwargs and kwargs['input'] is None:
        # Explicitly passing input=None was previously equivalent to passing an
        # empty string. That is maintained here for backwards compatibility.
        if kwargs.get('universal_newlines') or kwargs.get('text') or kwargs.get('encoding') \
                or kwargs.get('errors'):
            empty = ''
        else:
            empty = b''
        kwargs['input'] = empty

    return run(*popenargs, stdout=PIPE, timeout=timeout, check=True,
               **kwargs).stdout
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #22 · random · `_MainThread.__init__`

- **位置**：`threading.py:1353`（9 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_RLock.__init__`, `Condition.__init__`, `Semaphore.__init__`, `BoundedSemaphore.__init__`, `Event.__init__`, `Barrier.__init__`, `Thread.__init__`, `Thread.__repr__`（跨文件调用者未扫描）

**源码**：

```python
    def __init__(self):
        Thread.__init__(self, name="MainThread", daemon=False)
        self._started.set()
        self._ident = _get_main_thread_ident()
        self._handle = _make_thread_handle(self._ident)
        if _HAVE_THREAD_NATIVE_ID:
            self._set_native_id()
        with _active_limbo_lock:
            _active[self._ident] = self
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #23 · zero_cover · `print_stack`

- **位置**：`traceback.py:230`（10 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=-3 ｜ 池：（不在任何池内）
- **本函数调用**：`_getframe`, `extract_stack`, `print_list`
- **同文件调用者**：`extract_stack`（跨文件调用者未扫描）

**源码**：

```python
def print_stack(f=None, limit=None, file=None):
    """Print a stack trace from its invocation point.

    The optional 'f' argument can be used to specify an alternate
    stack frame at which to start. The optional 'limit' and 'file'
    arguments have the same meaning as for print_exception().
    """
    if f is None:
        f = sys._getframe().f_back
    print_list(extract_stack(f, limit=limit), file=file)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #24 · anchor · `register_standard_browsers`

- **位置**：`webbrowser.py:491`（87 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=-372 ｜ 池：p_anchor_breadth
- **本函数调用**：`BackgroundBrowser`, `Edge`, `Elinks`, `GenericBrowser`, `IOSBrowser`, `MacOSXOSAScript`, `_synthesize`, `check_output`, `decode`, `get`, `join`, `register`
- **同文件调用者**：`register`, `get`, `open`（跨文件调用者未扫描）
- **锚点命中行**：
  - L47 `raw_result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)` → import:import_subprocess
  - L49 `except (FileNotFoundError, subprocess.CalledProcessError,` → import:import_subprocess

**源码**：

```python
def register_standard_browsers():
    global _tryorder
    _tryorder = []

    if sys.platform == 'darwin':
        register("MacOSX", None, MacOSXOSAScript('default'))
        register("chrome", None, MacOSXOSAScript('chrome'))
        register("firefox", None, MacOSXOSAScript('firefox'))
        register("safari", None, MacOSXOSAScript('safari'))
        # OS X can use below Unix support (but we prefer using the OS X
        # specific stuff)

    if sys.platform == "ios":
        register("iosbrowser", None, IOSBrowser(), preferred=True)

    if sys.platform == "serenityos":
        # SerenityOS webbrowser, simply called "Browser".
        register("Browser", None, BackgroundBrowser("Browser"))

    if sys.platform[:3] == "win":
        # First try to use the default Windows browser
        register("windows-default", WindowsDefault)

        # Detect some common Windows browsers, fallback to Microsoft Edge
        # location in 64-bit Windows
        edge64 = os.path.join(os.environ.get("PROGRAMFILES(x86)", "C:\\Program Files (x86)"),
                              "Microsoft\\Edge\\Application\\msedge.exe")
        # location in 32-bit Windows
        edge32 = os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                              "Microsoft\\Edge\\Application\\msedge.exe")
        for browser in ("firefox", "seamonkey", "mozilla", "chrome",
                        "opera", edge64, edge32):
            if shutil.which(browser):
                register(browser, None, BackgroundBrowser(browser))
        if shutil.which("MicrosoftEdge.exe"):
            register("microsoft-edge", None, Edge("MicrosoftEdge.exe"))
    else:
        # Prefer X browsers if present
        #
        # NOTE: Do not check for X11 browser on macOS,
        # XQuartz installation sets a DISPLAY environment variable and will
        # autostart when someone tries to access the display. Mac users in
        # general don't need an X11 browser.
        if sys.platform != "darwin" and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            try:
                cmd = "xdg-settings get default-web-browser".split()
                raw_result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                result = raw_result.decode().strip()
            except (FileNotFoundError, subprocess.CalledProcessError,
                    PermissionError, NotADirectoryError):
                pass
            else:
                global _os_preferred_browser
                _os_preferred_browser = result

            register_X_browsers()

        # Also try console browsers
        if os.environ.get("TERM"):
            # Common symbolic link for the default text-based browser
```

> 已截断（共 87 行），完整见 `webbrowser.py:491`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #25 · anchor · `GenericBrowser.open`

- **位置**：`webbrowser.py:188`（13 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`open`, `open_new`, `open_new_tab`, `main`, `BaseBrowser.open`, `BaseBrowser.open_new`, `BaseBrowser.open_new_tab`, `BackgroundBrowser.open`（跨文件调用者未扫描）
- **锚点命中行**：
  - L8 `p = subprocess.Popen(cmdline)` → import:import_subprocess
  - L10 `p = subprocess.Popen(cmdline, close_fds=True)` → import:import_subprocess

**源码**：

```python
    def open(self, url, new=0, autoraise=True):
        sys.audit("webbrowser.open", url)
        self._check_url(url)
        cmdline = [self.name] + [arg.replace("%s", url)
                                 for arg in self.args]
        try:
            if sys.platform[:3] == 'win':
                p = subprocess.Popen(cmdline)
            else:
                p = subprocess.Popen(cmdline, close_fds=True)
            return not p.wait()
        except OSError:
            return False
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #26 · anchor · `Konqueror.open`

- **位置**：`webbrowser.py:369`（45 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`open`, `open_new`, `open_new_tab`, `main`, `BaseBrowser.open`, `BaseBrowser.open_new`, `BaseBrowser.open_new_tab`, `GenericBrowser.open`（跨文件调用者未扫描）
- **锚点命中行**：
  - L10 `devnull = subprocess.DEVNULL` → import:import_subprocess
  - L13 `p = subprocess.Popen(["kfmclient", action, url],` → import:import_subprocess
  - L25 `p = subprocess.Popen(["konqueror", "--silent", url],` → import:import_subprocess
  - L38 `p = subprocess.Popen(["kfm", "-d", url],` → import:import_subprocess

**源码**：

```python
    def open(self, url, new=0, autoraise=True):
        sys.audit("webbrowser.open", url)
        self._check_url(url)
        # XXX Currently I know no way to prevent KFM from opening a new win.
        if new == 2:
            action = "newTab"
        else:
            action = "openURL"

        devnull = subprocess.DEVNULL

        try:
            p = subprocess.Popen(["kfmclient", action, url],
                                 close_fds=True, stdin=devnull,
                                 stdout=devnull, stderr=devnull)
        except OSError:
            # fall through to next variant
            pass
        else:
            p.wait()
            # kfmclient's return code unfortunately has no meaning as it seems
            return True

        try:
            p = subprocess.Popen(["konqueror", "--silent", url],
                                 close_fds=True, stdin=devnull,
                                 stdout=devnull, stderr=devnull,
                                 start_new_session=True)
        except OSError:
            # fall through to next variant
            pass
        else:
            if p.poll() is None:
                # Should be running now.
                return True

        try:
            p = subprocess.Popen(["kfm", "-d", url],
                                 close_fds=True, stdin=devnull,
                                 stdout=devnull, stderr=devnull,
                                 start_new_session=True)
        except OSError:
            return False
        else:
            return p.poll() is None
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #27 · anchor · `_aix_bos_rte`

- **位置**：`_aix_support.py:42`（19 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=-226 ｜ 池：p_anchor_breadth
- **本函数调用**：`_read_cmd_output`, `check_output`, `decode`, `int`, `split`, `str`, `strip`
- **同文件调用者**：`aix_platform`（跨文件调用者未扫描）
- **锚点命中行**：
  - L10 `# subprocess may not be available during python bootstrap` → import:import_subprocess
  - L12 `import subprocess` → import:import_subprocess
  - L13 `out = subprocess.check_output(["/usr/bin/lslpp", "-Lqc", "bos.rte"])` → import:import_subprocess

**源码**：

```python
def _aix_bos_rte():
    # type: () -> Tuple[str, int]
    """
    Return a Tuple[str, int] e.g., ['7.1.4.34', 1806]
    The fileset bos.rte represents the current AIX run-time level. It's VRMF and
    builddate reflect the current ABI levels of the runtime environment.
    If no builddate is found give a value that will satisfy pep425 related queries
    """
    # All AIX systems to have lslpp installed in this location
    # subprocess may not be available during python bootstrap
    try:
        import subprocess
        out = subprocess.check_output(["/usr/bin/lslpp", "-Lqc", "bos.rte"])
    except ImportError:
        out = _read_cmd_output("/usr/bin/lslpp -Lqc bos.rte")
    out = out.decode("utf-8")
    out = out.strip().split(":")  # type: ignore
    _bd = int(out[-1]) if out[-1] != '' else 9988
    return (str(out[2]), _bd)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #28 · anchor · `timezone.__getinitargs__`

- **位置**：`_pydatetime.py:2347`（5 行）
- **层**：anchor ｜ 锚点命中 import:import_pickle
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L2 `"""pickle support"""` → import:import_pickle

**源码**：

```python
    def __getinitargs__(self):
        """pickle support"""
        if self._name is None:
            return (self._offset,)
        return (self._offset, self._name)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #29 · random · `Overflow.handle`

- **位置**：`_pydecimal.py:279`（14 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`DecimalException.handle`, `InvalidOperation.handle`, `ConversionSyntax.handle`, `DivisionByZero.handle`, `DivisionImpossible.handle`, `DivisionUndefined.handle`, `InvalidContext.handle`, `Context._raise_error`（跨文件调用者未扫描）

**源码**：

```python
    def handle(self, context, sign, *args):
        if context.rounding in (ROUND_HALF_UP, ROUND_HALF_EVEN,
                                ROUND_HALF_DOWN, ROUND_UP):
            return _SignedInfinity[sign]
        if sign == 0:
            if context.rounding == ROUND_CEILING:
                return _SignedInfinity[sign]
            return _dec_from_triple(sign, '9'*context.prec,
                            context.Emax-context.prec+1)
        if sign == 1:
            if context.rounding == ROUND_FLOOR:
                return _SignedInfinity[sign]
            return _dec_from_triple(sign, '9'*context.prec,
                             context.Emax-context.prec+1)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #30 · anchor · `BaseEventLoop._log_subprocess`

- **位置**：`asyncio/base_events.py:1736`（12 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`BaseEventLoop.subprocess_shell`, `BaseEventLoop.subprocess_exec`（跨文件调用者未扫描）
- **锚点命中行**：
  - L5 `if stdout is not None and stderr == subprocess.STDOUT:` → import:import_subprocess

**源码**：

```python
    def _log_subprocess(self, msg, stdin, stdout, stderr):
        info = [msg]
        if stdin is not None:
            info.append(f'stdin={_format_pipe(stdin)}')
        if stdout is not None and stderr == subprocess.STDOUT:
            info.append(f'stdout=stderr={_format_pipe(stdout)}')
        else:
            if stdout is not None:
                info.append(f'stdout={_format_pipe(stdout)}')
            if stderr is not None:
                info.append(f'stderr={_format_pipe(stderr)}')
        logger.debug(' '.join(info))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #31 · anchor · `AbstractEventLoop.subprocess_exec`

- **位置**：`asyncio/events.py:542`（6 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L2 `stdin=subprocess.PIPE,` → import:import_subprocess
  - L3 `stdout=subprocess.PIPE,` → import:import_subprocess
  - L4 `stderr=subprocess.PIPE,` → import:import_subprocess

**源码**：

```python
    async def subprocess_exec(self, protocol_factory, *args,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              **kwargs):
        raise NotImplementedError
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #32 · zero_cover · `AbstractEventLoop.set_exception_handler`

- **位置**：`asyncio/events.py:617`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def set_exception_handler(self, handler):
        raise NotImplementedError
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #33 · random · `_LoopBoundMixin._get_loop`

- **位置**：`asyncio/mixins.py:12`（10 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def _get_loop(self):
        loop = events._get_running_loop()

        if self._loop is None:
            with _global_lock:
                if self._loop is None:
                    self._loop = loop
        if loop is not self._loop:
            raise RuntimeError(f'{self!r} is bound to a different event loop')
        return loop
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #34 · zero_cover · `BaseSelectorEventLoop._add_reader`

- **位置**：`asyncio/selector_events.py:278`（14 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`BaseSelectorEventLoop._make_self_pipe`, `BaseSelectorEventLoop._start_serving`, `BaseSelectorEventLoop.add_reader`, `BaseSelectorEventLoop.sock_recv`, `BaseSelectorEventLoop.sock_recv_into`, `BaseSelectorEventLoop.sock_recvfrom`, `BaseSelectorEventLoop.sock_recvfrom_into`, `BaseSelectorEventLoop._sock_accept`（跨文件调用者未扫描）

**源码**：

```python
    def _add_reader(self, fd, callback, *args):
        self._check_closed()
        handle = events.Handle(callback, args, self, None)
        key = self._selector.get_map().get(fd)
        if key is None:
            self._selector.register(fd, selectors.EVENT_READ,
                                    (handle, None))
        else:
            mask, (reader, writer) = key.events, key.data
            self._selector.modify(fd, mask | selectors.EVENT_READ,
                                  (handle, writer))
            if reader is not None:
                reader.cancel()
        return handle
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #35 · random · `BaseSelectorEventLoop.sock_recvfrom`

- **位置**：`asyncio/selector_events.py:448`（22 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`BaseSelectorEventLoop._sock_recvfrom`（跨文件调用者未扫描）

**源码**：

```python
    async def sock_recvfrom(self, sock, bufsize):
        """Receive a datagram from a datagram socket.

        The return value is a tuple of (bytes, address) representing the
        datagram received and the address it came from.
        The maximum amount of data to be received at once is specified by
        nbytes.
        """
        base_events._check_ssl_socket(sock)
        if self._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")
        try:
            return sock.recvfrom(bufsize)
        except (BlockingIOError, InterruptedError):
            pass
        fut = self.create_future()
        fd = sock.fileno()
        self._ensure_fd_no_transport(fd)
        handle = self._add_reader(fd, self._sock_recvfrom, fut, sock, bufsize)
        fut.add_done_callback(
            functools.partial(self._sock_read_done, fd, handle=handle))
        return await fut
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #36 · zero_cover · `_SelectorSocketTransport._make_empty_waiter`

- **位置**：`asyncio/selector_events.py:1206`（7 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`BaseSelectorEventLoop._sendfile_native`（跨文件调用者未扫描）

**源码**：

```python
    def _make_empty_waiter(self):
        if self._empty_waiter is not None:
            raise RuntimeError("Empty waiter is already set")
        self._empty_waiter = self._loop.create_future()
        if not self._buffer:
            self._empty_waiter.set_result(None)
        return self._empty_waiter
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #37 · anchor · `SubprocessTransport.kill`

- **位置**：`asyncio/transports.py:241`（10 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L2 `"""Kill the subprocess.` → import:import_subprocess
  - L4 `On Posix OSs the function sends SIGKILL to the subprocess.` → import:import_subprocess
  - L8 `http://docs.python.org/3/library/subprocess#subprocess.Popen.kill` → import:import_subprocess

**源码**：

```python
    def kill(self):
        """Kill the subprocess.

        On Posix OSs the function sends SIGKILL to the subprocess.
        On Windows kill() is an alias for terminate().

        See also:
        http://docs.python.org/3/library/subprocess#subprocess.Popen.kill
        """
        raise NotImplementedError
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #38 · anchor · `namedtuple`

- **位置**：`collections/__init__.py:358`（173 行）
- **层**：anchor ｜ 锚点命中 sink:eval, import:import_pickle
- **结构量**：Forman=-222 ｜ 池：p_anchor_breadth, p_big1
- **本函数调用**：`TypeError`, `ValueError`, `_dict`, `_getframe`, `_getframemodulename`, `_iskeyword`, `_len`, `_make`, `_map`, `_tuple`, `_tuplegetter`, `_zip`
- **锚点命中行**：
  - L87 `__new__ = eval(code, namespace)` → sink:eval
  - L121 `'Return self as a plain tuple.  Used by copy and pickle.'` → import:import_pickle

**源码**：

```python
def namedtuple(typename, field_names, *, rename=False, defaults=None, module=None):
    """Returns a new subclass of tuple with named fields.

    >>> Point = namedtuple('Point', ['x', 'y'])
    >>> Point.__doc__                   # docstring for the new class
    'Point(x, y)'
    >>> p = Point(11, y=22)             # instantiate with positional args or keywords
    >>> p[0] + p[1]                     # indexable like a plain tuple
    33
    >>> x, y = p                        # unpack like a regular tuple
    >>> x, y
    (11, 22)
    >>> p.x + p.y                       # fields also accessible by name
    33
    >>> d = p._asdict()                 # convert to a dictionary
    >>> d['x']
    11
    >>> Point(**d)                      # convert from a dictionary
    Point(x=11, y=22)
    >>> p._replace(x=100)               # _replace() is like str.replace() but targets named fields
    Point(x=100, y=22)

    """

    # Validate the field names.  At the user's option, either generate an error
    # message or automatically replace the field name with a valid name.
    if isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    field_names = list(map(str, field_names))
    typename = _sys.intern(str(typename))

    if rename:
        seen = set()
        for index, name in enumerate(field_names):
            if (not name.isidentifier()
                or _iskeyword(name)
                or name.startswith('_')
                or name in seen):
                field_names[index] = f'_{index}'
            seen.add(name)

    for name in [typename] + field_names:
        if type(name) is not str:
            raise TypeError('Type names and field names must be strings')
        if not name.isidentifier():
            raise ValueError('Type names and field names must be valid '
                             f'identifiers: {name!r}')
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a '
                             f'keyword: {name!r}')

    seen = set()
    for name in field_names:
        if name.startswith('_') and not rename:
            raise ValueError('Field names cannot start with an underscore: '
                             f'{name!r}')
        if name in seen:
            raise ValueError(f'Encountered duplicate field name: {name!r}')
        seen.add(name)

```

> 已截断（共 173 行），完整见 `collections/__init__.py:358`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #39 · random · `test`

- **位置**：`ctypes/util.py:347`（39 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-213 ｜ 池：（不在任何池内）
- **本函数调用**：`CDLL`, `LoadLibrary`, `find_library`, `load`, `print`, `startswith`

**源码**：

```python
def test():
    from ctypes import cdll
    if os.name == "nt":
        print(cdll.msvcrt)
        print(cdll.load("msvcrt"))
        print(find_library("msvcrt"))

    if os.name == "posix":
        # find and load_version
        print(find_library("m"))
        print(find_library("c"))
        print(find_library("bz2"))

        # load
        if sys.platform == "darwin":
            print(cdll.LoadLibrary("libm.dylib"))
            print(cdll.LoadLibrary("libcrypto.dylib"))
            print(cdll.LoadLibrary("libSystem.dylib"))
            print(cdll.LoadLibrary("System.framework/System"))
        # issue-26439 - fix broken test call for AIX
        elif sys.platform.startswith("aix"):
            from ctypes import CDLL
            if sys.maxsize < 2**32:
                print(f"Using CDLL(name, os.RTLD_MEMBER): {CDLL('libc.a(shr.o)', os.RTLD_MEMBER)}")
                print(f"Using cdll.LoadLibrary(): {cdll.LoadLibrary('libc.a(shr.o)')}")
                # librpm.so is only available as 32-bit shared library
                print(find_library("rpm"))
                print(cdll.LoadLibrary("librpm.so"))
            else:
                print(f"Using CDLL(name, os.RTLD_MEMBER): {CDLL('libc.a(shr_64.o)', os.RTLD_MEMBER)}")
                print(f"Using cdll.LoadLibrary(): {cdll.LoadLibrary('libc.a(shr_64.o)')}")
            print(f"crypt\t:: {find_library('crypt')}")
            print(f"crypt\t:: {cdll.LoadLibrary(find_library('crypt'))}")
            print(f"crypto\t:: {find_library('crypto')}")
            print(f"crypto\t:: {cdll.LoadLibrary(find_library('crypto'))}")
        else:
            print(cdll.LoadLibrary("libm.so"))
            print(cdll.LoadLibrary("libcrypt.so"))
            print(find_library("crypt"))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #40 · anchor · `_findLib_gcc`

- **位置**：`ctypes/util.py:114`（48 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`find_library`, `find_library`, `find_library`（跨文件调用者未扫描）
- **锚点命中行**：
  - L23 `proc = subprocess.Popen(args,` → import:import_subprocess
  - L24 `stdout=subprocess.PIPE,` → import:import_subprocess
  - L25 `stderr=subprocess.STDOUT,` → import:import_subprocess

**源码**：

```python
    def _findLib_gcc(name):
        # Run GCC's linker with the -t (aka --trace) option and examine the
        # library name it prints out. The GCC command will fail because we
        # haven't supplied a proper program with main(), but that does not
        # matter.
        expr = os.fsencode(r'[^\(\)\s]*lib%s\.[^\(\)\s]*' % re.escape(name))

        c_compiler = shutil.which('gcc')
        if not c_compiler:
            c_compiler = shutil.which('cc')
        if not c_compiler:
            # No C compiler available, give up
            return None

        temp = tempfile.NamedTemporaryFile()
        try:
            args = [c_compiler, '-Wl,-t', '-o', temp.name, '-l' + name]

            env = dict(os.environ)
            env['LC_ALL'] = 'C'
            env['LANG'] = 'C'
            try:
                proc = subprocess.Popen(args,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        env=env)
            except OSError:  # E.g. bad executable
                return None
            with proc:
                trace = proc.stdout.read()
        finally:
            try:
                temp.close()
            except FileNotFoundError:
                # Raised if the file was already removed, which is the normal
                # behaviour of GCC if linking fails
                pass
        res = re.findall(expr, trace)
        if not res:
            return None

        for file in res:
            # Check if the given file is an elf file: gcc can report
            # some files that are linker scripts and not actual
            # shared objects. See bpo-41976 for more details
            if not _is_elf(file):
                continue
            return os.fsdecode(file)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #41 · random · `isctrl`

- **位置**：`curses/ascii.py:68`（1 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-13 ｜ 池：（不在任何池内）
- **本函数调用**：`_ctoi`

**源码**：

```python
def isctrl(c): return 0 <= _ctoi(c) < 32
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #42 · confluence · `_encode_base64`

- **位置**：`email/contentmanager.py:136`（7 行）
- **层**：confluence ｜ 曲率汇合点 forman=-380
- **结构量**：Forman=-380 ｜ 池：（不在任何池内）
- **本函数调用**：`append`, `b2a_base64`, `decode`, `join`, `len`, `range`
- **同文件调用者**：`_encode_text`, `set_bytes_content`（跨文件调用者未扫描）

**源码**：

```python
def _encode_base64(data, max_line_length):
    encoded_lines = []
    unencoded_bytes_per_line = max_line_length // 4 * 3
    for i in range(0, len(data), unencoded_bytes_per_line):
        thisline = data[i:i+unencoded_bytes_per_line]
        encoded_lines.append(binascii.b2a_base64(thisline).decode('ascii'))
    return ''.join(encoded_lines)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #43 · random · `encode_7or8bit`

- **位置**：`email/encoders.py:47`（15 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-82 ｜ 池：（不在任何池内）
- **本函数调用**：`decode`, `get_payload`

**源码**：

```python
def encode_7or8bit(msg):
    """Set the Content-Transfer-Encoding header to 7bit or 8bit."""
    orig = msg.get_payload(decode=True)
    if orig is None:
        # There's no payload.  For backwards compatibility we use 7bit
        msg['Content-Transfer-Encoding'] = '7bit'
        return
    # We play a trick to make this go fast.  If decoding from ASCII succeeds,
    # we know the data must be 7bit, otherwise treat it as 8bit.
    try:
        orig.decode('ascii')
    except UnicodeError:
        msg['Content-Transfer-Encoding'] = '8bit'
    else:
        msg['Content-Transfer-Encoding'] = '7bit'
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #44 · zero_cover · `Generator.__init__`

- **位置**：`email/generator.py:38`（31 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`DecodedGenerator.__init__`（跨文件调用者未扫描）

**源码**：

```python
    def __init__(self, outfp, mangle_from_=None, maxheaderlen=None, *,
                 policy=None):
        """Create the generator for message flattening.

        outfp is the output file-like object for writing the message to.  It
        must have a write() method.

        Optional mangle_from_ is a flag that, when True (the default if policy
        is not set), escapes From_ lines in the body of the message by putting
        a `>' in front of them.

        Optional maxheaderlen specifies the longest length for a non-continued
        header.  When a header line is longer (in characters, with tabs
        expanded to 8 spaces) than maxheaderlen, the header will split as
        defined in the Header class.  Set maxheaderlen to zero to disable
        header wrapping.  The default is 78, as recommended (but not required)
        by RFC 5322 section 2.1.1.

        The policy keyword specifies a policy object that controls a number of
        aspects of the generator's operation.  If no policy is specified,
        the policy associated with the Message object passed to the
        flatten method is used.

        """

        if mangle_from_ is None:
            mangle_from_ = True if policy is None else policy.mangle_from_
        self._fp = outfp
        self._mangle_from_ = mangle_from_
        self.maxheaderlen = maxheaderlen
        self.policy = policy
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #45 · confluence · `_au`

- **位置**：`email/mime/audio.py:84`（5 行）
- **层**：confluence ｜ 曲率汇合点 forman=-209
- **结构量**：Forman=-209 ｜ 池：（不在任何池内）
- **本函数调用**：`startswith`

**源码**：

```python
def _au(h):
    if h.startswith(b'.snd'):
        return 'basic'
    else:
        return None
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #46 · zero_cover · `StreamReader.decode`

- **位置**：`encodings/raw_unicode_escape.py:32`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`IncrementalDecoder._buffer_decode`（跨文件调用者未扫描）

**源码**：

```python
    def decode(self, input, errors='strict'):
        return codecs.raw_unicode_escape_decode(input, errors, False)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #47 · zero_cover · `StreamWriter.reset`

- **位置**：`encodings/utf_8_sig.py:86`（6 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`IncrementalEncoder.reset`, `IncrementalDecoder.reset`, `StreamReader.reset`（跨文件调用者未扫描）

**源码**：

```python
    def reset(self):
        codecs.StreamWriter.reset(self)
        try:
            del self.encode
        except AttributeError:
            pass
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #48 · anchor · `_run_pip`

- **位置**：`ensurepip/__init__.py:65`（24 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=-29 ｜ 池：p_anchor_breadth
- **本函数调用**：`insert`, `run`
- **同文件调用者**：`_bootstrap`, `_uninstall_helper`（跨文件调用者未扫描）
- **锚点命中行**：
  - L2 `# Run the bootstrapping in a subprocess to avoid leaking any state that happens` → import:import_subprocess
  - L24 `return subprocess.run(cmd, check=True).returncode` → import:import_subprocess

**源码**：

```python
def _run_pip(args, additional_paths=None):
    # Run the bootstrapping in a subprocess to avoid leaking any state that happens
    # after pip has executed. Particularly, this avoids the case when pip holds onto
    # the files in *additional_paths*, preventing us to remove them at the end of the
    # invocation.
    code = f"""
import runpy
import sys
sys.path = {additional_paths or []} + sys.path
sys.argv[1:] = {args}
runpy.run_module("pip", run_name="__main__", alter_sys=True)
"""

    cmd = [
        sys.executable,
        '-W',
        'ignore::DeprecationWarning',
        '-c',
        code,
    ]
    if sys.flags.isolated:
        # run code in isolated mode if currently running isolated
        cmd.insert(1, '-I')
    return subprocess.run(cmd, check=True).returncode
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #49 · confluence · `_url_collapse_path`

- **位置**：`http/server.py:922`（45 行）
- **层**：confluence ｜ 曲率汇合点 forman=-380
- **结构量**：Forman=-380 ｜ 池：（不在任何池内）
- **本函数调用**：`append`, `join`, `partition`, `pop`, `split`, `unquote`
- **同文件调用者**：`CGIHTTPRequestHandler.is_cgi`（跨文件调用者未扫描）

**源码**：

```python
def _url_collapse_path(path):
    """
    Given a URL path, remove extra '/'s and '.' path elements and collapse
    any '..' references and returns a collapsed path.

    Implements something akin to RFC-2396 5.2 step 6 to parse relative paths.
    The utility of this function is limited to is_cgi method and helps
    preventing some security attacks.

    Returns: The reconstituted URL, which will always start with a '/'.

    Raises: IndexError if too many '..' occur within the path.

    """
    # Query component should not be involved.
    path, _, query = path.partition('?')
    path = urllib.parse.unquote(path)

    # Similar to os.path.split(os.path.normpath(path)) but specific to URL
    # path semantics rather than local operating system semantics.
    path_parts = path.split('/')
    head_parts = []
    for part in path_parts[:-1]:
        if part == '..':
            head_parts.pop() # IndexError if more '..' than prior parts
        elif part and part != '.':
            head_parts.append( part )
    if path_parts:
        tail_part = path_parts.pop()
        if tail_part:
            if tail_part == '..':
                head_parts.pop()
                tail_part = ''
            elif tail_part == '.':
                tail_part = ''
    else:
        tail_part = ''

    if query:
        tail_part = '?'.join((tail_part, query))

    splitpath = ('/' + '/'.join(head_parts), tail_part)
    collapsed_path = "/".join(splitpath)

    return collapsed_path
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #50 · confluence · `_install`

- **位置**：`importlib/_bootstrap.py:1546`（6 行）
- **层**：confluence ｜ 曲率汇合点 forman=-377
- **结构量**：Forman=-377 ｜ 池：（不在任何池内）
- **本函数调用**：`_setup`, `append`
- **同文件调用者**：`_install_external_importers`（跨文件调用者未扫描）

**源码**：

```python
def _install(sys_module, _imp_module):
    """Install importers for builtin and frozen modules"""
    _setup(sys_module, _imp_module)

    sys.meta_path.append(BuiltinImporter)
    sys.meta_path.append(FrozenImporter)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #51 · anchor · `_compile_bytecode`

- **位置**：`importlib/_bootstrap_external.py:779`（11 行）
- **层**：anchor ｜ 锚点命中 sink:marshal
- **结构量**：Forman=-19 ｜ 池：p_anchor_breadth
- **本函数调用**：`ImportError`, `_fix_co_filename`, `_verbose_message`, `isinstance`, `loads`
- **同文件调用者**：`SourceLoader.get_code`, `SourcelessFileLoader.get_code`（跨文件调用者未扫描）
- **锚点命中行**：
  - L3 `code = marshal.loads(data)` → sink:marshal

**源码**：

```python
def _compile_bytecode(data, name=None, bytecode_path=None, source_path=None):
    """Compile bytecode as found in a pyc."""
    code = marshal.loads(data)
    if isinstance(code, _code_type):
        _bootstrap._verbose_message('code object from {!r}', bytecode_path)
        if source_path is not None:
            _imp._fix_co_filename(code, source_path)
        return code
    else:
        raise ImportError(f'Non-code object in {bytecode_path!r}',
                          name=name, path=bytecode_path)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #52 · random · `FileLoader.get_data`

- **位置**：`importlib/_bootstrap_external.py:1211`（8 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`SourceLoader.get_source`, `SourceLoader.get_code`, `SourcelessFileLoader.get_code`（跨文件调用者未扫描）

**源码**：

```python
    def get_data(self, path):
        """Return the data from path as raw bytes."""
        if isinstance(self, (SourceLoader, SourcelessFileLoader, ExtensionFileLoader)):
            with _io.open_code(str(path)) as file:
                return file.read()
        else:
            with _io.FileIO(path, 'r') as file:
                return file.read()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #53 · confluence · `_strip_spaces`

- **位置**：`logging/config.py:108`（2 行）
- **层**：confluence ｜ 曲率汇合点 forman=-227
- **结构量**：Forman=-227 ｜ 池：（不在任何池内）
- **本函数调用**：`map`
- **同文件调用者**：`_create_formatters`, `_install_handlers`, `_install_loggers`（跨文件调用者未扫描）

**源码**：

```python
def _strip_spaces(alist):
    return map(str.strip, alist)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #54 · anchor · `SocketHandler.makePickle`

- **位置**：`logging/handlers.py:649`（21 行）
- **层**：anchor ｜ 锚点命中 import:import_pickle
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`SocketHandler.emit`（跨文件调用者未扫描）
- **锚点命中行**：
  - L19 `s = pickle.dumps(d, 1)` → import:import_pickle

**源码**：

```python
    def makePickle(self, record):
        """
        Pickles the record in binary format with a length prefix, and
        returns it ready for transmission across the socket.
        """
        ei = record.exc_info
        if ei:
            # just to get traceback text into record.exc_text ...
            dummy = self.format(record)
        # See issue #14436: If msg or args are objects, they may not be
        # available on the receiving end. So we convert the msg % args
        # to a string, save it as msg and zap the args.
        d = dict(record.__dict__)
        d['msg'] = record.getMessage()
        d['args'] = None
        d['exc_info'] = None
        # Issue #25685: delete 'message' if present: redundant with 'msg'
        d.pop('message', None)
        s = pickle.dumps(d, 1)
        slen = struct.pack(">L", len(s))
        return slen + s
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #55 · random · `QueueListener.enqueue_sentinel`

- **位置**：`logging/handlers.py:1608`（9 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`QueueListener.stop`（跨文件调用者未扫描）

**源码**：

```python
    def enqueue_sentinel(self):
        """
        This is used to enqueue the sentinel record.

        The base implementation uses put_nowait. You may want to override this
        method if you want to use timeouts or work with custom queue
        implementations.
        """
        self.queue.put_nowait(self._sentinel)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #56 · random · `Logger.getChild`

- **位置**：`logging/__init__.py:1784`（18 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def getChild(self, suffix):
        """
        Get a logger which is a descendant to this one.

        This is a convenience method, such that

        logging.getLogger('abc').getChild('def.ghi')

        is the same as

        logging.getLogger('abc.def.ghi')

        It's useful, for example, when the parent logger is named using
        __name__ rather than a literal string.
        """
        if self.root is not self:
            suffix = '.'.join((self.name, suffix))
        return self.manager.getLogger(suffix)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #57 · random · `_ConnectionBase.__exit__`

- **位置**：`multiprocessing/connection.py:267`（2 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Listener.__exit__`（跨文件调用者未扫描）

**源码**：

```python
    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #58 · anchor · `XmlListener.accept`

- **位置**：`multiprocessing/connection.py:1019`（5 行）
- **层**：anchor ｜ 锚点命中 import:import_xmlrpclib
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`Listener.accept`, `SocketListener.accept`, `PipeListener.accept`（跨文件调用者未扫描）
- **锚点命中行**：
  - L3 `import xmlrpc.client as xmlrpclib` → import:import_xmlrpclib

**源码**：

```python
    def accept(self):
        global xmlrpclib
        import xmlrpc.client as xmlrpclib
        obj = Listener.accept(self)
        return ConnectionWrapper(obj, _xml_dumps, _xml_loads)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #59 · zero_cover · `BarrierProxy.abort`

- **位置**：`multiprocessing/managers.py:1116`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def abort(self):
        return self._callmethod('abort')
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #60 · anchor · `get_preparation_data`

- **位置**：`multiprocessing/spawn.py:160`（45 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=-370 ｜ 池：p_anchor_breadth
- **本函数调用**：`_check_not_importing_main`, `copy`, `current_process`, `dict`, `getEffectiveLevel`, `get_start_method`, `getattr`, `getcwd`, `index`, `isabs`, `join`, `normpath`
- **锚点命中行**：
  - L31 `# Figure out whether to initialise main in the subprocess as a module` → import:import_subprocess

**源码**：

```python
def get_preparation_data(name):
    '''
    Return info about parent needed by child to unpickle process object
    '''
    _check_not_importing_main()
    d = dict(
        log_to_stderr=util._log_to_stderr,
        authkey=process.current_process().authkey,
        )

    if util._logger is not None:
        d['log_level'] = util._logger.getEffectiveLevel()

    sys_path=sys.path.copy()
    try:
        i = sys_path.index('')
    except ValueError:
        pass
    else:
        sys_path[i] = process.ORIGINAL_DIR

    d.update(
        name=name,
        sys_path=sys_path,
        sys_argv=sys.argv,
        orig_dir=process.ORIGINAL_DIR,
        dir=os.getcwd(),
        start_method=get_start_method(allow_none=True),
        )

    # Figure out whether to initialise main in the subprocess as a module
    # or through direct execution (or to leave it alone entirely)
    main_module = sys.modules['__main__']
    main_mod_name = getattr(main_module.__spec__, "name", None)
    if main_mod_name is not None:
        d['init_main_from_name'] = main_mod_name
    elif sys.platform != 'win32' or (not WINEXE and not WINSERVICE):
        main_path = getattr(main_module, '__file__', None)
        if main_path is not None:
            if (not os.path.isabs(main_path) and
                        process.ORIGINAL_DIR is not None):
                main_path = os.path.join(process.ORIGINAL_DIR, main_path)
            d['init_main_from_path'] = os.path.normpath(main_path)

    return d
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #61 · random · `Condition._make_methods`

- **位置**：`multiprocessing/synchronize.py:242`（3 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`SemLock.__init__`, `SemLock._make_methods`, `SemLock.__setstate__`, `Condition.__init__`, `Condition.__setstate__`（跨文件调用者未扫描）

**源码**：

```python
    def _make_methods(self):
        self.acquire = self._lock.acquire
        self.release = self._lock.release
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #62 · anchor · `InprocessBuildEnvironmentInstaller.install`

- **位置**：`site-packages/pip/_internal/build_env.py:320`（51 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`BuildEnvironmentInstaller.install`, `SubprocessBuildEnvironmentInstaller.install`, `BuildEnvironment.install_requirements`（跨文件调用者未扫描）
- **锚点命中行**：
  - L27 `# Format similar to a nested subprocess error, where the` → import:import_subprocess

**源码**：

```python
    def install(
        self,
        requirements: Iterable[str],
        prefix: _Prefix,
        *,
        kind: str,
        for_req: InstallRequirement | None,
    ) -> None:
        """Install entrypoint. Manages output capturing and error handling."""
        capture_logs = not logger.isEnabledFor(VERBOSE) and self._level == 0
        if capture_logs:
            # Hide the logs from the installation of build dependencies.
            # They will be shown only if an error occurs.
            capture_ctx: ContextManager[StringIO] = capture_logging()
            spinner: ContextManager[None] = open_rich_spinner(f"Installing {kind}")
        else:
            # Otherwise, pass-through all logs (with a header).
            capture_ctx, spinner = nullcontext(StringIO()), nullcontext()
            logger.info("Installing %s ...", kind)

        try:
            self._level += 1
            with spinner, capture_ctx as stream:
                self._install_impl(requirements, prefix)

        except DiagnosticPipError as exc:
            # Format similar to a nested subprocess error, where the
            # causing error is shown first, followed by the build error.
            logger.info(textwrap.dedent(stream.getvalue()))
            logger.error("%s", exc, extra={"rich": True})
            logger.info("")
            raise BuildDependencyInstallError(
                for_req, requirements, cause=exc, log_lines=None
            )

        except Exception as exc:
            logs: list[str] | None = textwrap.dedent(stream.getvalue()).splitlines()
            if not capture_logs:
                # If logs aren't being captured, then display the error inline
                # with the rest of the logs.
                logs = None
                if isinstance(exc, PipError):
                    logger.error("%s", exc)
                else:
                    logger.exception("pip crashed unexpectedly")
            raise BuildDependencyInstallError(
                for_req, requirements, cause=exc, log_lines=logs
            )

        finally:
            self._level -= 1
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #63 · random · `editable`

- **位置**：`site-packages/pip/_internal/cli/cmdoptions.py:575`（13 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **本函数调用**：`Option`

**源码**：

```python
def editable() -> Option:
    return Option(
        "-e",
        "--editable",
        dest="editables",
        action="append",
        default=[],
        metavar="path/url",
        help=(
            "Install a project in editable mode (i.e. setuptools "
            '"develop mode") from a local project path or a VCS url.'
        ),
    )
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #64 · zero_cover · `LinkEvaluator.get_version_sort_key`

- **位置**：`site-packages/pip/_internal/index/package_finder.py:283`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`LinkEvaluator.evaluate_link`（跨文件调用者未扫描）

**源码**：

```python
                def get_version_sort_key(v: str) -> tuple[int, ...]:
                    return tuple(int(s) for s in v.split(".") if s.isdigit())
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #65 · zero_cover · `Link.path`

- **位置**：`site-packages/pip/_internal/models/link.py:455`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_clean_file_url_path`, `_clean_url_path`, `_ensure_quoted_url`, `Link.file_path`（跨文件调用者未扫描）

**源码**：

```python
    def path(self) -> str:
        return self._path
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #66 · confluence · `build_wheel_pep517`

- **位置**：`site-packages/pip/_internal/operations/build/wheel.py:13`（26 行）
- **层**：confluence ｜ 曲率汇合点 forman=-371
- **结构量**：Forman=-371 ｜ 池：（不在任何池内）
- **本函数调用**：`build_wheel`, `debug`, `error`, `join`, `runner_with_spinner_message`, `subprocess_runner`

**源码**：

```python
def build_wheel_pep517(
    name: str,
    backend: BuildBackendHookCaller,
    metadata_directory: str,
    wheel_directory: str,
) -> str | None:
    """Build one InstallRequirement using the PEP 517 build process.

    Returns path to wheel if successfully built. Otherwise, returns None.
    """
    assert metadata_directory is not None
    try:
        logger.debug("Destination directory: %s", wheel_directory)

        runner = runner_with_spinner_message(
            f"Building wheel for {name} (pyproject.toml)"
        )
        with backend.subprocess_runner(runner):
            wheel_name = backend.build_wheel(
                wheel_directory=wheel_directory,
                metadata_directory=metadata_directory,
            )
    except Exception:
        logger.error("Failed building wheel for %s", name)
        return None
    return os.path.join(wheel_directory, wheel_name)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #67 · confluence · `parse_editable`

- **位置**：`site-packages/pip/_internal/req/constructors.py:148`（32 行）
- **层**：confluence ｜ 曲率汇合点 forman=-366
- **结构量**：Forman=-366 ｜ 池：（不在任何池内）
- **本函数调用**：`InstallationError`, `Link`, `_parse_direct_url_editable`, `_parse_pip_syntax_editable`, `join`, `startswith`
- **同文件调用者**：`parse_req_from_editable`（跨文件调用者未扫描）

**源码**：

```python
def parse_editable(editable_req: str) -> tuple[str | None, str, set[str]]:
    """Parses an editable requirement into:
        - a requirement name with environment markers
        - an URL
        - extras
    Accepted requirements:
        - svn+http://blahblah@rev#egg=Foobar[baz]&subdirectory=version_subdir
        - local_path[some_extra]
        - Foobar[extra] @ svn+http://blahblah@rev#subdirectory=subdir ; markers
    """
    try:
        package_name, url, extras = _parse_direct_url_editable(editable_req)
    except ValueError:
        package_name, url, extras = _parse_pip_syntax_editable(editable_req)

    link = Link(url)

    if not link.is_vcs and not link.url.startswith("file:"):
        backends = ", ".join(vcs.all_schemes)
        raise InstallationError(
            f"{editable_req} is not a valid editable requirement. "
            f"It should either be a path to a local project or a VCS URL "
            f"(beginning with {backends})."
        )

    # The project name can be inferred from local file URIs easily.
    if not package_name and not link.url.startswith("file:"):
        raise InstallationError(
            f"Could not detect requirement name for '{editable_req}', "
            "please specify one with your_package_name @ URL"
        )
    return package_name, url, extras
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #68 · random · `deduce_helpful_msg`

- **位置**：`site-packages/pip/_internal/req/constructors.py:210`（23 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-45 ｜ 池：（不在任何池内）
- **本函数调用**：`check_first_requirement_in_file`, `debug`, `exists`
- **同文件调用者**：`parse_req_from_line`, `_parse_req_string`（跨文件调用者未扫描）

**源码**：

```python
def deduce_helpful_msg(req: str) -> str:
    """Returns helpful msg in case requirements file does not exist,
    or cannot be parsed.

    :params req: Requirements file path
    """
    if not os.path.exists(req):
        return f" File '{req}' does not exist."
    msg = " The path does exist. "
    # Try to parse and check if it is a requirements file.
    try:
        check_first_requirement_in_file(req)
    except InvalidRequirement:
        logger.debug("Cannot parse '%s' as requirements file", req)
    else:
        msg += (
            f"The argument you provided "
            f"({req}) appears to be a"
            f" requirements file. If that is the"
            f" case, use the '-r' flag to install"
            f" the packages specified within it."
        )
    return msg
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #69 · confluence · `handle_requirement_line`

- **位置**：`site-packages/pip/_internal/req/req_file.py:175`（32 行）
- **层**：confluence ｜ 曲率汇合点 forman=-144
- **结构量**：Forman=-144 ｜ 池：（不在任何池内）
- **本函数调用**：`ParsedRequirement`, `format`
- **同文件调用者**：`handle_line`（跨文件调用者未扫描）

**源码**：

```python
def handle_requirement_line(
    line: ParsedLine,
    options: optparse.Values | None = None,
) -> ParsedRequirement:
    # preserve for the nested code path
    line_comes_from = "{} {} (line {})".format(
        "-c" if line.constraint else "-r",
        line.filename,
        line.lineno,
    )

    assert line.requirement is not None

    # get the options that apply to requirements
    if line.is_editable:
        supported_dest = SUPPORTED_OPTIONS_EDITABLE_REQ_DEST
    else:
        supported_dest = SUPPORTED_OPTIONS_REQ_DEST
    req_options = {}
    for dest in supported_dest:
        if dest in line.opts.__dict__ and line.opts.__dict__[dest]:
            req_options[dest] = line.opts.__dict__[dest]

    line_source = f"line {line.lineno} of {line.filename}"
    return ParsedRequirement(
        requirement=line.requirement,
        is_editable=line.is_editable,
        comes_from=line_comes_from,
        constraint=line.constraint,
        options=req_options,
        line_source=line_source,
    )
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #70 · random · `glibc_version_string`

- **位置**：`site-packages/pip/_internal/utils/glibc.py:7`（3 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-1 ｜ 池：（不在任何池内）
- **本函数调用**：`glibc_version_string_confstr`, `glibc_version_string_ctypes`
- **同文件调用者**：`libc_ver`（跨文件调用者未扫描）

**源码**：

```python
def glibc_version_string() -> str | None:
    "Returns glibc version string, or None if not using glibc."
    return glibc_version_string_confstr() or glibc_version_string_ctypes()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #71 · confluence · `is_installable_dir`

- **位置**：`site-packages/pip/_internal/utils/misc.py:287`（15 行）
- **层**：confluence ｜ 曲率汇合点 forman=-366
- **结构量**：Forman=-366 ｜ 池：（不在任何池内）
- **本函数调用**：`isdir`, `isfile`, `join`

**源码**：

```python
def is_installable_dir(path: str) -> bool:
    """Is path is a directory containing pyproject.toml or setup.py?

    If pyproject.toml exists, this is a PEP 517 project. Otherwise we look for
    a legacy setuptools layout by identifying setup.py. We don't check for the
    setup.cfg because using it without setup.py is only available for PEP 517
    projects, which are already covered by the pyproject.toml check.
    """
    if not os.path.isdir(path):
        return False
    if os.path.isfile(os.path.join(path, "pyproject.toml")):
        return True
    if os.path.isfile(os.path.join(path, "setup.py")):
        return True
    return False
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #72 · random · `TempDirectoryTypeRegistry.set_delete`

- **位置**：`site-packages/pip/_internal/utils/temp_dir.py:54`（5 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=0 ｜ 池：（不在任何池内）

**源码**：

```python
    def set_delete(self, kind: str, value: bool) -> None:
        """Indicate whether a TempDirectory of the given kind should be
        auto-deleted.
        """
        self._should_delete[kind] = value
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #73 · random · `Serializer.dumps`

- **位置**：`site-packages/pip/_vendor/cachecontrol/serialize.py:20`（41 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Serializer.serialize`（跨文件调用者未扫描）

**源码**：

```python
    def dumps(
        self,
        request: PreparedRequest,
        response: HTTPResponse,
        body: bytes | None = None,
    ) -> bytes:
        response_headers: CaseInsensitiveDict[str] = CaseInsensitiveDict(
            response.headers
        )

        if body is None:
            # When a body isn't passed in, we'll read the response. We
            # also update the response with a new file handler to be
            # sure it acts as though it was never read.
            body = response.read(decode_content=False)
            response._fp = io.BytesIO(body)  # type: ignore[assignment]
            response.length_remaining = len(body)

        data = {
            "response": {
                "body": body,  # Empty bytestring if body is stored separately
                "headers": {str(k): str(v) for k, v in response.headers.items()},
                "status": response.status,
                "version": response.version,
                "reason": str(response.reason),
                "decode_content": response.decode_content,
            }
        }

        # Construct our vary headers
        data["vary"] = {}
        if "vary" in response_headers:
            varied_headers = response_headers["vary"].split(",")
            for header in varied_headers:
                header = str(header).strip()
                header_value = request.headers.get(header, None)
                if header_value is not None:
                    header_value = str(header_value)
                data["vary"][header] = header_value

        return b",".join([f"cc={self.serde_version}".encode(), self.serialize(data)])
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #74 · random · `proceed`

- **位置**：`site-packages/pip/_vendor/distlib/util.py:322`（14 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-100 ｜ 池：（不在任何池内）
- **本函数调用**：`lower`, `raw_input`

**源码**：

```python
def proceed(prompt, allowed_chars, error_prompt=None, default=None):
    p = prompt
    while True:
        s = raw_input(p)
        p = prompt
        if not s and default:
            s = default
        if s:
            c = s[0].lower()
            if c in allowed_chars:
                break
            if error_prompt:
                p = '%c: %s\n%s' % (c, error_prompt, prompt)
    return c
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #75 · anchor · `LinuxDistribution._lsb_release_info`

- **位置**：`site-packages/pip/_vendor/distro/distro.py:1154`（17 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L12 `stdout = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)` → import:import_subprocess
  - L14 `except (OSError, subprocess.CalledProcessError):` → import:import_subprocess

**源码**：

```python
    def _lsb_release_info(self) -> Dict[str, str]:
        """
        Get the information items from the lsb_release command output.

        Returns:
            A dictionary containing all information items.
        """
        if not self.include_lsb:
            return {}
        try:
            cmd = ("lsb_release", "-a")
            stdout = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        # Command not found or lsb_release returned error
        except (OSError, subprocess.CalledProcessError):
            return {}
        content = self._to_str(stdout).splitlines()
        return self._parse_lsb_release_content(content)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #76 · anchor · `LinuxDistribution._oslevel_info`

- **位置**：`site-packages/pip/_vendor/distro/distro.py:1209`（8 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L5 `stdout = subprocess.check_output("oslevel", stderr=subprocess.DEVNULL)` → import:import_subprocess
  - L6 `except (OSError, subprocess.CalledProcessError):` → import:import_subprocess

**源码**：

```python
    def _oslevel_info(self) -> str:
        if not self.include_oslevel:
            return ""
        try:
            stdout = subprocess.check_output("oslevel", stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            return ""
        return self._to_str(stdout).strip()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #77 · confluence · `check_bidi`

- **位置**：`site-packages/pip/_vendor/idna/core.py:70`（68 行）
- **层**：confluence ｜ 曲率汇合点 forman=-146
- **结构量**：Forman=-146 ｜ 池：（不在任何池内）
- **本函数调用**：`IDNABidiError`, `bidirectional`, `enumerate`, `format`, `repr`
- **同文件调用者**：`check_label`（跨文件调用者未扫描）

**源码**：

```python
def check_bidi(label: str, check_ltr: bool = False) -> bool:
    # Bidi rules should only be applied if string contains RTL characters
    bidi_label = False
    for idx, cp in enumerate(label, 1):
        direction = unicodedata.bidirectional(cp)
        if direction == "":
            # String likely comes from a newer version of Unicode
            raise IDNABidiError("Unknown directionality in label {} at position {}".format(repr(label), idx))
        if direction in ["R", "AL", "AN"]:
            bidi_label = True
    if not bidi_label and not check_ltr:
        return True

    # Bidi rule 1
    direction = unicodedata.bidirectional(label[0])
    if direction in ["R", "AL"]:
        rtl = True
    elif direction == "L":
        rtl = False
    else:
        raise IDNABidiError("First codepoint in label {} must be directionality L, R or AL".format(repr(label)))

    valid_ending = False
    number_type: Optional[str] = None
    for idx, cp in enumerate(label, 1):
        direction = unicodedata.bidirectional(cp)

        if rtl:
            # Bidi rule 2
            if direction not in [
                "R",
                "AL",
                "AN",
                "EN",
                "ES",
                "CS",
                "ET",
                "ON",
                "BN",
                "NSM",
            ]:
                raise IDNABidiError("Invalid direction for codepoint at position {} in a right-to-left label".format(idx))
            # Bidi rule 3
            if direction in ["R", "AL", "EN", "AN"]:
                valid_ending = True
            elif direction != "NSM":
                valid_ending = False
            # Bidi rule 4
            if direction in ["AN", "EN"]:
                if not number_type:
                    number_type = direction
                else:
                    if number_type != direction:
                        raise IDNABidiError("Can not mix numeral types in a right-to-left label")
        else:
            # Bidi rule 5
            if direction not in ["L", "EN", "ES", "CS", "ET", "ON", "BN", "NSM"]:
                raise IDNABidiError("Invalid direction for codepoint at position {} in a left-to-right label".format(idx))
            # Bidi rule 6
            if direction in ["L", "EN"]:
```

> 已截断（共 68 行），完整见 `site-packages/pip/_vendor/idna/core.py:70`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #78 · zero_cover · `is_valid_pylock_path`

- **位置**：`site-packages/pip/_vendor/packaging/pylock.py:73`（3 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=-80 ｜ 池：（不在任何池内）
- **本函数调用**：`bool`, `match`

**源码**：

```python
def is_valid_pylock_path(path: Path) -> bool:
    """Check if the given path is a valid pylock file path."""
    return path.name == "pylock.toml" or bool(_PYLOCK_FILE_NAME_RE.match(path.name))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #79 · random · `_UpperBound.__lt__`

- **位置**：`site-packages/pip/_vendor/packaging/specifiers.py:213`（12 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_BoundaryVersion.__lt__`, `_LowerBound.__lt__`（跨文件调用者未扫描）

**源码**：

```python
    def __lt__(self, other: _UpperBound) -> bool:
        if not isinstance(other, _UpperBound):  # pragma: no cover
            return NotImplemented
        # Nothing < +inf (except +inf itself).
        if self.version is None:
            return False
        if other.version is None:
            return True
        if self.version != other.version:
            return self.version < other.version
        # v) < v]: exclusive ends earlier.
        return not self.inclusive and other.inclusive
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #80 · zero_cover · `Specifier._require_spec_version`

- **位置**：`site-packages/pip/_vendor/packaging/specifiers.py:623`（9 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Specifier._wildcard_ranges`, `Specifier._standard_ranges`, `Specifier._canonical_spec`, `Specifier._compare_equal`, `Specifier._compare_less_than_equal`, `Specifier._compare_greater_than_equal`, `Specifier._compare_less_than`, `Specifier._compare_greater_than`（跨文件调用者未扫描）

**源码**：

```python
    def _require_spec_version(self, version: str) -> Version:
        """Get spec version, asserting it's valid (not for === operator).

        This method should only be called for operators where version
        strings are guaranteed to be valid PEP 440 versions (not ===).
        """
        spec_version = self._get_spec_version(version)
        assert spec_version is not None
        return spec_version
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #81 · zero_cover · `Distribution._dep_map`

- **位置**：`site-packages/pip/_vendor/pkg_resources/__init__.py:3029`（10 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Distribution._build_dep_map`, `DistInfoDistribution._dep_map`（跨文件调用者未扫描）

**源码**：

```python
    def _dep_map(self):
        """
        A map of extra to its list of (direct) requirements
        for this distribution, including the null extra.
        """
        try:
            return self.__dep_map
        except AttributeError:
            self.__dep_map = self._filter_extras(self._build_dep_map())
        return self.__dep_map
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #82 · confluence · `get_win_folder_from_env_vars`

- **位置**：`site-packages/pip/_vendor/platformdirs/windows.py:143`（19 行）
- **层**：confluence ｜ 曲率汇合点 forman=-216
- **结构量**：Forman=-216 ｜ 池：（不在任何池内）
- **本函数调用**：`ValueError`, `get`, `get_win_folder_if_csidl_name_not_env_var`

**源码**：

```python
def get_win_folder_from_env_vars(csidl_name: str) -> str:
    """Get folder from environment variables."""
    result = get_win_folder_if_csidl_name_not_env_var(csidl_name)
    if result is not None:
        return result

    env_var_name = {
        "CSIDL_APPDATA": "APPDATA",
        "CSIDL_COMMON_APPDATA": "ALLUSERSPROFILE",
        "CSIDL_LOCAL_APPDATA": "LOCALAPPDATA",
    }.get(csidl_name)
    if env_var_name is None:
        msg = f"Unknown CSIDL name: {csidl_name}"
        raise ValueError(msg)
    result = os.environ.get(env_var_name)
    if result is None:
        msg = f"Unset environment variable: {env_var_name}"
        raise ValueError(msg)
    return result
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #83 · confluence · `guess_lexer`

- **位置**：`site-packages/pip/_vendor/pygments/lexers/__init__.py:304`（37 行）
- **层**：confluence ｜ 曲率汇合点 forman=-222
- **结构量**：Forman=-222 ｜ 池：（不在任何池内）
- **本函数调用**：`ClassNotFound`, `_iter_lexerclasses`, `analyse_text`, `decode`, `get`, `get_filetype_from_buffer`, `get_lexer_by_name`, `guess_decode`, `isinstance`, `lexer`
- **同文件调用者**：`guess_lexer_for_filename`（跨文件调用者未扫描）

**源码**：

```python
def guess_lexer(_text, **options):
    """
    Return a `Lexer` subclass instance that's guessed from the text in
    `text`. For that, the :meth:`.analyse_text()` method of every known lexer
    class is called with the text as argument, and the lexer which returned the
    highest value will be instantiated and returned.

    :exc:`pygments.util.ClassNotFound` is raised if no lexer thinks it can
    handle the content.
    """

    if not isinstance(_text, str):
        inencoding = options.get('inencoding', options.get('encoding'))
        if inencoding:
            _text = _text.decode(inencoding or 'utf8')
        else:
            _text, _ = guess_decode(_text)

    # try to get a vim modeline first
    ft = get_filetype_from_buffer(_text)

    if ft is not None:
        try:
            return get_lexer_by_name(ft, **options)
        except ClassNotFound:
            pass

    best_lexer = [0.0, None]
    for lexer in _iter_lexerclasses():
        rv = lexer.analyse_text(_text)
        if rv == 1.0:
            return lexer(**options)
        if rv > best_lexer[0]:
            best_lexer[:] = (rv, lexer)
    if not best_lexer[0] or best_lexer[1] is None:
        raise ClassNotFound('no lexer matching the text found')
    return best_lexer[1](**options)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #84 · confluence · `_combine_regex`

- **位置**：`site-packages/pip/_vendor/rich/highlighter.py:8`（7 行）
- **层**：confluence ｜ 曲率汇合点 forman=-362
- **结构量**：Forman=-362 ｜ 池：（不在任何池内）
- **本函数调用**：`join`

**源码**：

```python
def _combine_regex(*regexes: str) -> str:
    """Combine a number of regexes in to a single regex.

    Returns:
        str: New regex with all regexes ORed together.
    """
    return "|".join(regexes)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #85 · zero_cover · `SetConsoleCursorPosition`

- **位置**：`site-packages/pip/_vendor/rich/_win32_console.py:252`（13 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **本函数调用**：`_SetConsoleCursorPosition`, `bool`
- **同文件调用者**：`LegacyWindowsTerm.move_cursor_to`, `LegacyWindowsTerm.move_cursor_up`, `LegacyWindowsTerm.move_cursor_down`, `LegacyWindowsTerm.move_cursor_forward`, `LegacyWindowsTerm.move_cursor_to_column`, `LegacyWindowsTerm.move_cursor_backward`（跨文件调用者未扫描）

**源码**：

```python
def SetConsoleCursorPosition(
    std_handle: wintypes.HANDLE, coords: WindowsCoordinates
) -> bool:
    """Set the position of the cursor in the console screen

    Args:
        std_handle (wintypes.HANDLE): A handle to the console input buffer or the console screen buffer.
        coords (WindowsCoordinates): The coordinates to move the cursor to.

    Returns:
        bool: True if the function succeeds, otherwise False.
    """
    return bool(_SetConsoleCursorPosition(std_handle, coords))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #86 · zero_cover · `BaseHTTPConnection.connect`

- **位置**：`site-packages/pip/_vendor/urllib3/_base_connection.py:75`（1 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
        def connect(self) -> None: ...
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #87 · zero_cover · `BaseHTTPConnection.close`

- **位置**：`site-packages/pip/_vendor/urllib3/_base_connection.py:95`（1 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
        def close(self) -> None: ...
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #88 · zero_cover · `HTTPHeaderDictItemView.__contains__`

- **位置**：`site-packages/pip/_vendor/urllib3/_collections.py:196`（6 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`HTTPHeaderDict.__contains__`（跨文件调用者未扫描）

**源码**：

```python
    def __contains__(self, item: object) -> bool:
        if isinstance(item, tuple) and len(item) == 2:
            passed_key, passed_val = item
            if isinstance(passed_key, str) and isinstance(passed_val, str):
                return self._headers._has_value_for_header(passed_key, passed_val)
        return False
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #89 · zero_cover · `HTTP2Connection.set_tunnel`

- **位置**：`site-packages/pip/_vendor/urllib3/http2/connection.py:215`（10 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def set_tunnel(
        self,
        host: str,
        port: int | None = None,
        headers: typing.Mapping[str, str] | None = None,
        scheme: str = "http",
    ) -> None:
        raise NotImplementedError(
            "HTTP/2 does not support setting up a tunnel through a proxy"
        )
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #90 · confluence · `create_connection`

- **位置**：`site-packages/pip/_vendor/urllib3/util/connection.py:27`（64 行）
- **层**：confluence ｜ 曲率汇合点 forman=-219
- **结构量**：Forman=-219 ｜ 池：（不在任何池内）
- **本函数调用**：`LocationParseError`, `OSError`, `_set_socket_options`, `allowed_gai_family`, `bind`, `close`, `connect`, `encode`, `getaddrinfo`, `settimeout`, `socket`, `startswith`

**源码**：

```python
def create_connection(
    address: tuple[str, int],
    timeout: _TYPE_TIMEOUT = _DEFAULT_TIMEOUT,
    source_address: tuple[str, int] | None = None,
    socket_options: _TYPE_SOCKET_OPTIONS | None = None,
) -> socket.socket:
    """Connect to *address* and return the socket object.

    Convenience function.  Connect to *address* (a 2-tuple ``(host,
    port)``) and return the socket object.  Passing the optional
    *timeout* parameter will set the timeout on the socket instance
    before attempting to connect.  If no *timeout* is supplied, the
    global default timeout setting returned by :func:`socket.getdefaulttimeout`
    is used.  If *source_address* is set it must be a tuple of (host, port)
    for the socket to bind as a source address before making the connection.
    An host of '' or port 0 tells the OS to use the default.
    """

    host, port = address
    if host.startswith("["):
        host = host.strip("[]")
    err = None

    # Using the value from allowed_gai_family() in the context of getaddrinfo lets
    # us select whether to work with IPv4 DNS records, IPv6 records, or both.
    # The original create_connection function always returns all records.
    family = allowed_gai_family()

    try:
        host.encode("idna")
    except UnicodeError:
        raise LocationParseError(f"'{host}', label empty or too long") from None

    for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket.socket(af, socktype, proto)

            # If provided, set socket level options before connecting.
            _set_socket_options(sock, socket_options)

            if timeout is not _DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sa)
            # Break explicitly a reference cycle
            err = None
            return sock

        except OSError as _:
            err = _
            if sock is not None:
                sock.close()

    if err is not None:
        try:
            raise err
        finally:
```

> 已截断（共 64 行），完整见 `site-packages/pip/_vendor/urllib3/util/connection.py:27`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #91 · zero_cover · `make_safe_parse_float`

- **位置**：`tomllib/_parser.py:685`（19 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=-12 ｜ 池：（不在任何池内）
- **本函数调用**：`ValueError`, `isinstance`, `parse_float`
- **同文件调用者**：`loads`（跨文件调用者未扫描）

**源码**：

```python
def make_safe_parse_float(parse_float: ParseFloat) -> ParseFloat:
    """A decorator to make `parse_float` safe.

    `parse_float` must not return dicts or lists, because these types
    would be mixed with parsed TOML tables and arrays, thus confusing
    the parser. The returned decorated callable raises `ValueError`
    instead of returning illegal types.
    """
    # The default `float` callable never returns illegal types. Optimize it.
    if parse_float is float:
        return float

    def safe_parse_float(float_str: str) -> Any:
        float_value = parse_float(float_str)
        if isinstance(float_value, (dict, list)):
            raise ValueError("parse_float must not return dicts or lists")
        return float_value

    return safe_parse_float
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #92 · anchor · `DOMBuilder.parse`

- **位置**：`xml/dom/xmlbuilder.py:187`（9 行）
- **层**：anchor ｜ 锚点命中 sink:urllib_urlopen
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`DOMBuilder.parseURI`, `DOMEntityResolver.resolveEntity`（跨文件调用者未扫描）
- **锚点命中行**：
  - L8 `fp = urllib.request.urlopen(input.systemId)` → sink:urllib_urlopen

**源码**：

```python
    def parse(self, input):
        options = copy.copy(self._options)
        options.filter = self.filter
        options.errorHandler = self.errorHandler
        fp = input.byteStream
        if fp is None and input.systemId:
            import urllib.request
            fp = urllib.request.urlopen(input.systemId)
        return self._parse_bytestream(fp, options)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #93 · random · `findall`

- **位置**：`xml/etree/ElementPath.py:410`（2 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-149 ｜ 池：（不在任何池内）
- **本函数调用**：`iterfind`, `list`
- **同文件调用者**：`xpath_tokenizer`, `prepare_predicate`, `select`, `select`（跨文件调用者未扫描）

**源码**：

```python
def findall(elem, path, namespaces=None):
    return list(iterfind(elem, path, namespaces))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #94 · random · `IncrementalParser.parse`

- **位置**：`xml/sax/xmlreader.py:115`（11 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`XMLReader.parse`（跨文件调用者未扫描）

**源码**：

```python
    def parse(self, source):
        from . import saxutils
        source = saxutils.prepare_input_source(source)

        self.prepareParser(source)
        file = source.getCharacterStream()
        if file is None:
            file = source.getByteStream()
        while buffer := file.read(self._bufsize):
            self.feed(buffer)
        self.close()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #95 · zero_cover · `ZipFile.read`

- **位置**：`zipfile/__init__.py:1618`（5 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_EndRecData64`, `_EndRecData`, `_SharedFile.read`, `ZipExtFile._init_decrypter`, `ZipExtFile.peek`, `ZipExtFile.read`, `ZipExtFile.read1`, `ZipExtFile._read1`（跨文件调用者未扫描）

**源码**：

```python
    def read(self, name, pwd=None):
        """Return file bytes for name. 'pwd' is the password to decrypt
        encrypted files."""
        with self.open(name, "r", pwd) as fp:
            return fp.read()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #96 · random · `ZoneInfo.dst`

- **位置**：`zoneinfo/_zoneinfo.py:112`（2 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`ZoneInfo._load_file`, `ZoneInfo._utcoff_to_dstoff`（跨文件调用者未扫描）

**源码**：

```python
    def dst(self, dt):
        return self._find_trans(dt).dstoff
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #97 · anchor · `ZoneInfo._file_reduce`

- **位置**：`zoneinfo/_zoneinfo.py:212`（6 行）
- **层**：anchor ｜ 锚点命中 import:import_pickle
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L2 `import pickle` → import:import_pickle
  - L4 `raise pickle.PicklingError(` → import:import_pickle
  - L5 `"Cannot pickle a ZoneInfo file created from a file stream."` → import:import_pickle

**源码**：

```python
    def _file_reduce(self):
        import pickle

        raise pickle.PicklingError(
            "Cannot pickle a ZoneInfo file created from a file stream."
        )
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #98 · zero_cover · `isearch_end.do`

- **位置**：`_pyrepl/historical_reader.py:205`（6 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`next_history.do`, `previous_history.do`, `history_search_backward.do`, `history_search_forward.do`, `restore_history.do`, `first_history.do`, `last_history.do`, `operate_and_get_next.do`（跨文件调用者未扫描）

**源码**：

```python
    def do(self) -> None:
        r = self.reader
        r.isearch_direction = ISEARCH_DIRECTION_NONE
        r.console.forgetinput()
        r.pop_input_trans()
        r.dirty = True
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #99 · anchor · `pipe_pager`

- **位置**：`_pyrepl/pager.py:127`（36 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=-148 ｜ 池：p_anchor_breadth
- **本函数调用**：`Popen`, `copy`, `escape_less`, `format`, `wait`, `write`
- **同文件调用者**：`get_pager`（跨文件调用者未扫描）
- **锚点命中行**：
  - L3 `import subprocess` → import:import_subprocess
  - L16 `proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,` → import:import_subprocess

**源码**：

```python
def pipe_pager(text: str, cmd: str, title: str = '') -> None:
    """Page through text by feeding it to another program."""
    import subprocess
    env = os.environ.copy()
    if title:
        title += ' '
    esc_title = escape_less(title)
    prompt_string = (
        f' {esc_title}' +
        '?ltline %lt?L/%L.'
        ':byte %bB?s/%s.'
        '.'
        '?e (END):?pB %pB\\%..'
        ' (press h for help or q to quit)')
    env['LESS'] = '-RmPm{0}$PM{0}$'.format(prompt_string)
    proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                            errors='backslashreplace', env=env)
    assert proc.stdin is not None
    try:
        with proc.stdin as pipe:
            try:
                pipe.write(text)
            except KeyboardInterrupt:
                # We've hereby abandoned whatever text hasn't been written,
                # but the pager is still in control of the terminal.
                pass
    except OSError:
        pass # Ignore broken pipes caused by quitting the pager program.
    while True:
        try:
            proc.wait()
            break
        except KeyboardInterrupt:
            # Ignore ctl-c like the pager itself does.  Otherwise the pager is
            # left running and the terminal is in raw mode and unusable.
            pass
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #100 · zero_cover · `Reader.update_cursor`

- **位置**：`_pyrepl/reader.py:567`（4 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Reader.do_cmd`（跨文件调用者未扫描）

**源码**：

```python
    def update_cursor(self) -> None:
        """Move the cursor to reflect changes in self.pos"""
        self.cxy = self.pos2xy()
        self.console.move_cursor(*self.cxy)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---
