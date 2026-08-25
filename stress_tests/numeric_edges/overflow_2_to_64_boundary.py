# -*- coding: utf-8 -*-
# stress test: overflow_2_to_64_boundary
# category: numeric_edges
#
# Target: Cross the unsigned int64 boundary at 2**64. Even a JIT that uses an unsigned 64-bit representation must promote here; 2**64 * 2**64 (== 2**128) has no fixed-width representation.
#
# Tags: ['bigint', 'numeric', 'overflow', 'uint64']
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

