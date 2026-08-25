# -*- coding: utf-8 -*-
# stress test: tuple_immutable_shell_mutable_contents
# category: aliasing
#
# Target: A tuple's *structure* is immutable, but its elements can be mutable. Mutating an element through the tuple slot is fine and visible to other aliases. A JIT that specializes on `isinstance(x, tuple)` and assumes deep immutability would get this wrong.
#
# Tags: ['aliasing', 'container', 'hash', 'immutability', 'stress', 'tuple']
inner = [2]
t = (1, inner, 3)
# The tuple slot itself is locked.
try:
    t[1] = 99
    assert False, "expected TypeError"
except TypeError:
    pass
# But the object at the slot is mutable.
t[1].append(99)
assert inner == [2, 99]
assert t[1] is inner
assert t == (1, [2, 99], 3)
# Reassignment through the alias still works.
inner.extend([100, 200])
assert t[1] == [2, 99, 100, 200]
# Hashing fails when a tuple contains an unhashable (mutable) element.
try:
    hash(t)
    assert False, "expected TypeError on hash"
except TypeError:
    pass
# But a tuple of immutables is hashable.
t2 = (1, (2, 3), "abc")
assert hash(t2) == hash((1, (2, 3), "abc"))

