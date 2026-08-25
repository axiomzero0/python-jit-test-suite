# -*- coding: utf-8 -*-
# stress test: bigint_arithmetic_2_to_1000
# category: numeric_edges
#
# Target: Python ints are arbitrary precision. 2**1000 has 1001 bits and no machine-word representation; all arithmetic, bit ops, and modular exponentiation must remain exact.
#
# Tags: ['arbitrary-precision', 'bigint', 'numeric']
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

