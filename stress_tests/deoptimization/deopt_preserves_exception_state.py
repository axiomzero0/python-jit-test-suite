# -*- coding: utf-8 -*-
# stress test: deopt_preserves_exception_state
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Exception is raised in optimized code. Deopt must preserve the exception object so it can be caught by a try/except in the caller.
#
# Tags: ['deopt', 'exception', 'preserve']
def raiser(x):
    if x == 500:
        raise ValueError("mid")
    return x

def caller():
    total = 0
    for i in range(1000):
        try:
            total += raiser(i)
        except ValueError:
            total -= 1  # one ValueError caught at i=500
    return total

r = caller()
# When raiser(500) raises: total += raiser(500) doesn't execute, and
# total -= 1 runs. So we lose 500 from the sum and subtract 1.
expected = sum(range(500)) + sum(range(501, 1000)) - 1
assert r == expected, f"r={r}, expected={expected}"

