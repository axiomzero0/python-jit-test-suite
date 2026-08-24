# -*- coding: utf-8 -*-
# stress test: dict_comprehension_with_collisions
# category: container_repr
# opt_state: (runs across all 6 states)
#
# Target: A dict comprehension builds a dict with 100 keys whose __hash__ all return 0, forcing a long collision chain. Lookups must use __eq__ to disambiguate. The JIT cannot rely on hash equality as a proxy for key equality.
#
# Tags: ['collision', 'container', 'dict', 'hash']
class CollidingHash:
    __slots__ = ('val',)
    def __init__(self, val):
        self.val = val
    def __hash__(self):
        return 0  # all collide
    def __eq__(self, other):
        return isinstance(other, CollidingHash) and self.val == other.val
    def __repr__(self):
        return f"CH({self.val})"

keys = [CollidingHash(i) for i in range(100)]
d = {k: k.val * 2 for k in keys}
assert len(d) == 100

# Every key looks up correctly despite collisions
for k in keys:
    assert d[k] == k.val * 2

# Look up by an equivalent key (different object, same val)
specific = CollidingHash(50)
assert d[specific] == 100

# Delete a key by an equivalent object
del d[CollidingHash(50)]
assert len(d) == 99
try:
    _ = d[specific]
    assert False, "expected KeyError"
except KeyError:
    pass

# Other keys still present
for k in keys:
    if k.val == 50:
        continue
    assert d[k] == k.val * 2

