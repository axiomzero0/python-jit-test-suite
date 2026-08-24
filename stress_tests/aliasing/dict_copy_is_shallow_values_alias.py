# -*- coding: utf-8 -*-
# stress test: dict_copy_is_shallow_values_alias
# category: aliasing
# opt_state: (runs across all 6 states)
#
# Target: `dict.copy()` produces a new dict but the *values* are still shared references. Mutating a mutable value in place must be visible through both dicts; replacing a value under a key in the copy must NOT affect the original.
#
# Tags: ['aliasing', 'container', 'dict', 'shallow-copy', 'stress']
shared_list = [1, 2]
d = {"k": shared_list, "n": 5}
c = d.copy()
assert c is not d
assert c["k"] is d["k"]   # value aliasing preserved
# In-place mutation through one alias is visible through the other.
c["k"].append(3)
assert d["k"] == [1, 2, 3]
assert c["k"] == [1, 2, 3]
# Replacing a value under a key in the copy is NOT visible in original.
c["n"] = 99
assert d["n"] == 5
assert c["n"] == 99
# Adding a key in the copy is not visible in original.
c["new"] = "x"
assert "new" not in d

