import pydoc as P
want = 'TextRepr'
cls = getattr(P, want, None)
print('resolved class:', cls)
inst = cls()
class BoomKI:
    def __repr__(self): raise KeyboardInterrupt('ctrl-c')
class BoomSE:
    def __repr__(self): raise SystemExit(3)
class BoomPlain:
    def __repr__(self): raise ValueError('nope')
cases = [('POSITIVE CONTROL plain object', object()),
         ('NEGATIVE CONTROL repr raises ValueError', BoomPlain()),
         ('ATTACK repr raises KeyboardInterrupt', BoomKI()),
         ('ATTACK repr raises SystemExit', BoomSE())]
for label, obj in cases:
    try:
        r = inst.repr_instance(obj, 0)
        print('  ' + label.ljust(42) + ' -> SWALLOWED, returned ' + repr(r))
    except BaseException as e:
        print('  ' + label.ljust(42) + ' -> propagated ' + type(e).__name__)
