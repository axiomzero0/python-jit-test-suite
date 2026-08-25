# -*- coding: utf-8 -*-
# stress test: guard_int_to_bigint
# category: guard_failures
#
# Target: Int size guard `fits in 64 bits` fails on overflow.
#
# Tags: ['bigint', 'guard', 'int', 'overflow']
def mul(x, y):
    return x * y

for _ in range(1000):
    mul(2, 3)

# Guard fails: overflow
assert mul(2**32, 2**32) == 2**64
assert mul(2**63, 2) == 2**64
assert mul(2**100, 2**100) == 2**200

# Back to small
assert mul(2, 3) == 6

