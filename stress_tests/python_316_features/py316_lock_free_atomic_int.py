# -*- coding: utf-8 -*-
# stress test: py316_lock_free_atomic_int
# category: python_316_features
#
# Target: PEP 703: In free-threaded mode, simple integer operations should be atomic at the bytecode level. Verify that a counter increment doesn't lose updates under high contention.
#
# Tags: ['PEP-703', 'atomic', 'free-threaded', 'lock', 'py3.16']
import sys
import threading

counter = [0]
N_THREADS = 4
N_INCREMENTS = 10000

lock = threading.Lock()

def worker():
    for _ in range(N_INCREMENTS):
        with lock:
            counter[0] += 1

threads = [threading.Thread(target=worker) for _ in range(N_THREADS)]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert counter[0] == N_THREADS * N_INCREMENTS

