"""Numeric edge case stress tests.

Each test here targets a specific numeric boundary that a JIT compiler
may get wrong if it makes assumptions about integer width, IEEE-754
float semantics, big-int promotion, mixed-type arithmetic, or
transcendental-function domains. The categories covered:

- Integer overflow at the 2**63 (signed int64) and 2**64 (uint64)
  boundaries, where a JIT that boxes small ints as machine words must
  promote to a multi-digit ``PyLong``.
- Arbitrary-precision integer arithmetic (2**1000) which has no
  fixed-width representation at all.
- IEEE-754 edge cases: subnormals, signed zero (-0.0), infinities, NaN
  propagation, and the classic 0.1 + 0.2 != 0.3 precision surprise.
- Mixed int/float and complex arithmetic, where the result type
  depends on the operands and a JIT's type speculation can deopt.
- Division / modulo / power semantics that change result type or sign
  depending on operand signs and the floor-vs-trunc distinction.
- Int<->float conversion precision loss across the 2**53 mantissa
  boundary.
- Transcendental domain errors (math.sqrt of a negative) vs. the
  complex-aware cmath variants.
- Float non-associativity (reordering a sum changes the result) and
  the bool-as-int subclass relationship.

Every source string is self-contained: it imports whatever it needs
and asserts its own post-conditions, so it runs identically under
unmodified CPython.
"""

from __future__ import annotations

import math

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="overflow_2_to_63_boundary",
        category="numeric_edges",
        description=(
            "Cross the signed int64 boundary at 2**63. A JIT that "
            "represents Python ints as int64 must promote to a "
            "multi-digit bigint at exactly this point; arithmetic across "
            "the boundary must stay exact."
        ),
        source='''\
# 2**63 - 1 is INT64_MAX and still fits a signed 64-bit word;
# 2**63 itself is one past INT64_MAX and forces bigint promotion.
below = 2 ** 63 - 1
at = 2 ** 63
above = at + 1
assert below == 9223372036854775807
assert at == 9223372036854775808
assert above == 9223372036854775809
assert (below + 1) == at
assert (at + at) == 2 ** 64
# Negation: -(2**63) would be INT64_MIN, but Python keeps the value exact.
assert (-at) == -9223372036854775808
assert (-at) - 1 == -9223372036854775809
# The transition happens inside a hot loop the JIT may have compiled.
# below + 2 == 2**63 + 1 == above, crossing the int64 boundary mid-loop.
acc = below
for _ in range(2):
    acc = acc + 1
assert acc == above
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "overflow", "bigint", "int64"}),
    ),
    T(
        name="overflow_2_to_64_boundary",
        category="numeric_edges",
        description=(
            "Cross the unsigned int64 boundary at 2**64. Even a JIT that "
            "uses an unsigned 64-bit representation must promote here; "
            "2**64 * 2**64 (== 2**128) has no fixed-width representation."
        ),
        source='''\
below = 2 ** 64 - 1   # UINT64_MAX
at = 2 ** 64
above = 2 ** 64 + 1
assert below == 18446744073709551615
assert at == 18446744073709551616
assert above == 18446744073709551617
assert (below + 1) == at
# Doubling UINT64_MAX crosses deep into bigint territory.
assert (below * 2) == 36893488147419103230
# A 64-bit JIT computing at * at would overflow; Python keeps it exact.
assert at * at == 2 ** 128
# Loop that accumulates across the boundary.
# below + 2 == 2**64 + 1 == above, crossing the uint64 boundary mid-loop.
acc = below
for _ in range(2):
    acc = acc + 1
