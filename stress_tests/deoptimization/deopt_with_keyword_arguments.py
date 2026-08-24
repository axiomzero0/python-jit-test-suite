# -*- coding: utf-8 -*-
# stress test: deopt_with_keyword_arguments
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Function called with keyword args. Deopt in the callee. The argument binding must be correctly reconstructed.
#
# Tags: ['argument-binding', 'deopt', 'kwargs']
def f(a, b, c=10, d=20):
    if a == 500:
        return "trigger"
    return a + b + c + d

def caller():
    results = []
    for i in range(1000):
        results.append(f(i, i*2, c=i*3, d=i*4))
    return results

r = caller()
assert r[0] == 0 + 0 + 0 + 0
assert r[499] == 499 + 998 + 1497 + 1996
assert r[500] == "trigger"
assert r[501] == 501 + 1002 + 1503 + 2004

