# -*- coding: utf-8 -*-
# stress test: deopt_during_chained_calls
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Chained calls `a().b().c()`. Deopt happens at the second call. The first call's return value must be preserved.
#
# Tags: ['chained-call', 'deopt']
class Chain:
    def __init__(self, v):
        self.v = v
    def a(self):
        return self
    def b(self):
        if self.v == 500:
            return "broken"  # returns str instead of Chain
        return self
    def c(self):
        return self.v

def work(n):
    results = []
    for i in range(n):
        obj = Chain(i)
        try:
            r = obj.a().b().c()
            results.append(r)
        except AttributeError:
            # "broken".c() raises AttributeError
            results.append("attr-error")
    return results

r = work(1000)
assert r[0] == 0
assert r[499] == 499
assert r[500] == "attr-error"
assert r[501] == 501
assert r[-1] == 999

