# -*- coding: utf-8 -*-
# test_id: conc-0000012
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: indirect
# opt_state: cold
# tags: ['GC', 'concurrency', 'threading_queue']
import queue, threading
q = queue.Queue()
def producer():
    for i in range(100):
        q.put(i)
    q.put(None)
def consumer(out):
    while True:
        v = q.get()
        if v is None:
            break
        out.append(v)
out = []
c = threading.Thread(target=consumer, args=(out,))
c.start()
producer()
c.join()
assert sorted(out) == list(range(100))

