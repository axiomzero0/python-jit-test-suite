# -*- coding: utf-8 -*-
# stress test: dict_popitem_loop_shrinks
# category: container_repr
# opt_state: (runs across all 6 states)
#
# Target: A loop calls dict.popitem() until the dict is empty. The internal hash table must shrink (or at least mark entries dummy) without losing any un-popped entries. popitem on an empty dict must raise KeyError.
#
# Tags: ['container', 'dict', 'popitem', 'shrink']
d = {i: i * 2 for i in range(100)}
items = []
while d:
    k, v = d.popitem()
    items.append((k, v))

assert len(items) == 100
assert len(d) == 0

# All items accounted for
assert sorted(items) == [(i, i * 2) for i in range(100)]

# popitem on empty raises KeyError
try:
    d.popitem()
    assert False, "expected KeyError"
except KeyError:
    pass

# Rebuild and verify interleaved popitem + get still works.
# In CPython 3.7+, dict.popitem removes the LAST-inserted entry, so after
# 25 pops from a 0..49 dict, the remaining keys are 0..24.
d = {i: i * 3 for i in range(50)}
popped_count = 0
while d:
    if popped_count == 25:
        # Mid-shrink: verify all remaining entries are still present
        remaining = sorted(d.items())
        assert remaining == [(i, i * 3) for i in range(0, 25)]
    k, v = d.popitem()
    popped_count += 1
assert popped_count == 50

