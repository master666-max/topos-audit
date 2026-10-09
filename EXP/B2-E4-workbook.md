# E-B2-4 参照标准定向工作簿（100 单元）

> 靶仓：Python 3.13.12 **标准库**（已排除 site-packages，见 B2-E4-framecheck.json）
> 抽样框 13203 单元（全框 18198，含 site-packages 的混合版见 B2-E4-workbook-mixed.md）｜池 4 个｜零覆盖 97.6%
> **这份工作簿不是让你标真值**——人不是真值（Devign 4 专家 × 600 人时 × 两轮交叉，
> 复测正确率仅 24%）。它的作用是 **定向**（打破 Hui–Walter 镜像等价解）、
> **一致性量化**（双盲 → Krippendorff's α，作废规则=双阶段，见 PREREG/B2.md v1.5）、**误差棒**（Wilson + 分层 bootstrap）。
> 判不出来填 `None`——None 比猜一个 0/1 有价值得多。
> 分层分布：{'random': 30, 'confluence': 20, 'anchor': 25, 'zero_cover': 25}

---
## #1 · random · `_ActionsContainer._add_action`

- **位置**：`argparse.py:1529`（20 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_ActionsContainer.add_argument`, `_ActionsContainer._add_container_actions`, `_ArgumentGroup._add_action`, `_MutuallyExclusiveGroup._add_action`, `ArgumentParser.add_subparsers`, `ArgumentParser._add_action`（跨文件调用者未扫描）

**源码**：

```python
    def _add_action(self, action):
        # resolve any conflicts
        self._check_conflict(action)

        # add to actions list
        self._actions.append(action)
        action.container = self

        # index the action by any option strings it has
        for option_string in action.option_strings:
            self._option_string_actions[option_string] = action

        # set the flag if any option strings look like negative numbers
        for option_string in action.option_strings:
            if self._negative_number_matcher.match(option_string):
                if not self._has_negative_number_optionals:
                    self._has_negative_number_optionals.append(True)

        # return the created action
        return action
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #2 · random · `_Unparser.escape_char`

- **位置**：`ast.py:1209`（9 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_Unparser._str_literal_helper`（跨文件调用者未扫描）

**源码**：

```python
        def escape_char(c):
            # \n and \t are non-printable, but we only escape them if
            # escape_special_whitespace is True
            if not escape_special_whitespace and c in "\n\t":
                return c
            # Always escape backslashes and other non-printable characters
            if c == "\\" or not c.isprintable():
                return c.encode("unicode_escape").decode("ascii")
            return c
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

## #4 · random · `compile_file`

- **位置**：`compileall.py:132`（148 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-386 ｜ 池：p_big1
- **本函数调用**：`Path`, `ValueError`, `basename`, `cache_from_source`, `cmp`, `compile`, `decode`, `encode`, `enumerate`, `format`, `fspath`, `getdefaultencoding`
- **同文件调用者**：`compile_dir`, `main`（跨文件调用者未扫描）

**源码**：

```python
def compile_file(fullname, ddir=None, force=False, rx=None, quiet=0,
                 legacy=False, optimize=-1,
                 invalidation_mode=None, *, stripdir=None, prependdir=None,
                 limit_sl_dest=None, hardlink_dupes=False):
    """Byte-compile one file.

    Arguments (only fullname is required):

    fullname:  the file to byte-compile
    ddir:      if given, the directory name compiled in to the
               byte-code file.
    force:     if True, force compilation, even if timestamps are up-to-date
    quiet:     full output with False or 0, errors only with 1,
               no output with 2
    legacy:    if True, produce legacy pyc paths instead of PEP 3147 paths
    optimize:  int or list of optimization levels or -1 for level of
               the interpreter. Multiple levels leads to multiple compiled
               files each with one optimization level.
    invalidation_mode: how the up-to-dateness of the pyc will be checked
    stripdir:  part of path to left-strip from source file path
    prependdir: path to prepend to beginning of original file path, applied
               after stripdir
    limit_sl_dest: ignore symlinks if they are pointing outside of
                   the defined path.
    hardlink_dupes: hardlink duplicated pyc files
    """

    if ddir is not None and (stripdir is not None or prependdir is not None):
        raise ValueError(("Destination dir (ddir) cannot be used "
                          "in combination with stripdir or prependdir"))

    success = True
    fullname = os.fspath(fullname)
    stripdir = os.fspath(stripdir) if stripdir is not None else None
    name = os.path.basename(fullname)

    dfile = None

    if ddir is not None:
        dfile = os.path.join(ddir, name)

    if stripdir is not None:
        fullname_parts = fullname.split(os.path.sep)
        stripdir_parts = stripdir.split(os.path.sep)

        if stripdir_parts != fullname_parts[:len(stripdir_parts)]:
            if quiet < 2:
                print("The stripdir path {!r} is not a valid prefix for "
                      "source path {!r}; ignoring".format(stripdir, fullname))
        else:
            dfile = os.path.join(*fullname_parts[len(stripdir_parts):])

    if prependdir is not None:
        if dfile is None:
            dfile = os.path.join(prependdir, fullname)
        else:
            dfile = os.path.join(prependdir, dfile)

    if isinstance(optimize, int):
        optimize = [optimize]
```

> 已截断（共 148 行），完整见 `compileall.py:132`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #5 · confluence · `_update_func_cell_for__class__`

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

## #6 · anchor · `Enum.__new__`

- **位置**：`enum.py:1158`（60 行）
- **层**：anchor ｜ 锚点命中 import:import_pickle
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`EnumType.__new__`, `EnumType.__call__`, `EnumType._create_`, `StrEnum.__new__`, `Flag._missing_`（跨文件调用者未扫描）
- **锚点命中行**：
  - L4 `# __call__ (i.e. Color(3) ), and by pickle` → import:import_pickle

**源码**：

```python
    def __new__(cls, value):
        # all enum instances are actually created during class construction
        # without calling this method; this method is called by the metaclass'
        # __call__ (i.e. Color(3) ), and by pickle
        if type(value) is cls:
            # For lookups like Color(Color.RED)
            return value
        # by-value search for a matching enum member
        # see if it's in the reverse mapping (for hashable values)
        try:
            return cls._value2member_map_[value]
        except KeyError:
            # Not found, no need to do long O(n) search
            pass
        except TypeError:
            # not there, now do long search -- O(n) behavior
            for name, unhashable_values in cls._unhashable_values_map_.items():
                if value in unhashable_values:
                    return cls[name]
            for name, member in cls._member_map_.items():
                if value == member._value_:
                    return cls[name]
        # still not found -- verify that members exist, in-case somebody got here mistakenly
        # (such as via super when trying to override __new__)
        if not cls._member_map_:
            if getattr(cls, '_%s__in_progress' % cls.__name__, False):
                raise TypeError('do not use `super().__new__; call the appropriate __new__ directly') from None
            raise TypeError("%r has no members defined" % cls)
        #
        # still not found -- try _missing_ hook
        try:
            exc = None
            result = cls._missing_(value)
        except Exception as e:
            exc = e
            result = None
        try:
            if isinstance(result, cls):
                return result
            elif (
                    Flag is not None and issubclass(cls, Flag)
                    and cls._boundary_ is EJECT and isinstance(result, int)
                ):
                return result
            else:
                ve_exc = ValueError("%r is not a valid %s" % (value, cls.__qualname__))
                if result is None and exc is None:
                    raise ve_exc
                elif exc is None:
                    exc = TypeError(
                            'error in %s._missing_: returned %r instead of None or a valid member'
                            % (cls.__name__, result)
                            )
                if not isinstance(exc, ValueError):
                    exc.__context__ = ve_exc
                raise exc
        finally:
            # ensure all variables that could hold an exception are destroyed
            exc = None
            ve_exc = None
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #7 · random · `isstdin`

