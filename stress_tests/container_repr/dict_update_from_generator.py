# -*- coding: utf-8 -*-
# stress test: dict_update_from_generator
# category: container_repr
# opt_state: (runs across all 6 states)
#
# Target: Dict.update() is called with a generator that yields (key, value) tuples. The dict must consume the generator lazily and insert each entry, including overriding existing keys.
#
# Tags: ['container', 'dict', 'generator', 'update']
d = {i: i * 10 for i in range(50)}

# Update with a generator of new keys
d.update((i, i * 100) for i in range(50, 100))
assert len(d) == 100
for i in range(100):
    expected = i * 10 if i < 50 else i * 100
    assert d[i] == expected

# Update with a generator that overrides existing keys
d.update((i, -1) for i in range(0, 100, 10))
for i in range(0, 100, 10):
    assert d[i] == -1
# Non-overridden keys intact
for i in range(1, 10):
    assert d[i] == i * 10

# Update with another dict
d.update({0: 'overwritten', 1: 'also'})
assert d[0] == 'overwritten'
assert d[1] == 'also'

# Update with a list of pairs
d.update([(200, 'list_pair'), (201, 'list_pair2')])
assert d[200] == 'list_pair'
assert d[201] == 'list_pair2'

