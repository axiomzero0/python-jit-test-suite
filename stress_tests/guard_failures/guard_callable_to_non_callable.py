# -*- coding: utf-8 -*-
# stress test: guard_callable_to_non_callable
# category: guard_failures
# opt_state: (runs across all 6 states)
#
# Target: Callable guard fails when a non-callable is passed.
#
# Tags: ['callable', 'guard']
def f():
    return 42

def call(g):
    return g()

for _ in range(1000):
    call(f)

# Guard fails: non-callable
try:
    call(42)
    assert False
except TypeError:
    pass

assert call(f) == 42

