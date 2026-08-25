# -*- coding: utf-8 -*-
# stress test: py316_free_threaded_basic
# category: python_316_features
#
# Target: PEP 703: Free-threaded mode (no GIL) is supported in 3.16. Multiple threads can run Python code in parallel. The JIT must be thread-safe without the GIL.
#
# Tags: ['PEP-703', 'free-threaded', 'py3.16', 'threading']
import sys
import threading

counter = [0]
lock = threading.Lock()

def worker(n):
    for _ in range(n):
        with lock:
            counter[0] += 1

threads = [threading.Thread(target=worker, args=(1000,)) for _ in range(8)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# With the lock, the counter must be exactly 8000
assert counter[0] == 8000, f"got {counter[0]}"

