# -*- coding: utf-8 -*-
# stress test: ic_megamorphic_threshold
# category: inline_caches
# opt_state: (runs across all 6 states)
#
# Target: Call site transitions from monomorphic -> polymorphic -> megamorphic by passing more than 4 different types. The IC must handle each transition correctly.
#
# Tags: ['IC', 'megamorphic', 'threshold']
class T1:
    def f(self): return 1
class T2:
    def f(self): return 2
class T3:
    def f(self): return 3
class T4:
    def f(self): return 4
class T5:
    def f(self): return 5
class T6:
    def f(self): return 6

def call(o):
    return o.f()

objs = [T1(), T2(), T3(), T4(), T5(), T6()]
results = []
# Iterate so the IC sees each type multiple times
for _ in range(100):
    for o in objs:
        results.append(call(o))

assert results[0] == 1
assert results[599] == 6
assert len(set(results)) == 6

