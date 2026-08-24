# -*- coding: utf-8 -*-
# stress test: empty_dict_grows_rehash
# category: container_repr
# opt_state: (runs across all 6 states)
#
# Target: A dict starts empty and grows to 1000 entries, triggering multiple hash table resizes (CPython resizes when load > 2/3 capacity). The JIT must keep all key/value pairs intact across each rehash, including through deliberate deletion and re-insertion.
#
# Tags: ['container', 'dict', 'rehash', 'resize']
d = {}
for i in range(1000):
    d[i] = i * 2

assert len(d) == 1000
for i in range(1000):
    assert d[i] == i * 2

# All keys present after multiple rehashes
assert all(d[i] == i * 2 for i in range(1000))
assert set(d.keys()) == set(range(1000))

# Delete half, forcing shrink
for i in range(0, 1000, 2):
    del d[i]
assert len(d) == 500
assert all(d[i] == i * 2 for i in range(1, 1000, 2))

# Re-add the deleted keys
for i in range(0, 1000, 2):
    d[i] = i * 2
assert len(d) == 1000
assert all(d[i] == i * 2 for i in range(1000))

