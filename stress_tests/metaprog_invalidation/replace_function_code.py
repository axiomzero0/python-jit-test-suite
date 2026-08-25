# -*- coding: utf-8 -*-
# stress test: replace_function_code
# category: metaprog_invalidation
#
# Target: A function's __code__ is replaced with the code of another function. Calls to the original name must execute the new bytecode. The JIT cannot cache the original code pointer.
#
# Tags: ['code-object', 'function', 'invalidation']
def f():
    return 1

def g():
    return 2

assert f() == 1
assert g() == 2

# Swap code
original_code = f.__code__
f.__code__ = g.__code__
assert f() == 2
assert g() == 2  # g is unaffected

# Swap back
f.__code__ = original_code
assert f() == 1

# Now swap with a function that takes an argument
def h(x):
    return x * 10

f.__code__ = h.__code__
assert f(5) == 50

