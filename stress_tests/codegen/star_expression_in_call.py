# -*- coding: utf-8 -*-
# stress test: star_expression_in_call
# category: codegen
#
# Target: A function call uses `*args` to unpack an iterable as positional arguments. The unpacking can be combined with positional and keyword args, and multiple iterables can be unpacked in the same call.
#
# Tags: ['call', 'codegen', 'star-unpack']
def f(a, b, c):
    return a + b + c

args = [1, 2, 3]
assert f(*args) == 6

# Mix of positional and starred
def g(a, b, c, d):
    return a * 1000 + b * 100 + c * 10 + d

assert g(1, *[2, 3, 4]) == 1234
assert g(*[1, 2], 3, 4) == 1234
assert g(*[1, 2], *[3, 4]) == 1234

# Empty star
def h():
    return 'no args'
assert h(*[]) == 'no args'

# Variadic with star
def variadic(*args, **kw):
    return sum(args), sorted(kw.items())
assert variadic(1, *[2, 3]) == (6, [])
assert variadic(1, *[2], x=10) == (3, [('x', 10)])

# Star unpacks a generator
def sum_three(a, b, c):
    return a + b + c
assert sum_three(*iter([10, 20, 30])) == 60

# Star unpacks a string (chars become positional args)
def cat3(a, b, c):
    return a + b + c
assert cat3(*'xyz') == 'xyz'

# Multiple stars in same call
def five(a, b, c, d, e):
    return (a, b, c, d, e)
assert five(*[1, 2], *[3, 4], 5) == (1, 2, 3, 4, 5)

# Too many args raises
try:
    f(*[1, 2, 3, 4])
    assert False, "expected TypeError"
except TypeError:
    pass

