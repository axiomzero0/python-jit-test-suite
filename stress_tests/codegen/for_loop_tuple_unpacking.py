# -*- coding: utf-8 -*-
# stress test: for_loop_tuple_unpacking
# category: codegen
# opt_state: (runs across all 6 states)
#
# Target: A for loop unpacks each iteration's value into multiple names, including starred targets and nested tuples. The JIT must UNPACK each item before binding.
#
# Tags: ['codegen', 'for-loop', 'unpack']
pairs = [(1, 'a'), (2, 'b'), (3, 'c')]
result = {}
for k, v in pairs:
    result[k] = v
assert result == {1: 'a', 2: 'b', 3: 'c'}

# Starred unpacking in loop
quads = [(1, 2, 3, 4), (5, 6, 7, 8)]
collected = []
for a, *middle, d in quads:
    collected.append((a, middle, d))
assert collected[0] == (1, [2, 3], 4)
assert collected[1] == (5, [6, 7], 8)

# Nested unpacking
nested = [((1, 2), 3), ((4, 5), 6)]
flat = []
for (a, b), c in nested:
    flat.append((a, b, c))
assert flat == [(1, 2, 3), (4, 5, 6)]

# Nested with star
nested_star = [((1, 2, 3), 4), ((5, 6, 7, 8), 9)]
flat_star = []
for (a, *rest), last in nested_star:
    flat_star.append((a, rest, last))
assert flat_star[0] == (1, [2, 3], 4)
assert flat_star[1] == (5, [6, 7, 8], 9)

# Dict iteration with unpacking
d = {('x', 1): 'a', ('y', 2): 'b'}
for (name, idx), val in d.items():
    assert isinstance(name, str)
    assert isinstance(idx, int)

# enumerate with nested unpacking
for i, (a, b) in enumerate([(1, 2), (3, 4)]):
    assert (i, a, b) in [(0, 1, 2), (1, 3, 4)]