assert acc == above
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "overflow", "bigint", "uint64"}),
    ),
    T(
        name="bigint_arithmetic_2_to_1000",
        category="numeric_edges",
        description=(
            "Python ints are arbitrary precision. 2**1000 has 1001 bits "
            "and no machine-word representation; all arithmetic, bit "
            "ops, and modular exponentiation must remain exact."
        ),
        source='''\
n = 2 ** 1000
assert n.bit_length() == 1001
assert len(str(n)) == 302            # 2**1000 has 302 decimal digits
# Arithmetic stays exact across huge magnitudes.
assert (n * 2) == 2 ** 1001
assert (n + 1) - n == 1
assert n // (2 ** 500) == 2 ** 500
assert (n * n) == 2 ** 2000
# Bit operations on thousand-bit ints. n == 2**1000 has only bit 1000 set.
assert (n | 1) == n + 1
assert (n & (2 ** 999)) == 0          # bit 999 is NOT set in n
assert (n & (2 ** 1000)) == 2 ** 1000  # bit 1000 IS set in n
# Three-arg pow (modular exponentiation) works on bigints.
assert pow(2, 1000, 10) == 6          # last decimal digit of 2**1000
assert pow(2, 1000, 2 ** 64) == 0
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "bigint", "arbitrary-precision"}),
    ),
    T(
        name="float_subnormal_min",
        category="numeric_edges",
        description=(
            "IEEE-754 subnormal numbers (smallest positive is ~5e-324). "
            "A JIT that flushes subnormals to zero would violate these "
            "assertions; halving the smallest subnormal must underflow "
            "to +0.0 while adding it to 1.0 must round away to 1.0."
        ),
        source='''\
import math
import sys
# Smallest positive subnormal double: 2**-1074 (printed as 5e-324).
sub = 5e-324
assert sub == 2.0 ** -1074
assert sub > 0.0
# Halving it underflows to +0.0.
assert (sub / 2) == 0.0
# Adding to 0.0 is exact (no rounding).
assert (0.0 + sub) == sub
# But adding to 1.0 rounds away (sub is far below the ULP of 1.0).
assert (1.0 + sub) == 1.0
# Gradual underflow: smallest normal * eps == smallest subnormal.
assert (sys.float_info.min * sys.float_info.epsilon) == sub
# Multiplying two subnormals underflows to zero.
assert (sub * sub) == 0.0
# A JIT must not fold `0.0 < sub < sys.float_info.min` to False.
assert 0.0 < sub < sys.float_info.min
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "ieee-754", "subnormal"}),
    ),
    T(
        name="float_negative_zero",
        category="numeric_edges",
        description=(
            "IEEE-754 has two zeros: +0.0 and -0.0. They compare equal "
            "but differ in sign bit, which is observable via copysign, "
            "repr, and atan2. A JIT that canonicalizes -0.0 to +0.0 "
            "would break these."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "ieee-754", "signed-zero"}),
    ),
    T(
        name="float_infinity_arithmetic",
        category="numeric_edges",
        description=(
            "Infinity arithmetic: inf+x==inf, inf-inf==NaN, 1/inf==0. "
            "A JIT that elides overflow checks or assumes finite operands "
            "would miscompute these."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "ieee-754", "infinity", "nan"}),
    ),
    T(
        name="float_nan_semantics",
        category="numeric_edges",
        description=(
            "NaN is not equal to anything, including itself, and "
            "propagates through arithmetic. A JIT that folds NaN "
            "comparisons or treats NaN as a normal value would break "
            "these invariants."
        ),
        source='''\
import math
nan = float('nan')
# Defining property: NaN is not equal to itself.
assert nan != nan
assert not (nan == nan)
assert not (nan < 0.0)
assert not (nan > 0.0)
assert not (nan == 0.0)
assert not (nan <= 0.0)
assert not (nan >= 0.0)
assert math.isnan(nan)
# NaN propagates through arithmetic.
assert math.isnan(nan + 1.0)
assert math.isnan(nan * 0.0)
assert math.isnan(nan - nan)
# Containers use PyObject_RichCompareBool, which short-circuits on
# identity before calling __eq__. The SAME nan object IS found (via
# identity) even though nan == nan is False; distinct nan objects are not.
same = [nan, nan]
assert same.count(nan) == 2          # identity fast path counts both
assert nan in same                   # identity fast path
nan_other = float('nan')
assert nan_other not in same         # different objects, == is False
assert nan not in [0.0, 1.0]        # 0.0/1.0 are not nan, == is False
# math.isnan is the only reliable NaN detector.
assert any(math.isnan(x) for x in same)
# A NaN with a sign bit is still NaN and still unequal to itself.
nan2 = float('-nan')
assert math.isnan(nan2)
assert nan2 != nan2
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "ieee-754", "nan"}),
    ),
    T(
        name="float_precision_0_1_plus_0_2",
        category="numeric_edges",
        description=(
            "The canonical IEEE-754 surprise: 0.1 + 0.2 != 0.3 in binary "
            "float, and accumulating 0.1 ten times drifts away from 1.0. "
            "A JIT that rewrites float sums must preserve IEEE rounding "
            "(or use math.fsum for correct rounding)."
        ),
        source='''\
import math
from decimal import Decimal
# The canonical surprise.
assert (0.1 + 0.2) != 0.3
assert (0.1 + 0.2) == 0.30000000000000004
# Decimal arithmetic is exact for decimal fractions.
assert Decimal('0.1') + Decimal('0.2') == Decimal('0.3')
# Accumulating 0.1 ten times does not yield exactly 1.0.
acc = 0.0
for _ in range(10):
    acc += 0.1
assert acc != 1.0
assert acc == 0.9999999999999999
# A tiny addend is lost against a large value.
assert (1e16 + 1.0) - 1e16 == 0.0
# math.fsum recovers the correctly-rounded sum.
assert math.fsum([0.1] * 10) == 1.0
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "ieee-754", "precision", "rounding"}),
    ),
    T(
        name="mixed_int_float_arithmetic",
        category="numeric_edges",
        description=(
            "int + float promotes to float, and large ints coerce to "
            "float (losing precision). A JIT that speculates int+int "
            "must deopt when a float appears, and must not assume "
            "int+float yields an int."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "promotion", "mixed-types"}),
    ),
    T(
        name="complex_arithmetic",
        category="numeric_edges",
        description=(
            "Complex numbers: addition, multiplication, absolute value, "
            "division, and conjugation. A JIT that only specializes on "
            "real numeric types must fall back correctly for complex."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "complex"}),
    ),
    T(
        name="division_true_vs_floor",
        category="numeric_edges",
        description=(
            "True division (/) always returns float; floor division (//) "
            "on ints returns int and rounds toward -inf (not toward "
            "zero). A JIT that conflates the two would miscompute "
            "negative operands."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "division", "floor"}),
    ),
    T(
        name="modulo_negative_operands",
        category="numeric_edges",
        description=(
            "Python's % follows the sign of the divisor (not the "
            "dividend), so -7 % 3 == 2 and 7 % -3 == -2. A JIT that uses "
            "the C/REM semantics (sign of dividend) would miscompute."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "modulo", "sign"}),
    ),
    T(
        name="power_int_to_float_transition",
        category="numeric_edges",
        description=(
            "The ** operator changes result type with the exponent: "
            "int**positive_int stays int, int**negative_int becomes "
            "float, and a negative base with a fractional exponent "
            "becomes complex. A JIT must dispatch on operand types."
        ),
        source='''\
import math
# 2 ** 0 stays int.
assert 2 ** 0 == 1
assert type(2 ** 0) is int
# 2 ** positive int stays int (arbitrary precision).
assert type(2 ** 10) is int
assert 2 ** 10 == 1024
# 2 ** negative int -> float.
assert 2 ** -1 == 0.5
assert type(2 ** -1) is float
assert type(2 ** -2) is float
# 0 ** 0 == 1 by definition.
assert 0 ** 0 == 1
# Negative base with a fractional exponent -> complex.
result = (-1) ** 0.5
assert isinstance(result, complex)
assert abs(result.imag - 1.0) < 1e-12
# 10 ** 0.5 -> float.
assert type(10 ** 0.5) is float
assert abs((10 ** 0.5) ** 2 - 10.0) < 1e-12
# Three-arg pow (modular exponentiation) only accepts ints.
assert pow(2, 10, 1000) == 24
assert type(pow(2, 10, 1000)) is int
assert pow(2, -1, 5) == 3      # modular inverse of 2 mod 5 (2*3 == 6 == 1)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "power", "type-transition"}),
    ),
    T(
        name="bitops_large_ints",
        category="numeric_edges",
        description=(
            "Bitwise operations on ints far larger than a machine word "
            "(2**100 | 2**200). A JIT that lowers these to native CPU "
            "instructions must fall back to bigint algorithms here."
        ),
        source='''\
a = 2 ** 100
b = 2 ** 200
# No overlapping bits -> OR is the sum, AND is zero.
assert (a | b) == (2 ** 100 + 2 ** 200)
assert (a & b) == 0
assert (b ^ a) == (2 ** 200 + 2 ** 100)
# Shifts.
assert (b >> 100) == (2 ** 100)
assert (a << 100) == (2 ** 200)
assert (2 ** 200 >> 200) == 1
# Bitwise NOT: ~x == -x - 1 (two's complement, arbitrary width).
assert ~a == -(2 ** 100) - 1
assert ~0 == -1
assert ~(-1) == 0
# bit_length.
assert a.bit_length() == 101
assert b.bit_length() == 201
assert (2 ** 100 - 1).bit_length() == 100
# Combine widely-spaced bits.
mask = 0
for i in (0, 64, 128, 200, 500):
    mask |= (1 << i)
assert mask.bit_length() == 501
assert mask == sum(1 << i for i in (0, 64, 128, 200, 500))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="cold",
                         tags={"numeric", "bigint", "bitops"}),
    ),
    T(
        name="left_shift_creates_bigint",
        category="numeric_edges",
        description=(
            "1 << 64 and 1 << 128 cross from machine-word ints into "
            "bigint territory. Right shift on negative ints is arithmetic "
            "(rounds toward -inf), not logical."
        ),
        source='''\
# 1 << 64 crosses into bigint (would overflow uint64).
assert (1 << 64) == 2 ** 64
assert (1 << 64) == 18446744073709551616
# 1 << 128 is well beyond machine-word range.
assert (1 << 128) == 2 ** 128
assert (1 << 128).bit_length() == 129
# Shifting by zero is a no-op.
assert (5 << 0) == 5
# Shifting a value already in bigint range.
big = 1 << 100
assert (big << 100) == (1 << 200)
# Right shift on negative ints is arithmetic (rounds toward -inf).
assert (-1) >> 1 == -1
assert (-2) >> 1 == -1
assert (-3) >> 1 == -2
assert (-4) >> 1 == -2
# Large left shift inside a loop.
v = 1
for _ in range(10):
    v <<= 8
assert v == 2 ** 80
# Shifting builds the same value as exponentiation.
assert (1 << 64) == (2 ** 64)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="cold",
                         tags={"numeric", "bigint", "shift"}),
    ),
    T(
        name="float_to_int_truncation",
        category="numeric_edges",
        description=(
            "int() truncates toward zero (so int(-3.7) == -3), while "
            "math.floor rounds toward -inf (so floor(-3.7) == -4). "
            "round() uses banker's rounding (round half to even). A JIT "
            "that confuses truncation with floor would miscompute "
            "negatives."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "conversion", "truncation", "rounding"}),
    ),
    T(
        name="int_to_float_precision_loss",
        category="numeric_edges",
        description=(
            "Above 2**53 not all integers are representable as floats: "
            "float(2**53 + 1) == float(2**53). A JIT that widens int to "
            "float without checking the mantissa width would silently "
            "drop low bits."
        ),
        source='''\
# 2**53 is the boundary: above it, not all integers are representable.
assert 2 ** 53 == 9007199254740992
# 2**53 is exactly representable; 2**53 + 1 is NOT.
assert float(2 ** 53) == 9007199254740992.0
assert float(2 ** 53 + 1) == float(2 ** 53)    # the +1 is rounded away
assert float(2 ** 53 + 1) == 9007199254740992.0
assert float(2 ** 53 + 2) == 9007199254740994.0  # +2 survives (even)
# Round-trip int(float(x)) loses the low bit.
assert int(float(2 ** 53 + 1)) == 2 ** 53
assert int(float(2 ** 53 + 3)) == 2 ** 53 + 4    # rounds to nearest even
# Below 2**53 everything round-trips exactly.
for k in (0, 1, 2, 100, 2 ** 52, 2 ** 53 - 1):
    assert int(float(k)) == k
# Going much larger: the float skips many integers.
huge = 2 ** 70
assert float(huge + 1) == float(huge)            # +1 invisible at this scale
assert float(huge) + 1.0 == float(huge)         # adding 1.0 does nothing
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "conversion", "precision", "mantissa"}),
    ),
    T(
        name="transcendental_functions",
        category="numeric_edges",
        description=(
            "math.sqrt of a strictly-negative number raises ValueError, "
            "while cmath.sqrt returns an imaginary result. math.sqrt(2) "
            "is irrational, so its square is not exactly 2. A JIT that "
            "inlines transcendentals must preserve domain checks."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="cold",
                         tags={"numeric", "transcendental", "domain-error"}),
    ),
    T(
        name="float_addition_non_associative",
        category="numeric_edges",
        description=(
            "Float addition is not associative: reordering operands "
            "changes the result. A JIT that reassociates sums for "
            "vectorization would change observable results; math.fsum "
            "and Kahan summation recover the correct total."
        ),
        source='''\
import math
# Reordering operands changes the result.
a, b, c = 1.0, 1e16, -1e16
left = (a + b) + c      # 1.0 is absorbed into 1e16, then cancels -> 0.0
right = a + (b + c)     # 1e16 + (-1e16) cancels exactly first -> 1.0
assert left == 0.0
assert right == 1.0
assert left != right
# A tiny addend is lost against a large value.
assert (1e16 + 1.0) == 1e16
assert (1e16 + 1.0) - 1e16 == 0.0
# Naive summation of 0.1 x10 drifts; math.fsum is correctly rounded.
naive = 0.0
for _ in range(10):
    naive += 0.1
assert naive != 1.0
assert naive == 0.9999999999999999
assert math.fsum([0.1] * 10) == 1.0
# Kahan compensated summation recovers the lost precision.
def kahan(values):
    total = 0.0
    comp = 0.0
    for v in values:
        y = v - comp
        t = total + y
        comp = (t - total) - y
        total = t
    return total
assert kahan([0.1] * 10) == 1.0
# Summation order over mixed magnitudes changes the total.
seq = [1e16, 1.0, -1e16, 1.0]
s_left_to_right = 0.0
for v in seq:
    s_left_to_right += v
# Pairing the 1e16 terms first cancels them exactly, leaving 1.0 + 1.0.
s_paired = (1e16 + (-1e16)) + (1.0 + 1.0)
assert s_left_to_right == 1.0
assert s_paired == 2.0
assert s_left_to_right != s_paired
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="cold",
                         tags={"numeric", "ieee-754", "associativity", "fsum"}),
    ),
    T(
        name="bool_is_int_subclass",
        category="numeric_edges",
        description=(
            "bool is a subclass of int (True == 1, False == 0) but is a "
            "distinct singleton type. Arithmetic promotes bool to int, "
            "bitwise ops keep bool, and bools work as list indices. A "
            "JIT that treats bool and int as identical would miss the "
            "type transitions."
        ),
        source='''\
# bool is a subclass of int: True == 1, False == 0.
assert isinstance(True, int)
assert isinstance(False, int)
assert issubclass(bool, int)
assert True == 1
assert False == 0
# Arithmetic promotes bool to int.
assert True + True == 2
assert type(True + True) is int
assert True * 3 == 3
assert False * 99 == 0
assert 1 + True == 2
assert 10 - False == 10
# bool values are singletons (identity).
assert True is True
assert False is False
# But the int 1 is NOT the singleton True (different objects).
one = 1
zero = 0
assert one is not True
assert zero is not False
# Bools behave as indices.
assert [10, 20, 30][True] == 20
assert [10, 20, 30][False] == 10
# sum() over bools counts the Trues.
assert sum([True, False, True, True]) == 3
assert sum([True, True]) == 2
# Bitwise ops on bools return bools (bool defines its own __and__/__or__).
assert (True & False) is False
assert (True | False) is True
assert (True & True) is True
# Negation promotes to int.
assert -True == -1
assert type(-True) is int
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"numeric", "bool", "subclass", "promotion"}),
    ),
]
