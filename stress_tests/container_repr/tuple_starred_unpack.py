# -*- coding: utf-8 -*-
# stress test: tuple_starred_unpack
# category: container_repr
# opt_state: (runs across all 6 states)
#
# Target: Tuples of varying sizes are unpacked with starred targets, including nested unpacking. The JIT must support the full UNPACK_EX bytecode (PEP 3132) including the empty-middle and all-in-middle edge cases.
#
# Tags: ['UNPACK_EX', 'container', 'tuple', 'unpack']
t = (1, 2, 3, 4, 5)
a, b, *c, d = t
assert a == 1
assert b == 2
assert c == [3, 4]
assert d == 5

# Empty middle
a, *b, c = (1, 2)
assert a == 1
assert b == []
assert c == 2

# All in middle
*a, = (1, 2, 3)
assert a == [1, 2, 3]

# Single trailing star
a, b, *c = (1, 2)
assert (a, b, c) == (1, 2, [])

# Nested tuple unpacking
t2 = ((1, 2), (3, 4), (5, 6))
(a, b), (c, d), (e, f) = t2
assert (a, b, c, d, e, f) == (1, 2, 3, 4, 5, 6)

# Nested with star
t3 = ((1, 2, 3), (4, 5, 6, 7))
(a, *b), (c, *d) = t3
assert a == 1
assert b == [2, 3]
assert c == 4
assert d == [5, 6, 7]

# Swap via unpacking
x, y = 10, 20
x, y = y, x
assert (x, y) == (20, 10)

