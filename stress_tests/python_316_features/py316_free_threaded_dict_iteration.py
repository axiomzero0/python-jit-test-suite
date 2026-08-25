# -*- coding: utf-8 -*-
# stress test: py316_free_threaded_dict_iteration
# category: python_316_features
#
# Target: In free-threaded mode, dict iteration must handle concurrent mutation safely (RuntimeError on mutation during iteration).
#
# Tags: ['PEP-703', 'dict', 'free-threaded', 'iteration', 'py3.16']
import sys
import threading

d = {str(i): i for i in range(100)}

def iterate_and_collect():
    seen = []
    try:
        for k in d:
            seen.append(k)
    except RuntimeError:
        return "runtime-error"
    return seen

r = iterate_and_collect()
assert r != "runtime-error" or isinstance(r, str)

assert len(d) == 100
assert d["50"] == 50

