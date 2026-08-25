# -*- coding: utf-8 -*-
# stress test: guard_type_list_to_tuple
# category: guard_failures
#
# Target: Type guard `isinstance(x, list)` fails when x is tuple.
#
# Tags: ['guard', 'index', 'type']
def first(x):
    return x[0]

for _ in range(1000):
    first([1, 2, 3])

assert first((10, 20, 30)) == 10
assert first("hello") == "h"
assert first(range(5)) == 0