- **位置**：`fileinput.py:162`（8 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-20 ｜ 池：（不在任何池内）
- **本函数调用**：`RuntimeError`, `isstdin`
- **同文件调用者**：`FileInput.isstdin`（跨文件调用者未扫描）

**源码**：

```python
def isstdin():
    """
    Returns true if the last line was read from sys.stdin,
    otherwise returns false.
    """
    if not _state:
        raise RuntimeError("no active input()")
    return _state.isstdin()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #8 · random · `partial.__setstate__`

- **位置**：`functools.py:330`（23 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-39 ｜ 池：（不在任何池内）

**源码**：

```python
    def __setstate__(self, state):
        if not isinstance(state, tuple):
            raise TypeError("argument to __setstate__ must be a tuple")
        if len(state) != 4:
            raise TypeError(f"expected 4 items in state, got {len(state)}")
        func, args, kwds, namespace = state
        if (not callable(func) or not isinstance(args, tuple) or
           (kwds is not None and not isinstance(kwds, dict)) or
           (namespace is not None and not isinstance(namespace, dict))):
            raise TypeError("invalid partial state")

        args = tuple(args) # just in case it's a subclass
        if kwds is None:
            kwds = {}
        elif type(kwds) is not dict: # XXX does it need to be *exactly* dict?
            kwds = dict(kwds)
        if namespace is None:
            namespace = {}

        self.__dict__ = namespace
        self.func = func
        self.args = args
        self.keywords = kwds
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #9 · zero_cover · `is_related`

- **位置**：`functools.py:767`（4 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=-4 ｜ 池：（不在任何池内）
- **同文件调用者**：`_compose_mro`（跨文件调用者未扫描）

**源码**：

```python
    def is_related(typ):
        return (typ not in bases and hasattr(typ, '__mro__')
                                 and not isinstance(typ, GenericAlias)
                                 and issubclass(cls, typ))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #10 · confluence · `_Globber.compile`

- **位置**：`glob.py:394`（2 行）
- **层**：confluence ｜ 曲率汇合点 forman=-129
- **结构量**：Forman=-129 ｜ 池：（不在任何池内）
- **同文件调用者**：`_compile_pattern`, `_Globber.wildcard_selector`, `_Globber.recursive_selector`（跨文件调用者未扫描）

**源码**：

```python
    def compile(self, pat):
        return _compile_pattern(pat, self.sep, self.case_sensitive, self.recursive)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #11 · zero_cover · `GzipFile.seek`

