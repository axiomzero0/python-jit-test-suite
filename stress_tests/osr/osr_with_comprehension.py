# -*- coding: utf-8 -*-
# stress test: osr_with_comprehension
# category: osr
#
# Target: OSR into a list comprehension's implicit loop. The comprehension's hidden state (the result list, the iterator, the condition) must all be reconstructed.
#
# Tags: ['OSR', 'comprehension']
def work(n):
    return [i * i for i in range(n) if i % 2 == 0]

r = work(10000)
assert len(r) == 5000
assert r[0] == 0
assert r[-1] == 9998 ** 2
assert r[2500] == 5000 ** 2

