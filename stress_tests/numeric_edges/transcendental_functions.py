# -*- coding: utf-8 -*-
# stress test: transcendental_functions
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: math.sqrt of a strictly-negative number raises ValueError, while cmath.sqrt returns an imaginary result. math.sqrt(2) is irrational, so its square is not exactly 2. A JIT that inlines transcendentals must preserve domain checks.
#
# Tags: ['domain-error', 'numeric', 'transcendental']
import math
import cmath
# math.sqrt of a strictly-negative number raises ValueError.
for x in (-1.0, -1e-300, -1e308):
    try:
        math.sqrt(x)
        assert False, "expected ValueError for sqrt(%r)" % (x,)
    except ValueError:
        pass
# math.sqrt(2) is irrational: its square is not exactly 2.
sqrt2 = math.sqrt(2)
assert sqrt2 * sqrt2 != 2
assert abs(sqrt2 * sqrt2 - 2) < 1e-15
assert abs(sqrt2 - 1.4142135623730951) < 1e-15
# cmath.sqrt handles negatives -> imaginary axis.
assert cmath.sqrt(-1) == 1j
assert abs(cmath.sqrt(-4) - 2j) < 1e-15
assert abs(cmath.sqrt(-1 + 0j) - 1j) < 1e-15
# math.log of a non-positive is a domain error.
for x in (-1.0, 0.0):
    try:
        math.log(x)
        assert False, "expected ValueError for log(%r)" % (x,)
    except ValueError:
        pass
# Transcendentals return floats, not ints.
assert type(math.sin(0.0)) is float
assert type(math.exp(1.0)) is float
# Constants are floats (not exact rationals).
assert abs(math.pi - 3.141592653589793) < 1e-15
assert abs(math.e - 2.718281828459045) < 1e-15