- **位置**：`gzip.py:423`（22 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_PaddedFile.seek`, `GzipFile._init_write`, `GzipFile.rewind`（跨文件调用者未扫描）

**源码**：

```python
    def seek(self, offset, whence=io.SEEK_SET):
        if self.mode == WRITE:
            self._check_not_closed()
            # Flush buffer to ensure validity of self.offset
            self._buffer.flush()
            if whence != io.SEEK_SET:
                if whence == io.SEEK_CUR:
                    offset = self.offset + offset
                else:
                    raise ValueError('Seek from end not supported')
            if offset < self.offset:
                raise OSError('Negative seek in write mode')
            count = offset - self.offset
            chunk = b'\0' * self._buffer_size
            for i in range(count // self._buffer_size):
                self.write(chunk)
            self.write(b'\0' * (count % self._buffer_size))
        elif self.mode == READ:
            self._check_not_closed()
            return self._buffer.seek(offset, whence)

        return self.offset
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #12 · random · `IMAP4.uid`

- **位置**：`imaplib.py:888`（23 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def uid(self, command, *args):
        """Execute "command arg ..." with messages identified by UID,
                rather than message number.

        (typ, [data]) = <instance>.uid(command, arg1, arg2, ...)

        Returns response appropriate to 'command'.
        """
        command = command.upper()
        if not command in Commands:
            raise self.error("Unknown IMAP4 UID command: %s" % command)
        if self.state not in Commands[command]:
            raise self.error("command %s illegal in state %s, "
                             "only allowed in states %s" %
                             (command, self.state,
                              ', '.join(Commands[command])))
        name = 'UID'
        typ, dat = self._simple_command(name, command, *args)
        if command in ('SEARCH', 'SORT', 'THREAD'):
            name = command
        else:
            name = 'FETCH'
        return self._untagged_response(typ, dat, name)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #13 · confluence · `getfile`

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

## #14 · confluence · `getfullargspec`

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

## #15 · random · `IPv4Address.is_unspecified`

- **位置**：`ipaddress.py:1389`（9 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_BaseNetwork.is_unspecified`, `IPv6Address.is_unspecified`, `IPv6Interface.is_unspecified`（跨文件调用者未扫描）

**源码**：

```python
    def is_unspecified(self):
        """Test if the address is unspecified.

        Returns:
            A boolean, True if this is the unspecified address as defined in
            RFC 5735 3.

        """
        return self == self._constants._unspecified_address
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #16 · confluence · `normalize`

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

## #17 · random · `ModuleFinder.import_hook`

- **位置**：`modulefinder.py:167`（10 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-7 ｜ 池：（不在任何池内）
- **同文件调用者**：`test`, `ModuleFinder._safe_import_hook`, `ModuleFinder.scan_code`（跨文件调用者未扫描）

**源码**：

```python
    def import_hook(self, name, caller=None, fromlist=None, level=-1):
        self.msg(3, "import_hook", name, caller, fromlist, level)
        parent = self.determine_parent(caller, level=level)
        q, tail = self.find_head_package(parent, name)
        m = self.load_tail(q, tail)
        if not fromlist:
            return q
        if m.__path__:
            self.ensure_fromlist(m, fromlist)
        return None
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #18 · zero_cover · `netrc._parse`

- **位置**：`netrc.py:93`（63 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`netrc.__init__`（跨文件调用者未扫描）

**源码**：

```python
    def _parse(self, file, fp, default_netrc):
        lexer = _netrclex(fp)
        while 1:
            # Look for a machine, default, or macdef top-level keyword
            saved_lineno = lexer.lineno
            toplevel = tt = lexer.get_token()
            if not tt:
                break
            elif tt[0] == '#':
                if lexer.lineno == saved_lineno and len(tt) == 1:
                    lexer.instream.readline()
                continue
            elif tt == 'machine':
                entryname = lexer.get_token()
            elif tt == 'default':
                entryname = 'default'
            elif tt == 'macdef':
                entryname = lexer.get_token()
                self.macros[entryname] = []
                while 1:
                    line = lexer.instream.readline()
                    if not line:
                        raise NetrcParseError(
                            "Macro definition missing null line terminator.",
                            file, lexer.lineno)
                    if line == '\n':
                        # a macro definition finished with consecutive new-line
                        # characters. The first \n is encountered by the
                        # readline() method and this is the second \n.
                        break
                    self.macros[entryname].append(line)
                continue
            else:
                raise NetrcParseError(
                    "bad toplevel token %r" % tt, file, lexer.lineno)

            if not entryname:
                raise NetrcParseError("missing %r name" % tt, file, lexer.lineno)

            # We're looking at start of an entry for a named machine or default.
            login = account = password = ''
            self.hosts[entryname] = {}
            while 1:
                prev_lineno = lexer.lineno
                tt = lexer.get_token()
                if tt.startswith('#'):
                    if lexer.lineno == prev_lineno:
                        lexer.instream.readline()
                    continue
                if tt in {'', 'machine', 'default', 'macdef'}:
                    self.hosts[entryname] = (login, account, password)
                    lexer.push_token(tt)
                    break
                elif tt == 'login' or tt == 'user':
                    login = lexer.get_token()
                elif tt == 'account':
                    account = lexer.get_token()
                elif tt == 'password':
                    password = lexer.get_token()
                else:
```

> 已截断（共 63 行），完整见 `netrc.py:93`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #19 · anchor · `spawnl`

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

## #20 · random · `_Unpickler.load_binbytes`

- **位置**：`pickle.py:1387`（6 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def load_binbytes(self):
        len, = unpack('<I', self.read(4))
        if len > maxsize:
            raise UnpicklingError("BINBYTES exceeds system's maximum size "
                                  "of %d bytes" % maxsize)
        self.append(self.read(len))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #21 · anchor · `_Unpickler.find_class`

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

## #22 · anchor · `genops`

- **位置**：`pickletools.py:2300`（24 行）
- **层**：anchor ｜ 锚点命中 import:import_pickle
- **结构量**：Forman=-8 ｜ 池：p_anchor_breadth
- **本函数调用**：`_genops`
- **同文件调用者**：`_genops`, `optimize`, `dis`（跨文件调用者未扫描）
- **锚点命中行**：
  - L1 `def genops(pickle):` → import:import_pickle
  - L2 `"""Generate all the opcodes in a pickle.` → import:import_pickle
  - L4 `'pickle' is a file-like object, or string, containing the pickle.` → import:import_pickle
  - L6 `Each opcode in the pickle is generated, from the current pickle position,` → import:import_pickle
  - L14 `If the opcode has an argument embedded in the pickle, arg is its decoded` → import:import_pickle

**源码**：

```python
def genops(pickle):
    """Generate all the opcodes in a pickle.

    'pickle' is a file-like object, or string, containing the pickle.

    Each opcode in the pickle is generated, from the current pickle position,
    stopping after a STOP opcode is delivered.  A triple is generated for
    each opcode:

        opcode, arg, pos

    opcode is an OpcodeInfo record, describing the current opcode.

    If the opcode has an argument embedded in the pickle, arg is its decoded
    value, as a Python object.  If the opcode doesn't have an argument, arg
    is None.

    If the pickle has a tell() method, pos was the value of pickle.tell()
    before reading the current opcode.  If the pickle is a bytes object,
    it's wrapped in a BytesIO object, and the latter's tell() result is
    used.  Else (the pickle doesn't have a tell(), and it's not obvious how
    to query its current position) pos is None.
    """
    return _genops(pickle)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #23 · anchor · `OpcodeInfo.__init__`

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

## #24 · zero_cover · `ProfileBrowser.do_callers`

- **位置**：`pstats.py:677`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
        def do_callers(self, line):
            return self.generic('print_callers', line)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #25 · random · `_ModuleBrowser.visit_ImportFrom`

- **位置**：`pyclbr.py:248`（19 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def visit_ImportFrom(self, node):
        if node.col_offset != 0:
            return
        try:
            module = "." * node.level
            if node.module:
                module += node.module
            module = _readmodule(module, self.path, self.inpackage)
        except (ImportError, SyntaxError):
            return

        for name in node.names:
            if name.name in module:
                self.tree[name.asname or name.name] = module[name.name]
            elif name.name == "*":
                for import_name, import_value in module.items():
                    if import_name.startswith("_"):
                        continue
                    self.tree[import_name] = import_value
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #26 · zero_cover · `TextRepr.repr_instance`

- **位置**：`pydoc.py:1259`（5 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`HTMLRepr.repr_instance`（跨文件调用者未扫描）

**源码**：

```python
    def repr_instance(self, x, level):
        try:
            return cram(stripid(repr(x)), self.maxstring)
        except:
            return '<%s instance>' % x.__class__.__name__
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #27 · confluence · `_rmtree_unsafe`

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

## #28 · random · `TCPServer.get_request`

- **位置**：`socketserver.py:505`（7 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`BaseServer._handle_request_noblock`, `UDPServer.get_request`（跨文件调用者未扫描）

**源码**：

```python
    def get_request(self):
        """Get the request and client address from the socket.

        May be overridden.

        """
        return self.socket.accept()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #29 · zero_cover · `_SocketWriter.writable`

- **位置**：`socketserver.py:841`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def writable(self):
        return True
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #30 · anchor · `check_output`

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

## #31 · zero_cover · `TarInfo._proc_gnusparse_01`

- **位置**：`tarfile.py:1613`（5 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`TarInfo._proc_pax`（跨文件调用者未扫描）

**源码**：

```python
    def _proc_gnusparse_01(self, next, pax_headers):
        """Process a GNU tar extended sparse header, version 0.1.
        """
        sparse = [int(x) for x in pax_headers["GNU.sparse.map"].split(",")]
        next.sparse = list(zip(sparse[::2], sparse[1::2]))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #32 · zero_cover · `TarFile.makelink_with_filter`

- **位置**：`tarfile.py:2677`（52 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`TarFile._extract_member`, `TarFile.makelink`（跨文件调用者未扫描）

**源码**：

```python
    def makelink_with_filter(self, tarinfo, targetpath,
                             filter_function, extraction_root):
        """Make a (symbolic) link called targetpath. If it cannot be created
          (platform limitation), we try to make a copy of the referenced file
          instead of a link.

          filter_function is only used when extracting a *different*
          member (e.g. as fallback to creating a link).
        """
        keyerror_to_extracterror = False
        try:
            # For systems that support symbolic and hard links.
            if tarinfo.issym():
                if os.path.lexists(targetpath):
                    # Avoid FileExistsError on following os.symlink.
                    os.unlink(targetpath)
                os.symlink(tarinfo.linkname, targetpath)
                return
            else:
                if os.path.exists(tarinfo._link_target):
                    if os.path.lexists(targetpath):
                        # Avoid FileExistsError on following os.link.
                        os.unlink(targetpath)
                    os.link(tarinfo._link_target, targetpath)
                    return
        except symlink_exception:
            keyerror_to_extracterror = True

        try:
            unfiltered = self._find_link_target(tarinfo)
        except KeyError:
            if keyerror_to_extracterror:
                raise ExtractError(
                    "unable to resolve link inside archive") from None
            else:
                raise

        if filter_function is None:
            filtered = unfiltered
        else:
            if extraction_root is None:
                raise ExtractError(
                    "makelink_with_filter: if filter_function is not None, "
                    + "extraction_root must also not be None")
            try:
                filtered = filter_function(unfiltered, extraction_root)
            except _FILTER_ERRORS as cause:
                raise LinkFallbackError(tarinfo, unfiltered.name) from cause
        if filtered is not None:
            self._extract_member(filtered, targetpath,
                                 filter_function=filter_function,
                                 extraction_root=extraction_root)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #33 · random · `main`

- **位置**：`tokenize.py:502`（62 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-154 ｜ 池：（不在任何池内）
- **本函数调用**：`ArgumentParser`, `_builtin_open`, `_generate_tokens_from_c_tokenizer`, `add_argument`, `error`, `exit`, `list`, `parse_args`, `perror`, `print`, `tokenize`, `write`

**源码**：

```python
def main():
    import argparse

    # Helper error handling routines
    def perror(message):
        sys.stderr.write(message)
        sys.stderr.write('\n')

    def error(message, filename=None, location=None):
        if location:
            args = (filename,) + location + (message,)
            perror("%s:%d:%d: error: %s" % args)
        elif filename:
            perror("%s: error: %s" % (filename, message))
        else:
            perror("error: %s" % message)
        sys.exit(1)

    # Parse the arguments and options
    parser = argparse.ArgumentParser(prog='python -m tokenize')
    parser.add_argument(dest='filename', nargs='?',
                        metavar='filename.py',
                        help='the file to tokenize; defaults to stdin')
    parser.add_argument('-e', '--exact', dest='exact', action='store_true',
                        help='display token names using the exact type')
    args = parser.parse_args()

    try:
        # Tokenize the input
        if args.filename:
            filename = args.filename
            with _builtin_open(filename, 'rb') as f:
                tokens = list(tokenize(f.readline))
        else:
            filename = "<stdin>"
            tokens = _generate_tokens_from_c_tokenizer(
                sys.stdin.readline, extra_tokens=True)


        # Output the tokenization
        for token in tokens:
            token_type = token.type
            if args.exact:
                token_type = token.exact_type
            token_range = "%d,%d-%d,%d:" % (token.start + token.end)
            print("%-20s%-15s%-15r" %
                  (token_range, tok_name[token_type], token.string))
    except IndentationError as err:
        line, column = err.args[1][1:3]
        error(err.args[0], filename, (line, column))
    except TokenError as err:
        line, column = err.args[1]
        error(err.args[0], filename, (line, column))
    except SyntaxError as err:
        error(err, filename)
    except OSError as err:
        error(err)
    except KeyboardInterrupt:
        print("interrupted\n")
    except Exception as err:
```

> 已截断（共 62 行），完整见 `tokenize.py:502`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #34 · random · `_compare_args_orderless`

- **位置**：`typing.py:368`（10 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-147 ｜ 池：（不在任何池内）
- **本函数调用**：`_deduplicate_unhashable`, `list`, `remove`
- **同文件调用者**：`_UnionGenericAlias.__eq__`（跨文件调用者未扫描）

**源码**：

```python
def _compare_args_orderless(first_args, second_args):
    first_unhashable = _deduplicate_unhashable(first_args)
    second_unhashable = _deduplicate_unhashable(second_args)
    t = list(second_unhashable)
    try:
        for elem in first_unhashable:
            t.remove(elem)
    except ValueError:
        return False
    return not t
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #35 · zero_cover · `_is_universal`

- **位置**：`uuid.py:409`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=-8 ｜ 池：（不在任何池内）
- **同文件调用者**：`_find_mac_near_keyword`, `_find_mac_under_heading`（跨文件调用者未扫描）

**源码**：

```python
def _is_universal(mac):
    return not (mac & (1 << 41))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #36 · random · `WeakValueDictionary.popitem`

- **位置**：`weakref.py:252`（8 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`WeakKeyDictionary.popitem`（跨文件调用者未扫描）

**源码**：

```python
    def popitem(self):
        if self._pending_removals:
            self._commit_removals()
        while True:
            key, wr = self.data.popitem()
            o = wr()
            if o is not None:
                return key, o
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #37 · anchor · `register_standard_browsers`

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

## #38 · anchor · `GenericBrowser.open`

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

## #39 · anchor · `Konqueror.open`

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

## #40 · anchor · `_aix_bos_rte`

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

## #41 · random · `MutableSequence.pop`

- **位置**：`_collections_abc.py:1167`（7 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`MutableSet.pop`, `MutableSet.clear`, `MutableMapping.pop`, `MutableSequence.clear`（跨文件调用者未扫描）

**源码**：

```python
    def pop(self, index=-1):
        '''S.pop([index]) -> item -- remove and return item at index (default
        last).  Raise IndexError if list is empty or index is out of range.
        '''
        v = self[index]
        del self[index]
        return v
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #42 · zero_cover · `time.__le__`

- **位置**：`_pydatetime.py:1428`（5 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`timedelta.__le__`, `date.__le__`, `datetime.__le__`（跨文件调用者未扫描）

**源码**：

```python
    def __le__(self, other):
        if isinstance(other, time):
            return self._cmp(other) <= 0
        else:
            return NotImplemented
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #43 · zero_cover · `Decimal.compare`

- **位置**：`_pydecimal.py:840`（17 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Decimal.compare_signal`, `Context.compare`, `Context.compare_signal`（跨文件调用者未扫描）

**源码**：

```python
    def compare(self, other, context=None):
        """Compare self to other.  Return a decimal value:

        a or b is a NaN ==> Decimal('NaN')
        a < b           ==> Decimal('-1')
        a == b          ==> Decimal('0')
        a > b           ==> Decimal('1')
        """
        other = _convert_other(other, raiseit=True)

        # Compare(NaN, NaN) = NaN
        if (self._is_special or other and other._is_special):
            ans = self._check_nans(other, context)
            if ans:
                return ans

        return Decimal(self._cmp(other))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #44 · random · `TextIOWrapper.errors`

- **位置**：`_pyio.py:2121`（2 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`TextIOBase.errors`, `StringIO.errors`（跨文件调用者未扫描）

**源码**：

```python
    def errors(self):
        return self._errors
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #45 · random · `parse_int`

- **位置**：`_strptime.py:574`（5 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=-27 ｜ 池：（不在任何池内）
- **同文件调用者**：`_strptime`（跨文件调用者未扫描）

**源码**：

```python
        def parse_int(s):
            try:
                return locale_time.LC_alt_digits.index(s)
            except ValueError:
                return int(s)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #46 · anchor · `_format_pipe`

- **位置**：`asyncio/base_events.py:80`（7 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=-55 ｜ 池：p_anchor_breadth
- **本函数调用**：`repr`
- **同文件调用者**：`BaseEventLoop._log_subprocess`（跨文件调用者未扫描）
- **锚点命中行**：
  - L2 `if fd == subprocess.PIPE:` → import:import_subprocess
  - L4 `elif fd == subprocess.STDOUT:` → import:import_subprocess

**源码**：

```python
def _format_pipe(fd):
    if fd == subprocess.PIPE:
        return '<pipe>'
    elif fd == subprocess.STDOUT:
        return '<stdout>'
    else:
        return repr(fd)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #47 · anchor · `BaseEventLoop._log_subprocess`

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

## #48 · anchor · `AbstractEventLoop.subprocess_exec`

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

## #49 · zero_cover · `wrap_future`

- **位置**：`asyncio/futures.py:406`（11 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=-13 ｜ 池：（不在任何池内）
- **本函数调用**：`_chain_future`, `create_future`, `get_event_loop`, `isfuture`, `isinstance`

**源码**：

```python
def wrap_future(future, *, loop=None):
    """Wrap concurrent.futures.Future object."""
    if isfuture(future):
        return future
    assert isinstance(future, concurrent.futures.Future), \
        f'concurrent.futures.Future is expected, got {future!r}'
    if loop is None:
        loop = events.get_event_loop()
    new_future = loop.create_future()
    _chain_future(future, new_future)
    return new_future
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #50 · random · `Lock.__repr__`

- **位置**：`asyncio/locks.py:79`（6 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Event.__repr__`, `Condition.__repr__`, `Semaphore.__repr__`, `Barrier.__repr__`（跨文件调用者未扫描）

**源码**：

```python
    def __repr__(self):
        res = super().__repr__()
        extra = 'locked' if self._locked else 'unlocked'
        if self._waiters:
            extra = f'{extra}, waiters:{len(self._waiters)}'
        return f'<{res[1:-1]} [{extra}]>'
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #51 · zero_cover · `BoundedSemaphore.release`

- **位置**：`asyncio/locks.py:462`（4 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_ContextManagerMixin.__aexit__`, `Lock.release`, `Condition.__init__`, `Condition.wait`, `Semaphore.acquire`, `Semaphore.release`, `Barrier.wait`, `Barrier._release`（跨文件调用者未扫描）

**源码**：

```python
    def release(self):
        if self._value >= self._bound_value:
            raise ValueError('BoundedSemaphore released too many times')
        super().release()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #52 · anchor · `SubprocessTransport.get_returncode`

- **位置**：`asyncio/transports.py:207`（7 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L2 `"""Get subprocess returncode.` → import:import_subprocess
  - L5 `http://docs.python.org/3/library/subprocess#subprocess.Popen.returncode` → import:import_subprocess

**源码**：

```python
    def get_returncode(self):
        """Get subprocess returncode.

        See also
        http://docs.python.org/3/library/subprocess#subprocess.Popen.returncode
        """
        raise NotImplementedError
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #53 · anchor · `SubprocessTransport.kill`

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

## #54 · anchor · `_UnixSelectorEventLoop._make_subprocess_transport`

- **位置**：`asyncio/unix_events.py:198`（32 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L12 `# prevents subprocess execution if the watcher` → import:import_subprocess
  - L15 `"subprocess support is not installed.")` → import:import_subprocess

**源码**：

```python
    async def _make_subprocess_transport(self, protocol, args, shell,
                                         stdin, stdout, stderr, bufsize,
                                         extra=None, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            watcher = events.get_child_watcher()

        with watcher:
            if not watcher.is_active():
                # Check early.
                # Raising exception before process creation
                # prevents subprocess execution if the watcher
                # is not ready to handle it.
                raise RuntimeError("asyncio.get_child_watcher() is not activated, "
                                "subprocess support is not installed.")
            waiter = self.create_future()
            transp = _UnixSubprocessTransport(self, protocol, args, shell,
                                            stdin, stdout, stderr, bufsize,
                                            waiter=waiter, extra=extra,
                                            **kwargs)
            watcher.add_child_handler(transp.get_pid(),
                                    self._child_watcher_callback, transp)
            try:
                await waiter
            except (SystemExit, KeyboardInterrupt):
                raise
            except BaseException:
                transp.close()
                await transp._wait()
                raise

        return transp
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #55 · anchor · `namedtuple`

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

## #56 · anchor · `_findLib_gcc`

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

## #57 · confluence · `_encode_base64`

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

## #58 · zero_cover · `BufferedSubFile.unreadline`

- **位置**：`email/feedparser.py:97`（4 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`FeedParser._parsegen`, `FeedParser._parse_headers`（跨文件调用者未扫描）

**源码**：

```python
    def unreadline(self, line):
        # Let the consumer push a line back into the buffer.
        assert line is not NeedMoreData
        self._lines.appendleft(line)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #59 · zero_cover · `BufferedSubFile.pushlines`

- **位置**：`email/feedparser.py:123`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`BufferedSubFile.close`, `BufferedSubFile.push`（跨文件调用者未扫描）

**源码**：

```python
    def pushlines(self, lines):
        self._lines.extend(lines)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #60 · zero_cover · `FeedParser._new_message`

- **位置**：`email/feedparser.py:197`（12 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`FeedParser._parsegen`（跨文件调用者未扫描）

**源码**：

```python
    def _new_message(self):
        if self._old_style_factory:
            msg = self._factory()
        else:
            msg = self._factory(policy=self.policy)
        if self._cur and self._cur.get_content_type() == 'multipart/digest':
            msg.set_default_type('message/rfc822')
        if self._msgstack:
            self._msgstack[-1].attach(msg)
        self._msgstack.append(msg)
        self._cur = msg
        self._last = msg
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #61 · zero_cover · `MIMEPart._add_multipart`

- **位置**：`email/message.py:1183`（9 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`MIMEPart.add_related`, `MIMEPart.add_alternative`, `MIMEPart.add_attachment`（跨文件调用者未扫描）

**源码**：

```python
    def _add_multipart(self, _subtype, *args, _disp=None, **kw):
        if (self.get_content_maintype() != 'multipart' or
                self.get_content_subtype() != _subtype):
            getattr(self, 'make_' + _subtype)()
        part = type(self)(policy=self.policy)
        part.set_content(*args, **kw)
        if _disp and 'content-disposition' not in part:
            part['Content-Disposition'] = _disp
        self.attach(part)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #62 · confluence · `get_local_part`

- **位置**：`email/_header_value_parser.py:1486`（38 行）
- **层**：confluence ｜ 曲率汇合点 forman=-407
- **结构量**：Forman=-407 ｜ 池：p_hot, p_deep_conf
- **本函数调用**：`HeaderParseError`, `InvalidHeaderDefect`, `LocalPart`, `NonASCIILocalPartDefect`, `ObsoleteHeaderDefect`, `TokenList`, `append`, `encode`, `format`, `get_cfws`, `get_dot_atom`, `get_obs_local_part`
- **同文件调用者**：`get_addr_spec`（跨文件调用者未扫描）

**源码**：

```python
def get_local_part(value):
    """ local-part = dot-atom / quoted-string / obs-local-part

    """
    local_part = LocalPart()
    leader = None
    if value and value[0] in CFWS_LEADER:
        leader, value = get_cfws(value)
    if not value:
        raise errors.HeaderParseError(
            "expected local-part but found '{}'".format(value))
    try:
        token, value = get_dot_atom(value)
    except errors.HeaderParseError:
        try:
            token, value = get_word(value)
        except errors.HeaderParseError:
            if value[0] != '\\' and value[0] in PHRASE_ENDS:
                raise
            token = TokenList()
    if leader is not None:
        token[:0] = [leader]
    local_part.append(token)
    if value and (value[0]=='\\' or value[0] not in PHRASE_ENDS):
        obs_local_part, value = get_obs_local_part(str(local_part) + value)
        if obs_local_part.token_type == 'invalid-obs-local-part':
            local_part.defects.append(errors.InvalidHeaderDefect(
                "local-part is not dot-atom, quoted-string, or obs-local-part"))
        else:
            local_part.defects.append(errors.ObsoleteHeaderDefect(
                "local-part is not a dot-atom (contains CFWS)"))
        local_part[0] = obs_local_part
    try:
        local_part.value.encode('ascii')
    except UnicodeEncodeError:
        local_part.defects.append(errors.NonASCIILocalPartDefect(
                "local-part contains non-ASCII characters)"))
    return local_part, value
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #63 · confluence · `rule`

- **位置**：`email/mime/audio.py:68`（3 行）
- **层**：confluence ｜ 曲率汇合点 forman=-376
- **结构量**：Forman=-376 ｜ 池：（不在任何池内）
- **本函数调用**：`append`

**源码**：

```python
def rule(rulefunc):
    _rules.append(rulefunc)
    return rulefunc
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #64 · confluence · `_au`

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

## #65 · random · `IncrementalEncoder.encode`

- **位置**：`encodings/koi8_r.py:18`（2 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Codec.encode`（跨文件调用者未扫描）

**源码**：

```python
    def encode(self, input, final=False):
        return codecs.charmap_encode(input,self.errors,encoding_table)[0]
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #66 · random · `IncrementalEncoder.reset`

- **位置**：`encodings/utf_16.py:33`（3 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`IncrementalDecoder.reset`, `StreamWriter.reset`, `StreamReader.reset`（跨文件调用者未扫描）

**源码**：

```python
    def reset(self):
        codecs.IncrementalEncoder.reset(self)
        self.encoder = None
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #67 · anchor · `_run_pip`

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

## #68 · random · `LineTooLong.__init__`

- **位置**：`http/client.py:1569`（3 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`HTTPResponse.__init__`, `HTTPConnection.__init__`, `UnknownProtocol.__init__`, `IncompleteRead.__init__`, `BadStatusLine.__init__`, `RemoteDisconnected.__init__`, `HTTPSConnection.__init__`（跨文件调用者未扫描）

**源码**：

```python
    def __init__(self, line_type):
        HTTPException.__init__(self, "got more than %d bytes when reading %s"
                                     % (_MAXLINE, line_type))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #69 · zero_cover · `Morsel.__ior__`

- **位置**：`http/cookies.py:344`（3 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def __ior__(self, values):
        self.update(values)
        return self
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #70 · confluence · `_url_collapse_path`

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

## #71 · zero_cover · `HTTPServer.server_bind`

- **位置**：`http/server.py:138`（6 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`DualStackServer.server_bind`（跨文件调用者未扫描）

**源码**：

```python
    def server_bind(self):
        """Override server_bind to store the server name."""
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #72 · anchor · `CGIHTTPRequestHandler.run_cgi`

- **位置**：`http/server.py:1074`（196 行）
- **层**：anchor ｜ 锚点命中 import:import_subprocess
- **结构量**：Forman=None ｜ 池：p_anchor_breadth, p_big1
- **同文件调用者**：`CGIHTTPRequestHandler.do_POST`, `CGIHTTPRequestHandler.send_head`（跨文件调用者未扫描）
- **锚点命中行**：
  - L145 `# Non-Unix -- use subprocess` → import:import_subprocess
  - L146 `import subprocess` → import:import_subprocess
  - L156 `self.log_message("command: %s", subprocess.list2cmdline(cmdline))` → import:import_subprocess
  - L161 `p = subprocess.Popen(cmdline,` → import:import_subprocess
  - L162 `stdin=subprocess.PIPE,` → import:import_subprocess

**源码**：

```python
    def run_cgi(self):
        """Execute a CGI script."""
        dir, rest = self.cgi_info
        path = dir + '/' + rest
        i = path.find('/', len(dir)+1)
        while i >= 0:
            nextdir = path[:i]
            nextrest = path[i+1:]

            scriptdir = self.translate_path(nextdir)
            if os.path.isdir(scriptdir):
                dir, rest = nextdir, nextrest
                i = path.find('/', len(dir)+1)
            else:
                break

        # find an explicit query string, if present.
        rest, _, query = rest.partition('?')

        # dissect the part after the directory name into a script name &
        # a possible additional path, to be stored in PATH_INFO.
        i = rest.find('/')
        if i >= 0:
            script, rest = rest[:i], rest[i:]
        else:
            script, rest = rest, ''

        scriptname = dir + '/' + script
        scriptfile = self.translate_path(scriptname)
        if not os.path.exists(scriptfile):
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "No such CGI script (%r)" % scriptname)
            return
        if not os.path.isfile(scriptfile):
            self.send_error(
                HTTPStatus.FORBIDDEN,
                "CGI script is not a plain file (%r)" % scriptname)
            return
        ispy = self.is_python(scriptname)
        if self.have_fork or not ispy:
            if not self.is_executable(scriptfile):
                self.send_error(
                    HTTPStatus.FORBIDDEN,
                    "CGI script is not executable (%r)" % scriptname)
                return

        # Reference: https://www6.uniovi.es/~antonio/ncsa_httpd/cgi/env.html
        # XXX Much of the following could be prepared ahead of time!
        env = copy.deepcopy(os.environ)
        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command
        uqrest = urllib.parse.unquote(rest)
        env['PATH_INFO'] = uqrest
        env['PATH_TRANSLATED'] = self.translate_path(uqrest)
        env['SCRIPT_NAME'] = scriptname
```

> 已截断（共 196 行），完整见 `http/server.py:1074`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #73 · confluence · `_install`

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

## #74 · random · `NamespaceReader._resolve_zip_path`

- **位置**：`importlib/resources/readers.py:165`（10 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`NamespaceReader._candidate_paths`（跨文件调用者未扫描）

**源码**：

```python
    def _resolve_zip_path(path_str: str):
        for match in reversed(list(re.finditer(r'[\\/]', path_str))):
            with contextlib.suppress(
                FileNotFoundError,
                IsADirectoryError,
                NotADirectoryError,
                PermissionError,
            ):
                inner = path_str[match.end() :].replace('\\', '/') + '/'
                yield zipfile.Path(path_str[: match.start()], inner.lstrip('/'))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #75 · confluence · `_strip_spaces`

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

## #76 · anchor · `SocketHandler.makePickle`

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

## #77 · confluence · `_checkLevel`

- **位置**：`logging/__init__.py:205`（11 行）
- **层**：confluence ｜ 曲率汇合点 forman=-172
- **结构量**：Forman=-172 ｜ 池：（不在任何池内）
- **本函数调用**：`TypeError`, `ValueError`, `isinstance`, `str`
- **同文件调用者**：`Handler.__init__`, `Handler.setLevel`, `Manager.disable`, `Logger.__init__`, `Logger.setLevel`（跨文件调用者未扫描）

**源码**：

```python
def _checkLevel(level):
    if isinstance(level, int):
        rv = level
    elif str(level) == level:
        if level not in _nameToLevel:
            raise ValueError("Unknown level: %r" % level)
        rv = _nameToLevel[level]
    else:
        raise TypeError("Level not an integer or a valid string: %r"
                        % (level,))
    return rv
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #78 · anchor · `XmlListener.accept`

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

## #79 · random · `ApplyResult.wait`

- **位置**：`multiprocessing/pool.py:764`（2 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Pool._wait_for_updates`, `ApplyResult.get`, `IMapIterator.next`（跨文件调用者未扫描）

**源码**：

```python
    def wait(self, timeout=None):
        self._event.wait(timeout)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #80 · anchor · `get_preparation_data`

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

## #81 · random · `Condition.__setstate__`

- **位置**：`multiprocessing/synchronize.py:231`（4 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`SemLock.__setstate__`, `Barrier.__init__`, `Barrier.__setstate__`（跨文件调用者未扫描）

**源码**：

```python
    def __setstate__(self, state):
        (self._lock, self._sleeping_count,
         self._woken_count, self._wait_semaphore) = state
        self._make_methods()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #82 · zero_cover · `_AssertRaisesBaseContext.handle`

- **位置**：`unittest/case.py:214`（28 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`TestCase.assertRaises`, `TestCase.assertWarns`, `TestCase._assertNotWarns`, `TestCase.assertRaisesRegex`, `TestCase.assertWarnsRegex`（跨文件调用者未扫描）

**源码**：

```python
    def handle(self, name, args, kwargs):
        """
        If args is empty, assertRaises/Warns is being used as a
        context manager, so check for a 'msg' kwarg and return self.
        If args is not empty, call a callable passing positional and keyword
        arguments.
        """
        try:
            if not _is_subtype(self.expected, self._base_type):
                raise TypeError('%s() arg 1 must be %s' %
                                (name, self._base_type_str))
            if not args:
                self.msg = kwargs.pop('msg', None)
                if kwargs:
                    raise TypeError('%r is an invalid keyword argument for '
                                    'this function' % (next(iter(kwargs)),))
                return self

            callable_obj, *args = args
            try:
                self.obj_name = callable_obj.__name__
            except AttributeError:
                self.obj_name = str(callable_obj)
            with self:
                callable_obj(*args, **kwargs)
        finally:
            # bpo-23890: manually break a reference cycle
            self = None
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #83 · random · `MagicMixin._mock_set_magics`

- **位置**：`unittest/mock.py:2179`（21 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`MagicMixin.__init__`, `NonCallableMagicMock.mock_add_spec`, `MagicMock.mock_add_spec`（跨文件调用者未扫描）

**源码**：

```python
    def _mock_set_magics(self):
        orig_magics = _magics | _async_method_magics
        these_magics = orig_magics

        if getattr(self, "_mock_methods", None) is not None:
            these_magics = orig_magics.intersection(self._mock_methods)

            remove_magics = set()
            remove_magics = orig_magics - these_magics

            for entry in remove_magics:
                if entry in type(self).__dict__:
                    # remove unneeded magic methods
                    delattr(self, entry)

        # don't overwrite existing attributes if called a second time
        these_magics = these_magics - set(type(self).__dict__)

        _type = type(self)
        for entry in these_magics:
            setattr(_type, entry, MagicProxy(entry, self))
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #84 · zero_cover · `MagicProxy.__init__`

- **位置**：`unittest/mock.py:2253`（3 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_SentinelObject.__init__`, `_Sentinel.__init__`, `_MockIter.__init__`, `Base.__init__`, `NonCallableMock.__init__`, `CallableMixin.__init__`, `_patch.__init__`, `_patch_dict.__init__`（跨文件调用者未扫描）

**源码**：

```python
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #85 · zero_cover · `_exit_side_effect`

- **位置**：`unittest/mock.py:2994`（2 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`mock_open`（跨文件调用者未扫描）

**源码**：

```python
    def _exit_side_effect(exctype, excinst, exctb):
        handle.close()
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #86 · zero_cover · `ThreadingMixin._get_child_mock`

- **位置**：`unittest/mock.py:3062`（6 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`NonCallableMock.__get_return_value`, `NonCallableMock.__getattr__`, `NonCallableMock._get_child_mock`, `MagicProxy.create_mock`, `PropertyMock._get_child_mock`（跨文件调用者未扫描）

**源码**：

```python
    def _get_child_mock(self, /, **kw):
        if isinstance(kw.get("parent"), ThreadingMixin):
            kw["timeout"] = kw["parent"]._mock_wait_timeout
        elif isinstance(kw.get("_new_parent"), ThreadingMixin):
            kw["timeout"] = kw["_new_parent"]._mock_wait_timeout
        return super()._get_child_mock(**kw)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #87 · random · `TestResult._setupStdout`

- **位置**：`unittest/result.py:65`（7 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`TestResult.startTest`（跨文件调用者未扫描）

**源码**：

```python
    def _setupStdout(self):
        if self.buffer:
            if self._stderr_buffer is None:
                self._stderr_buffer = io.StringIO()
                self._stdout_buffer = io.StringIO()
            sys.stdout = self._stdout_buffer
            sys.stderr = self._stderr_buffer
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #88 · zero_cover · `_NetlocResultMixinStr._hostinfo`

- **位置**：`urllib/parse.py:206`（12 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`_check_bracketed_netloc`, `_NetlocResultMixinBytes._hostinfo`（跨文件调用者未扫描）

**源码**：

```python
    def _hostinfo(self):
        netloc = self.netloc
        _, _, hostinfo = netloc.rpartition('@')
        _, have_open_br, bracketed = hostinfo.partition('[')
        if have_open_br:
            hostname, _, port = bracketed.partition(']')
            _, _, port = port.partition(':')
        else:
            hostname, _, port = hostinfo.partition(':')
        if not port:
            port = None
        return hostname, port
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #89 · confluence · `read_environ`

- **位置**：`wsgiref/handlers.py:34`（58 行）
- **层**：confluence ｜ 曲率汇合点 forman=-214
- **结构量**：Forman=-214 ｜ 池：（不在任何池内）
- **本函数调用**：`_needs_transcode`, `decode`, `encode`, `get`, `getfilesystemencoding`, `items`, `lower`, `startswith`
- **同文件调用者**：`CGIHandler.__init__`, `IISCGIHandler.__init__`（跨文件调用者未扫描）

**源码**：

```python
def read_environ():
    """Read environment, fixing HTTP variables"""
    enc = sys.getfilesystemencoding()
    esc = 'surrogateescape'
    try:
        ''.encode('utf-8', esc)
    except LookupError:
        esc = 'replace'
    environ = {}

    # Take the basic environment from native-unicode os.environ. Attempt to
    # fix up the variables that come from the HTTP request to compensate for
    # the bytes->unicode decoding step that will already have taken place.
    for k, v in os.environ.items():
        if _needs_transcode(k):

            # On win32, the os.environ is natively Unicode. Different servers
            # decode the request bytes using different encodings.
            if sys.platform == 'win32':
                software = os.environ.get('SERVER_SOFTWARE', '').lower()

                # On IIS, the HTTP request will be decoded as UTF-8 as long
                # as the input is a valid UTF-8 sequence. Otherwise it is
                # decoded using the system code page (mbcs), with no way to
                # detect this has happened. Because UTF-8 is the more likely
                # encoding, and mbcs is inherently unreliable (an mbcs string
                # that happens to be valid UTF-8 will not be decoded as mbcs)
                # always recreate the original bytes as UTF-8.
                if software.startswith('microsoft-iis/'):
                    v = v.encode('utf-8').decode('iso-8859-1')

                # Apache mod_cgi writes bytes-as-unicode (as if ISO-8859-1) direct
                # to the Unicode environ. No modification needed.
                elif software.startswith('apache/'):
                    pass

                # Python 3's http.server.CGIHTTPRequestHandler decodes
                # using the urllib.unquote default of UTF-8, amongst other
                # issues.
                elif (
                    software.startswith('simplehttp/')
                    and 'python/3' in software
                ):
                    v = v.encode('utf-8').decode('iso-8859-1')

                # For other servers, guess that they have written bytes to
                # the environ using stdio byte-oriented interfaces, ending up
                # with the system code page.
                else:
                    v = v.encode(enc, 'replace').decode('iso-8859-1')

            # Recover bytes from unicode environ, using surrogate escapes
            # where available (Python 3.1+).
            else:
                v = v.encode(enc, esc).decode('iso-8859-1')

        environ[k] = v
    return environ
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #90 · confluence · `_parse_ns_name`

- **位置**：`xml/dom/expatbuilder.py:114`（17 行）
- **层**：confluence ｜ 曲率汇合点 forman=-221
- **结构量**：Forman=-221 ｜ 池：（不在任何池内）
- **本函数调用**：`ValueError`, `intern`, `len`, `split`
- **同文件调用者**：`Namespaces.start_element_handler`, `Namespaces.end_element_handler`（跨文件调用者未扫描）

**源码**：

```python
def _parse_ns_name(builder, name):
    assert ' ' in name
    parts = name.split(' ')
    intern = builder._intern_setdefault
    if len(parts) == 3:
        uri, localname, prefix = parts
        prefix = intern(prefix, prefix)
        qname = "%s:%s" % (prefix, localname)
        qname = intern(qname, qname)
        localname = intern(localname, localname)
    elif len(parts) == 2:
        uri, localname = parts
        prefix = EMPTY_PREFIX
        qname = localname = intern(localname, localname)
    else:
        raise ValueError("Unsupported syntax: spaces in URIs not supported: %r" % name)
    return intern(uri, uri), localname, prefix, qname
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #91 · random · `Node._get_lastChild`

- **位置**：`xml/dom/minidom.py:78`（3 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Childless._get_lastChild`（跨文件调用者未扫描）

**源码**：

```python
    def _get_lastChild(self):
        if self.childNodes:
            return self.childNodes[-1]
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #92 · anchor · `DOMBuilder._parse_bytestream`

- **位置**：`xml/dom/xmlbuilder.py:202`（4 行）
- **层**：anchor ｜ 锚点命中 import:import_xml_expat
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **同文件调用者**：`DOMBuilder.parse`（跨文件调用者未扫描）
- **锚点命中行**：
  - L2 `import xml.dom.expatbuilder` → import:import_xml_expat
  - L3 `builder = xml.dom.expatbuilder.makeBuilder(options)` → import:import_xml_expat

**源码**：

```python
    def _parse_bytestream(self, stream, options):
        import xml.dom.expatbuilder
        builder = xml.dom.expatbuilder.makeBuilder(options)
        return builder.parseFile(stream)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #93 · confluence · `_include`

- **位置**：`xml/etree/ElementInclude.py:132`（55 行）
- **层**：confluence ｜ 曲率汇合点 forman=-220
- **结构量**：Forman=-220 ｜ 池：（不在任何池内）
- **本函数调用**：`FatalIncludeError`, `LimitedRecursiveIncludeError`, `_include`, `add`, `copy`, `get`, `len`, `loader`, `remove`, `urljoin`
- **同文件调用者**：`include`（跨文件调用者未扫描）

**源码**：

```python
def _include(elem, loader, base_url, max_depth, _parent_hrefs):
    # look for xinclude elements
    i = 0
    while i < len(elem):
        e = elem[i]
        if e.tag == XINCLUDE_INCLUDE:
            # process xinclude directive
            href = e.get("href")
            if base_url:
                href = urljoin(base_url, href)
            parse = e.get("parse", "xml")
            if parse == "xml":
                if href in _parent_hrefs:
                    raise FatalIncludeError("recursive include of %s" % href)
                if max_depth == 0:
                    raise LimitedRecursiveIncludeError(
                        "maximum xinclude depth reached when including file %s" % href)
                _parent_hrefs.add(href)
                node = loader(href, parse)
                if node is None:
                    raise FatalIncludeError(
                        "cannot load %r as %r" % (href, parse)
                        )
                node = copy.copy(node)  # FIXME: this makes little sense with recursive includes
                _include(node, loader, href, max_depth - 1, _parent_hrefs)
                _parent_hrefs.remove(href)
                if e.tail:
                    node.tail = (node.tail or "") + e.tail
                elem[i] = node
            elif parse == "text":
                text = loader(href, parse, e.get("encoding"))
                if text is None:
                    raise FatalIncludeError(
                        "cannot load %r as %r" % (href, parse)
                        )
                if e.tail:
                    text += e.tail
                if i:
                    node = elem[i-1]
                    node.tail = (node.tail or "") + text
                else:
                    elem.text = (elem.text or "") + text
                del elem[i]
                continue
            else:
                raise FatalIncludeError(
                    "unknown parse type in xi:include tag (%r)" % parse
                )
        elif e.tag == XINCLUDE_FALLBACK:
            raise FatalIncludeError(
                "xi:fallback tag must be child of xi:include (%r)" % e.tag
                )
        else:
            _include(e, loader, base_url, max_depth, _parent_hrefs)
        i += 1
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #94 · random · `Unmarshaller.end_value`

- **位置**：`xmlrpc/client.py:782`（5 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def end_value(self, data):
        # if we stumble upon a value element with no internal
        # elements, treat it as a string element
        if self._value:
            self.end_string(data)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #95 · anchor · `SimpleXMLRPCDispatcher.register_introspection_functions`

- **位置**：`xmlrpc/server.py:225`（10 行）
- **层**：anchor ｜ 锚点命中 import:import_xmlrpclib
- **结构量**：Forman=None ｜ 池：p_anchor_breadth
- **锚点命中行**：
  - L5 `see http://xmlrpc.usefulinc.com/doc/reserved.html` → import:import_xmlrpclib

**源码**：

```python
    def register_introspection_functions(self):
        """Registers the XML-RPC introspection methods in the system
        namespace.

        see http://xmlrpc.usefulinc.com/doc/reserved.html
        """

        self.funcs.update({'system.listMethods' : self.system_listMethods,
                      'system.methodSignature' : self.system_methodSignature,
                      'system.methodHelp' : self.system_methodHelp})
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #96 · confluence · `main`

- **位置**：`zipfile/__init__.py:2316`（68 行）
- **层**：confluence ｜ 曲率汇合点 forman=-381
- **结构量**：Forman=-381 ｜ 池：（不在任何池内）
- **本函数调用**：`ArgumentParser`, `ZipFile`, `addToZip`, `add_argument`, `add_mutually_exclusive_group`, `basename`, `dirname`, `exit`, `extractall`, `format`, `isdir`, `isfile`

**源码**：

```python
def main(args=None):
    import argparse

    description = 'A simple command-line interface for zipfile module.'
    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-l', '--list', metavar='<zipfile>',
                       help='Show listing of a zipfile')
    group.add_argument('-e', '--extract', nargs=2,
                       metavar=('<zipfile>', '<output_dir>'),
                       help='Extract zipfile into target dir')
    group.add_argument('-c', '--create', nargs='+',
                       metavar=('<name>', '<file>'),
                       help='Create zipfile from sources')
    group.add_argument('-t', '--test', metavar='<zipfile>',
                       help='Test if a zipfile is valid')
    parser.add_argument('--metadata-encoding', metavar='<encoding>',
                        help='Specify encoding of member names for -l, -e and -t')
    args = parser.parse_args(args)

    encoding = args.metadata_encoding

    if args.test is not None:
        src = args.test
        with ZipFile(src, 'r', metadata_encoding=encoding) as zf:
            badfile = zf.testzip()
        if badfile:
            print("The following enclosed file is corrupted: {!r}".format(badfile))
        print("Done testing")

    elif args.list is not None:
        src = args.list
        with ZipFile(src, 'r', metadata_encoding=encoding) as zf:
            zf.printdir()

    elif args.extract is not None:
        src, curdir = args.extract
        with ZipFile(src, 'r', metadata_encoding=encoding) as zf:
            zf.extractall(curdir)

    elif args.create is not None:
        if encoding:
            print("Non-conforming encodings not supported with -c.",
                  file=sys.stderr)
            sys.exit(1)

        zip_name = args.create.pop(0)
        files = args.create

        def addToZip(zf, path, zippath):
            if os.path.isfile(path):
                zf.write(path, zippath, ZIP_DEFLATED)
            elif os.path.isdir(path):
                if zippath:
                    zf.write(path, zippath)
                for nm in sorted(os.listdir(path)):
                    addToZip(zf,
                             os.path.join(path, nm), os.path.join(zippath, nm))
            # else: ignore

