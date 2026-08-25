# -*- coding: utf-8 -*-
# stress test: float_to_int_truncation
# category: numeric_edges
#
# Target: int() truncates toward zero (so int(-3.7) == -3), while math.floor rounds toward -inf (so floor(-3.7) == -4). round() uses banker's rounding (round half to even). A JIT that confuses truncation with floor would miscompute negatives.
#
# Tags: ['conversion', 'numeric', 'rounding', 'truncation']
import math
# int() truncates toward zero.
assert int(3.7) == 3
assert int(-3.7) == -3        # NOT -4 (toward zero, not floor)
assert int(3.0) == 3
assert int(-3.0) == -3
assert int(0.999999) == 0
assert int(-0.999999) == 0
assert int(1e20) == 10 ** 20  # 10**20 happens to be exactly representable
# math.floor rounds toward -inf (differs from int() for negatives).
assert math.floor(3.7) == 3
assert math.floor(-3.7) == -4
assert math.ceil(3.7) == 4
assert math.ceil(-3.7) == -3
# math.trunc matches int().
assert math.trunc(3.7) == int(3.7)
assert math.trunc(-3.7) == int(-3.7)
# round() uses banker's rounding (round half to even).
assert round(2.5) == 2
assert round(3.5) == 4
assert round(0.5) == 0
assert round(1.5) == 2
assert round(-0.5) == 0
assert round(-1.5) == -2
# The classic 2.675 float-surprise (2.675 is stored slightly below).
assert round(2.675, 2) == 2.67

