# -*- coding: utf-8 -*-
# stress test: modulo_negative_operands
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: Python's % follows the sign of the divisor (not the dividend), so -7 % 3 == 2 and 7 % -3 == -2. A JIT that uses the C/REM semantics (sign of dividend) would miscompute.
#
# Tags: ['modulo', 'numeric', 'sign']
# Python's % follows the sign of the divisor.
assert 7 % 3 == 1
assert -7 % 3 == 2            # divisor positive -> result in [0, 3)
assert 7 % -3 == -2          # divisor negative -> result in (-3, 0]
assert -7 % -3 == -1
# Float modulo also follows the divisor's sign.
assert -7.5 % 3.0 == 1.5
assert 7.5 % -3.0 == -1.5
# The invariant (a // b) * b + (a % b) == a holds for all sign combos.
for a in range(-12, 13):
    for b in (-7, -3, -2, -1, 1, 2, 3, 7):
        assert (a // b) * b + (a % b) == a
# divmod's remainder matches % for all sign combos.
assert divmod(-7, 3)[1] == -7 % 3
assert divmod(7, -3)[1] == 7 % -3
# Modulo by zero raises ZeroDivisionError (for both int and float zero).
for b in (0, 0.0):
    try:
        7 % b
        assert False, "expected ZeroDivisionError"
    except ZeroDivisionError:
        pass

