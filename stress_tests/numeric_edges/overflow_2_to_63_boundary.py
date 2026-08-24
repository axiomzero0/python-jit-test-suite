# -*- coding: utf-8 -*-
# stress test: overflow_2_to_63_boundary
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: Cross the signed int64 boundary at 2**63. A JIT that represents Python ints as int64 must promote to a multi-digit bigint at exactly this point; arithmetic across the boundary must stay exact.
#
# Tags: ['bigint', 'int64', 'numeric', 'overflow']
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

