# -*- coding: utf-8 -*-
# test_id: conc-0000010
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: indirect
# opt_state: deoptimized
# tags: ['GC', 'concurrency', 'threading_lock']
import threading
lock = threading.Lock()
counter = [0]
def worker():
    for _ in range(100):
        with lock:
            counter[0] += 1
ts = [threading.Thread(target=worker) for _ in range(10)]
for t in ts:
    t.start()
for t in ts:
    t.join()
assert counter[0] == 1000

