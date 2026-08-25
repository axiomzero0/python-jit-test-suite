# -*- coding: utf-8 -*-
# stress test: escape_via_function_return
# category: escape_analysis
#
# Target: An object is constructed inside a function and returned to the caller. The JIT must heap-allocate it because the caller can observe identity and outlive the callee frame. A buggy scalar replacement that promoted the object to registers would corrupt identity comparisons and field mutations performed by the caller.
#
# Tags: ['escape-analysis', 'escape-via-return', 'identity']
class Pair:
    __slots__ = ("a", "b")
    def __init__(self, a, b):
        self.a = a
        self.b = b

def make_pair(a, b):
    p = Pair(a, b)
    return p  # escapes via return value

p1 = make_pair(1, 2)
p2 = make_pair(1, 2)
assert p1.a == 1 and p1.b == 2
assert p2.a == 1 and p2.b == 2

# Heap-allocated: distinct identities.
assert p1 is not p2

# Mutating one must not affect the other.
p1.a = 99
assert p1.a == 99
assert p2.a == 1

