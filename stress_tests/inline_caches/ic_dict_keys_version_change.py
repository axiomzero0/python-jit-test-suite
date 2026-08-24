# -*- coding: utf-8 -*-
# stress test: ic_dict_keys_version_change
# category: inline_caches
# opt_state: (runs across all 6 states)
#
# Target: JIT caches dict lookups by the dict's keys version. Adding a new key bumps the version, invalidating the cache.
#
# Tags: ['IC', 'dict', 'keys-version']
d = {str(i): i for i in range(20)}

def lookup(k):
    return d[k]

for _ in range(1000):
    lookup("5")

# Add new keys (changes keys version)
for i in range(20, 30):
    d[str(i)] = i

assert lookup("5") == 5
assert lookup("25") == 25
assert lookup("29") == 29

# Delete a key
del d["0"]
try:
    lookup("0")
    assert False
except KeyError:
    pass

