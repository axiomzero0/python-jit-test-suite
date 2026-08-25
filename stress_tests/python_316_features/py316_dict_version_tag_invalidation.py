# -*- coding: utf-8 -*-
# stress test: py316_dict_version_tag_invalidation
# category: python_316_features
#
# Target: Python 3.13+ uses dict version tags for fast IC invalidation. Mutating a dict bumps its version, invalidating any cached lookups. The JIT must respect version tag changes.
#
# Tags: ['IC', 'PEP-659', 'dict', 'py3.16', 'version-tag']
d = {str(i): i for i in range(20)}

def lookup(k):
    return d.get(k)

for i in range(100):
    lookup(str(i % 20))

assert all(lookup(str(i)) == i for i in range(20))
assert lookup("missing") is None

d["new_key"] = 99
assert lookup("new_key") == 99
assert lookup("0") == 0

del d["0"]
assert lookup("0") is None
assert lookup("1") == 1

