# -*- coding: utf-8 -*-
# stress test: register_pressure_from_inlined
# category: register_alloc
# opt_state: (runs across all 6 states)
#
# Target: A function is called multiple times in close succession. If the JIT inlines each call, the combined locals of all the inlined copies create high register pressure. A buggy allocator that didn't account for the inlined frames' locals would either fail to inline (missed optimization) or spill incorrectly and corrupt values.
#
# Tags: ['caller-saved', 'inlining', 'pressure', 'register-alloc']
def inner(a, b, c, d, e):
    # Five parameters + two locals + return value.
    s = a + b
    t = c + d
    u = s + t
    return u + e

def outer(x):
    # Three inlined calls; their locals all live simultaneously.
    p = inner(x, x + 1, x + 2, x + 3, x + 4)
    q = inner(x * 2, x * 2 + 1, x * 2 + 2, x * 2 + 3, x * 2 + 4)
    r = inner(x * 3, x * 3 + 1, x * 3 + 2, x * 3 + 3, x * 3 + 4)
    return p + q + r

# Reference implementation (no inlining) for cross-checking.
def ref_inner(a, b, c, d, e):
    return ((a + b) + (c + d)) + e

def ref_outer(x):
    return (ref_inner(x, x + 1, x + 2, x + 3, x + 4) +
            ref_inner(x * 2, x * 2 + 1, x * 2 + 2, x * 2 + 3, x * 2 + 4) +
            ref_inner(x * 3, x * 3 + 1, x * 3 + 2, x * 3 + 3, x * 3 + 4))

assert outer(10) == ref_outer(10)
assert outer(0) == ref_outer(0)
assert outer(-5) == ref_outer(-5)
assert outer(100) == ref_outer(100)

