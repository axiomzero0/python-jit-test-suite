# -*- coding: utf-8 -*-
# stress test: dict_int_keys_then_str
# category: container_repr
#
# Target: A dict with all-int keys gets a string key, then a tuple key, then a float key. The key type spec changes; the dict may switch from a compact-keys representation to a general-keys representation. All original entries must remain accessible.
#
# Tags: ['container', 'dict', 'keys', 'type-change']
d = {}
for i in range(100):
    d[i] = f"int_{i}"

assert d[0] == "int_0"
assert d[99] == "int_99"

# Add a string key (changes key type spec)
d["hello"] = "world"
assert d["hello"] == "world"

# Add a tuple key
d[(1, 2)] = "tuple_key"
assert d[(1, 2)] == "tuple_key"

# Add a float key (different hash type)
d[3.14] = "pi"
assert d[3.14] == "pi"
# 3 (int) and 3.14 (float) hash differently and coexist
assert d[3] == "int_3"

# All original int keys still present
assert all(d.get(i) == f"int_{i}" for i in range(100))

# Length reflects all keys
assert len(d) == 100 + 3

# Delete a heterogeneous mix
del d[0]
del d["hello"]
del d[(1, 2)]
assert len(d) == 100
assert 0 not in d
assert "hello" not in d
assert (1, 2) not in d

