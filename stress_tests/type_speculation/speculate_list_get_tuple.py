# -*- coding: utf-8 -*-
# stress test: speculate_list_get_tuple
# category: type_speculation
# opt_state: (runs across all 6 states)
#
# Target: JIT speculates `x[0]` is a list indexing op after seeing lists. Then a tuple is passed. The deopt must reconstruct the correct tuple-indexing semantics (which differ in error messages and negative index handling).
#
# Tags: ['container', 'type-speculation']
def first(x):
    return x[0]

lists = [[i] for i in range(100)]
for l in lists:
    first(l)

# Now pass tuples
tuples = [(i,) for i in range(100)]
for t in tuples:
    first(t)

# And strings
first("hello")

assert first([10, 20]) == 10
assert first((10, 20)) == 10
assert first("hello") == "h"

