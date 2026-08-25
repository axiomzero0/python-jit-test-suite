# -*- coding: utf-8 -*-
# stress test: operator_precedence_evaluation_order
# category: codegen
#
# Target: A complex expression mixes arithmetic, power, unary, bitwise, and shift operators. The JIT must emit operations in CPython's documented precedence order, evaluating each operand exactly once.
#
# Tags: ['binop', 'codegen', 'precedence']
# Arithmetic precedence: ** binds tighter than *, which binds tighter than +/-
result = 2 + 3 * 4 ** 2 - 1
# 4**2 = 16; 3*16 = 48; 2+48 = 50; 50-1 = 49
assert result == 49

# Unary minus
x = -5
y = -x * 2 + 3
# -x = 5; 5*2 = 10; 10+3 = 13
assert y == 13

# Bitwise precedence: & higher than |, ^ between
r = 1 | 2 & 3  # 2 & 3 = 2; 1 | 2 = 3
assert r == 3
r = 5 ^ 1 | 2  # 5 ^ 1 = 4; 4 | 2 = 6
assert r == 6

# Shifts: + binds tighter than <<
r = 1 + 2 << 3  # (1+2) << 3 = 24
assert r == 24
r = 16 >> 1 + 1  # 16 >> (1+1) = 16 >> 2 = 4
assert r == 4

# Chained comparison with all operators distinct
a, b, c = 1, 2, 3
assert -1 < a < b < c < 4

# Mixed comparison and arithmetic
r = 1 + 1 == 2 < 3
assert r is True

# Power is right-associative
r = 2 ** 3 ** 2  # 2 ** (3 ** 2) = 2 ** 9 = 512
assert r == 512

# Ternary has lower precedence than most binary ops
r = 1 if True else 2 + 3  # parses as (1 if True else 2) + 3
# Actually: `1 if True else (2 + 3)` — ternary is lowest precedence
# so the entire RHS is the false branch. Verify in CPython:
assert (1 if True else 2 + 3) == 1
assert (1 if False else 2 + 3) == 5

