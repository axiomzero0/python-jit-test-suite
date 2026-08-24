# -*- coding: utf-8 -*-
# stress test: modify_function_defaults
# category: metaprog_invalidation
# opt_state: (runs across all 6 states)
#
# Target: A function's __defaults__ tuple is replaced mid-program. Subsequent calls must use the new defaults, not the ones captured at def time.
#
# Tags: ['defaults', 'function', 'invalidation']
def f(a, b=10):
    return a + b

assert f(1) == 11
assert f(1, 20) == 21

# Replace defaults
f.__defaults__ = (99,)
assert f(1) == 100

# Replace with different value
f.__defaults__ = (0,)
assert f(1) == 1

# Remove defaults entirely
f.__defaults__ = None
try:
    f(1)
    assert False, "expected TypeError for missing arg"
except TypeError:
    pass
assert f(1, 2) == 3

# Restore
f.__defaults__ = (10,)
assert f(1) == 11

