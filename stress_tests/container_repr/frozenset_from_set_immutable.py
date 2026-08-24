# -*- coding: utf-8 -*-
# stress test: frozenset_from_set_immutable
# category: container_repr
# opt_state: (runs across all 6 states)
#
# Target: A frozenset is constructed from a set. The frozenset must be immutable and usable as a dict key, while the source set remains mutable. Mutating the source must not affect the frozenset.
#
# Tags: ['container', 'frozenset', 'hash', 'immutable']
s = {1, 2, 3, 4, 5}
fs = frozenset(s)
assert fs == frozenset({1, 2, 3, 4, 5})
assert isinstance(fs, frozenset)
assert isinstance(s, set)

# Mutating the source does not affect the frozenset
s.add(6)
s.discard(1)
assert s == {2, 3, 4, 5, 6}
assert fs == frozenset({1, 2, 3, 4, 5})

# frozenset operations
fs2 = frozenset(range(3, 10))
assert fs | fs2 == frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9})
assert fs & fs2 == frozenset({3, 4, 5})
assert fs - fs2 == frozenset({1, 2})

# Can use frozenset as dict key
d = {fs: 'value'}
assert d[frozenset({1, 2, 3, 4, 5})] == 'value'

# Cannot use a set as a dict key (unhashable)
try:
    {s: 'x'}
    assert False, "expected TypeError"
except TypeError:
    pass

# frozenset from a generator
fs3 = frozenset(x * x for x in range(5))
assert fs3 == frozenset({0, 1, 4, 9, 16})

# frozenset from a string (chars become elements)
fs4 = frozenset("hello")
assert fs4 == frozenset({'h', 'e', 'l', 'l', 'o'})
assert fs4 == frozenset({'h', 'e', 'l', 'o'})

# Frozen set is immutable: cannot add/remove
try:
    fs.add(99)
    assert False, "expected AttributeError"
except AttributeError:
    pass

