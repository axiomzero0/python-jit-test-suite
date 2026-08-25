# -*- coding: utf-8 -*-
# test_id: conc-0000002
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: indirect
# opt_state: hot
# tags: ['GC', 'concurrency', 'threading_basic']
import threading
results = []
def worker(i):
    results.append(i)
ts = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in ts:
    t.start()
for t in ts:
    t.join()
assert sorted(results) == list(range(10))

