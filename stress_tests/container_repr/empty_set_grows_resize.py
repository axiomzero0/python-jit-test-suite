# -*- coding: utf-8 -*-
# stress test: empty_set_grows_resize
# category: container_repr
#
# Target: A set starts empty and grows to 1000 elements, triggering multiple hash table resizes. Duplicates added during growth must be deduplicated, and lookups must succeed after every resize.
#
# Tags: ['container', 'resize', 'set']
s = set()
for i in range(1000):
    s.add(i)

assert len(s) == 1000
for i in range(1000):
    assert i in s

# Re-add the same elements; size must not change
for i in range(1000):
    s.add(i)
assert len(s) == 1000

# Remove and re-add
for i in range(0, 500):
    s.discard(i)
assert len(s) == 500
assert 1 not in s
assert 999 in s

for i in range(0, 500):
    s.add(i)
assert len(s) == 1000
assert 1 in s

