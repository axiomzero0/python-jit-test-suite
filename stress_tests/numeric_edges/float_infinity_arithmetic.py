# -*- coding: utf-8 -*-
# stress test: float_infinity_arithmetic
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: Infinity arithmetic: inf+x==inf, inf-inf==NaN, 1/inf==0. A JIT that elides overflow checks or assumes finite operands would miscompute these.
#
# Tags: ['ieee-754', 'infinity', 'nan', 'numeric']
import math
inf = float('inf')
ninf = float('-inf')
assert inf + 1 == inf
assert inf - 1 == inf
assert inf * 2 == inf
assert inf * -1 == ninf
assert ninf + ninf == ninf
# inf - inf is the indeterminate NaN.
nan = inf - inf
assert math.isnan(nan)
assert nan != nan
# 1.0 / inf underflows to 0.0, preserving sign.
assert (1.0 / inf) == 0.0
assert math.copysign(1.0, 1.0 / inf) == 1.0
assert math.copysign(1.0, -1.0 / inf) == -1.0
# Comparisons.
assert inf > 1e308
assert ninf < -1e308
assert max(inf, 1) == inf
assert min(inf, 1) == 1
# abs() preserves the magnitude.
assert abs(inf) == inf
assert abs(ninf) == inf