```

> 已截断（共 68 行），完整见 `zipfile/__init__.py:2316`

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #97 · random · `Translator.restrict_rglob`

- **位置**：`zipfile/_path/glob.py:77`（13 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）
- **同文件调用者**：`Translator.translate_core`（跨文件调用者未扫描）

**源码**：

```python
    def restrict_rglob(self, pattern):
        """
        Raise ValueError if ** appears in anything but a full path segment.

        >>> Translator().translate('**foo')
        Traceback (most recent call last):
        ...
        ValueError: ** must appear alone in a path segment
        """
        seps_pattern = rf'[{re.escape(self.seps)}]+'
        segments = re.split(seps_pattern, pattern)
        if any('**' in segment and segment != '**' for segment in segments):
            raise ValueError("** must appear alone in a path segment")
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #98 · confluence · `_validate_tzfile_path`

- **位置**：`zoneinfo/_tzpath.py:92`（21 行）
- **层**：confluence ｜ 曲率汇合点 forman=-366
- **结构量**：Forman=-366 ｜ 池：（不在任何池内）
- **本函数调用**：`ValueError`, `isabs`, `join`, `len`, `normpath`, `startswith`
- **同文件调用者**：`find_tzfile`（跨文件调用者未扫描）

**源码**：

```python
def _validate_tzfile_path(path, _base=_TEST_PATH):
    if os.path.isabs(path):
        raise ValueError(
            f"ZoneInfo keys may not be absolute paths, got: {path}"
        )

    # We only care about the kinds of path normalizations that would change the
    # length of the key - e.g. a/../b -> a/b, or a/b/ -> a/b. On Windows,
    # normpath will also change from a/b to a\b, but that would still preserve
    # the length.
    new_path = os.path.normpath(path)
    if len(new_path) != len(path):
        raise ValueError(
            f"ZoneInfo keys must be normalized relative paths, got: {path}"
        )

    resolved = os.path.normpath(os.path.join(_base, new_path))
    if not resolved.startswith(_base):
        raise ValueError(
            f"ZoneInfo keys must refer to subdirectories of TZPATH, got: {path}"
        )
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #99 · random · `_TZStr._get_trans_info`

- **位置**：`zoneinfo/_zoneinfo.py:465`（23 行）
- **层**：random ｜ 随机层（无偏基线）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def _get_trans_info(self, ts, year, fold):
        """Get the information about the current transition - tti"""
        start, end = self.transitions(year)

        # With fold = 0, the period (denominated in local time) with the
        # smaller offset starts at the end of the gap and ends at the end of
        # the fold; with fold = 1, it runs from the start of the gap to the
        # beginning of the fold.
        #
        # So in order to determine the DST boundaries we need to know both
        # the fold and whether DST is positive or negative (rare), and it
        # turns out that this boils down to fold XOR is_positive.
        if fold == (self.dst_diff >= 0):
            end -= self.dst_diff
        else:
            start += self.dst_diff

        if start < end:
            isdst = start <= ts < end
        else:
            isdst = not (end <= ts < start)

        return self.dst if isdst else self.std
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---

## #100 · zero_cover · `UnixConsole.__move_x_hpa`

- **位置**：`_pyrepl/unix_console.py:759`（3 行）
- **层**：zero_cover ｜ 零覆盖：不在任何池内（盲区核查）
- **结构量**：Forman=None ｜ 池：（不在任何池内）

**源码**：

```python
    def __move_x_hpa(self, x: int) -> None:
        if x != self.posxy[0]:
            self.__write_code(self._hpa, x)
```

**判定**：truth = `___`（1 有缺陷 / 0 无缺陷 / **None 判不出来就填 None**） ｜ defect_type = `___` ｜ 备注 = `___`

---
