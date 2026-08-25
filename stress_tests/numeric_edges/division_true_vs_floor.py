# -*- coding: utf-8 -*-
# stress test: division_true_vs_floor
# category: numeric_edges
#
# Target: True division (/) always returns float; floor division (//) on ints returns int and rounds toward -inf (not toward zero). A JIT that conflates the two would miscompute negative operands.
#
# Tags: ['division', 'floor', 'numeric']
# True division (/) always returns float.
assert 7 / 2 == 3.5
assert type(7 / 2) is float
assert 6 / 2 == 3.0
assert type(6 / 2) is float
# Floor division (//) on ints returns int, rounding toward -inf.
assert 7 // 2 == 3
assert type(7 // 2) is int
assert -7 // 2 == -4          # floor(-3.5) == -4, NOT -3 (truncation)
assert 7 // -2 == -4
assert -7 // -2 == 3
# divmod is consistent with //.
assert divmod(7, 2) == (3, 1)
assert divmod(-7, 2) == (-4, 1)
assert divmod(7, -2) == (-4, -1)
# Floor division on floats returns float.
assert 7.0 // 2 == 3.0
assert type(7.0 // 2) is float
assert -7.5 // 2 == -4.0
# The identity (a // b) * b + (a % b) == a must hold for every sign combo.
for a, b in [(7, 2), (-7, 2), (7, -2), (-7, -2), (100, 7)]:
    assert (a // b) * b + (a % b) == a

