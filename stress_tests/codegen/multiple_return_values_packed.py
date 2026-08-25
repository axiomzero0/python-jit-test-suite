# -*- coding: utf-8 -*-
# stress test: multiple_return_values_packed
# category: codegen
#
# Target: `return a, b, c` builds a tuple and returns it. The caller can then unpack or treat it as a single value. The JIT must build the tuple at the return site, not elide it even if the caller immediately unpacks.
#
# Tags: ['codegen', 'return', 'tuple-pack']
def three():
    return 1, 2, 3

r = three()
assert isinstance(r, tuple)
assert r == (1, 2, 3)
assert len(r) == 3

# Unpacking at call site
a, b, c = three()
assert (a, b, c) == (1, 2, 3)

# Mixed return types
def mixed():
    return 1, "hello", [1, 2], {'k': 'v'}
n, s, lst, d = mixed()
assert n == 1
assert s == "hello"
assert lst == [1, 2]
assert d == {'k': 'v'}

# Single-element tuple (trailing comma)
def single():
    return 42,
assert single() == (42,)
assert isinstance(single(), tuple)

# Empty return (None)
def nothing():
    return
assert nothing() is None

# Single non-tuple value
def just_int():
    return 42
assert just_int() == 42
assert not isinstance(just_int(), tuple)

# Return a generator expression (not a tuple)
def gen_return():
    return (x * 2 for x in range(3))
g = gen_return()
assert list(g) == [0, 2, 4]
assert isinstance(g, type((x for x in [])))  # generator type

# Star unpacking in return
def variadic_return(*args):
    return args
assert variadic_return(1, 2, 3) == (1, 2, 3)
assert isinstance(variadic_return(), tuple)
assert variadic_return() == ()

# Conditional return (single ternary expression with nested parens)
def classify(n):
    return ('neg', n) if n < 0 else (('zero', n) if n == 0 else ('pos', n))
assert classify(-5) == ('neg', -5)
assert classify(0) == ('zero', 0)
assert classify(7) == ('pos', 7)

