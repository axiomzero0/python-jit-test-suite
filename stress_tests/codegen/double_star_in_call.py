# -*- coding: utf-8 -*-
# stress test: double_star_in_call
# category: codegen
#
# Target: A function call uses `**kwargs` to unpack a dict as keyword arguments. Multiple dicts can be unpacked in the same call, mixed with explicit keyword args.
#
# Tags: ['call', 'codegen', 'double-star', 'kwargs']
def f(a, b, c):
    return f"{a}-{b}-{c}"

kwargs = {'a': 1, 'b': 2, 'c': 3}
assert f(**kwargs) == "1-2-3"

# Mix of positional and keyword
def g(a, b, c, d):
    return (a, b, c, d)
assert g(1, **{'b': 2, 'c': 3}, d=4) == (1, 2, 3, 4)

# Variadic with double star
def h(**kw):
    return sorted(kw.items())
d1 = {'a': 1, 'b': 2}
d2 = {'c': 3}
result = h(**d1, **d2, e=4)
assert result == [('a', 1), ('b', 2), ('c', 3), ('e', 4)]

# Empty double star
def k():
    return 'ok'
assert k(**{}) == 'ok'

# Double unpacking merge (PEP 448)
merged = {**d1, **d2, 'e': 4}
assert merged == {'a': 1, 'b': 2, 'c': 3, 'e': 4}

# Conflicting keys raise
def two(a):
    return a
try:
    two(a=1, **{'a': 2})
    assert False, "expected TypeError for multiple values"
except TypeError:
    pass

# Mixing * and **
def both(a, b, c):
    return (a, b, c)
assert both(*[1, 2], **{'c': 3}) == (1, 2, 3)
assert both(1, *[2], **{'c': 3}) == (1, 2, 3)

