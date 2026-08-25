# -*- coding: utf-8 -*-
# stress test: mixed_int_float_arithmetic
# category: numeric_edges
#
# Target: int + float promotes to float, and large ints coerce to float (losing precision). A JIT that speculates int+int must deopt when a float appears, and must not assume int+float yields an int.
#
# Tags: ['mixed-types', 'numeric', 'promotion']
# int + float promotes to float.
r = 1 + 2.0
assert r == 3.0
assert type(r) is float
# int * float
assert type(2 * 3.0) is float
assert 2 * 3.0 == 6.0
# Large int + float: the int is converted to float (may lose precision).
big_int = 2 ** 60
big_sum = big_int + 1.0
assert type(big_sum) is float
assert big_sum == float(2 ** 60)
# int ** float -> float
assert type(2 ** 1.0) is float
assert 2 ** 1.0 == 2.0
# float ** int -> float
assert type(2.0 ** 3) is float
assert 2.0 ** 3 == 8.0
# True division always yields float, even for evenly divisible ints.
assert type(6 / 2) is float
assert 6 / 2 == 3.0
# But floor division preserves the int type for int operands.
assert type(6 // 2) is int
assert 6 // 2 == 3

