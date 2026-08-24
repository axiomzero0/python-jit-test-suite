# -*- coding: utf-8 -*-
# stress test: float_negative_zero
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: IEEE-754 has two zeros: +0.0 and -0.0. They compare equal but differ in sign bit, which is observable via copysign, repr, and atan2. A JIT that canonicalizes -0.0 to +0.0 would break these.
#
# Tags: ['ieee-754', 'numeric', 'signed-zero']
import math
nz = -0.0
pz = 0.0
# -0.0 == 0.0 under value equality.
assert nz == pz
# But the sign bit is preserved and observable.
assert math.copysign(1.0, nz) == -1.0
assert math.copysign(1.0, pz) == 1.0
# repr/str distinguish them.
assert repr(nz) == '-0.0'
assert repr(pz) == '0.0'
assert str(nz) == '-0.0'
# -0.0 arises naturally from multiplication with a negative operand.
assert math.copysign(1.0, -1.0 * 0.0) == -1.0
assert math.copysign(1.0, 1.0 * 0.0) == 1.0
# IEEE rule: -0.0 + +0.0 == +0.0, but -0.0 + -0.0 == -0.0.
assert math.copysign(1.0, nz + pz) == 1.0
assert math.copysign(1.0, nz + nz) == -1.0
# atan2 distinguishes the sign of zero.
assert math.copysign(1.0, math.atan2(-0.0, 1.0)) == -1.0
assert math.copysign(1.0, math.atan2(0.0, 1.0)) == 1.0

