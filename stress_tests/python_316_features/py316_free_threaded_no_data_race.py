# -*- coding: utf-8 -*-
# stress test: py316_free_threaded_no_data_race
# category: python_316_features
#
# Target: In free-threaded mode, simple integer operations on shared state must be atomic at the bytecode level. The JIT must preserve this atomicity in optimized code.
#
# Tags: ['PEP-703', 'free-threaded', 'lock', 'py3.16']
import sys
import threading

shared = [0]

def incrementer(n):
    for _ in range(n):
        with threading.Lock():
            shared[0] += 1

threads = [threading.Thread(target=incrementer, args=(10000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert shared[0] == 40000

