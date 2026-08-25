# -*- coding: utf-8 -*-
# stress test: ic_global_rebind
# category: inline_caches
#
# Target: Global `X` is rebound mid-loop. The IC for LOAD_GLOBAL must invalidate and re-fetch.
#
# Tags: ['IC', 'global', 'invalidation']
X = 1

def reader():
    return X

results = []
for i in range(100):
    results.append(reader())
    if i == 50:
        X = 2
    if i == 75:
        X = 3

# X is set AFTER the append, so:
# results[0..50] = 1 (X was 1 during those calls)
# results[51..75] = 2 (X was 2 during those calls)
# results[76..99] = 3 (X was 3 during those calls)
assert results[0] == 1
assert results[50] == 1   # X set to 2 AFTER this append
assert results[51] == 2   # first call with X=2
assert results[75] == 2   # X set to 3 AFTER this append
assert results[76] == 3   # first call with X=3
assert results[-1] == 3

