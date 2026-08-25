# -*- coding: utf-8 -*-
# stress test: complex_arithmetic
# category: numeric_edges
#
# Target: Complex numbers: addition, multiplication, absolute value, division, and conjugation. A JIT that only specializes on real numeric types must fall back correctly for complex.
#
# Tags: ['complex', 'numeric']
a = 1 + 2j
b = 3 + 4j
assert a + b == (4 + 6j)
assert a - b == (-2 - 2j)
# (1+2j)*(3+4j) = (1*3 - 2*4) + (1*4 + 2*3)j = -5 + 10j
assert a * b == (-5 + 10j)
assert abs(3 + 4j) == 5.0
assert type(abs(3 + 4j)) is float
# Components are floats.
assert (1.0 + 2.0j).real == 1.0
assert type((1.0 + 2.0j).real) is float
# Division.
assert (1 + 0j) / (2 + 0j) == 0.5 + 0j
# Conjugate.
assert (3 + 4j).conjugate() == (3 - 4j)
# complex ** int
assert (1 + 1j) ** 2 == 2j
# Mixing complex with float.
assert (1 + 2j) + 1.0 == (2 + 2j)
# Equality compares exactly (bit-for-bit).
assert (0.1 + 0.2j) == (0.1 + 0.2j)

