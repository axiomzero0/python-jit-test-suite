# -*- coding: utf-8 -*-
# stress test: dict_shared_mutable_value_object
# category: aliasing
#
# Target: Two dicts store the *same* mutable value object under different keys. Mutating that shared value (in place) must be visible through both dicts. A JIT that snapshots dict values into locals and reuses them across calls would miss the in-place mutation.
#
# Tags: ['aliasing', 'container', 'dict', 'stress', 'value']
shared = [1, 2]
d1 = {"a": shared}
d2 = {"b": shared}
assert d1["a"] is d2["b"]
shared.append(3)
assert d1["a"] == [1, 2, 3]
assert d2["b"] == [1, 2, 3]
# Mutate through the dict slot
d1["a"].append(4)
assert d2["b"] == [1, 2, 3, 4]
assert shared == [1, 2, 3, 4]

