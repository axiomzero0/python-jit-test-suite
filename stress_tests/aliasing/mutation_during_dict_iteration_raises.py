# -*- coding: utf-8 -*-
# stress test: mutation_during_dict_iteration_raises
# category: aliasing
# opt_state: (runs across all 6 states)
#
# Target: Adding or removing keys during dict iteration must raise RuntimeError (CPython sets a `ma_version_tag` change marker). A JIT that compiles the iterator without a version check would silently observe a stale or partial key set.
#
# Tags: ['RuntimeError', 'aliasing', 'container', 'dict', 'mutation-during-iter', 'stress']
d = {i: i * i for i in range(5)}
caught = []
try:
    for k in d:
        if k == 2:
            d[100] = 10000  # insert during iteration
except RuntimeError:
    caught.append("insert")
# Reset and try a delete
d = {i: i * i for i in range(5)}
try:
    for k in d:
        if k == 2:
            del d[3]  # delete during iteration
except RuntimeError:
    caught.append("delete")
assert caught == ["insert", "delete"], caught

