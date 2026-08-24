# -*- coding: utf-8 -*-
# stress test: no_escape_scalar_replace
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: A small mutable object is constructed inside a function, its fields are read and mutated, and only a derived primitive value escapes. A correct escape analysis can scalar-replace the object (no heap allocation is needed). A buggy analysis that fails to track the field writes would observe stale field values and produce wrong results.
#
# Tags: ['allocation-elimination', 'escape-analysis', 'scalar-replacement']
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x = x
        self.y = y

def translate(p, dx, dy):
    # p never escapes translate(); JIT can scalar-replace it.
    return (p.x + dx, p.y + dy)

def work(n):
    results = []
    for i in range(n):
        # Each Point is local to this iteration; it never leaks.
        p = Point(i, i * 2)
        results.append(translate(p, 1, 1))
    return results

r = work(100)
assert len(r) == 100
assert r[0] == (1, 1)
assert r[50] == (51, 101)
assert r[99] == (100, 199)

# Determinism: re-running must yield identical results.
r2 = work(100)
assert r == r2

