# -*- coding: utf-8 -*-
# stress test: set_algebra_across_reprs
# category: container_repr
#
# Target: Set operations (difference, intersection, symmetric difference, union) between sets and frozensets of varying sizes. The JIT must handle the different internal representations and the from-set / from-frozenset source types.
#
# Tags: ['algebra', 'container', 'frozenset', 'set']
s1 = set(range(100))
s2 = set(range(50, 150))
s3 = set(range(0, 200, 2))  # even numbers

# Difference
diff = s1 - s2
assert diff == set(range(50))

# Intersection
inter = s1 & s2
assert inter == set(range(50, 100))

# Symmetric difference
sym = s1 ^ s2
assert sym == set(range(50)) | set(range(100, 150))

# Union
uni = s1 | s3
assert uni == set(range(0, 100)) | set(range(0, 200, 2))

# Mixed set / frozenset
fs = frozenset(range(75, 125))
inter2 = s1 & fs
assert inter2 == set(range(75, 100))
diff2 = fs - s1
assert diff2 == set(range(100, 125))

# In-place operations
base = set(range(20))
base &= set(range(10, 30))
assert base == set(range(10, 20))
base |= set(range(30, 40))
assert base == set(range(10, 20)) | set(range(30, 40))
base -= set(range(15, 35))
assert base == {10, 11, 12, 13, 14, 35, 36, 37, 38, 39}

