# -*- coding: utf-8 -*-
# test_id: conc-0000023
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: indirect
# opt_state: reheated
# tags: ['GC', 'concurrency', 'threading_pool']
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(lambda x: x * x, range(20)))
assert results == [i * i for i in range(20)]

