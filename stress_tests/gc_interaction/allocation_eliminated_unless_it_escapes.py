# -*- coding: utf-8 -*-
# stress test: allocation_eliminated_unless_it_escapes
# category: gc_interaction
# opt_state: (runs across all 6 states)
#
# Target: An object allocated, used, and discarded in a single function may be eliminated by escape analysis. But if it escapes (here, via a weakref), the allocation must survive and the GC must see it. The test verifies both: in CPython the no-escape path allocates 1000 objects (correct, if not optimized), and the escape path allocates 1000 AND collects them after scope exit.
#
# Tags: ['GC', 'escape-analysis', 'weakref']
import gc
import weakref

class Hidden:
    counter = 0
    def __init__(self):
        Hidden.counter += 1

# Case 1: no escape. JIT may eliminate; CPython allocates all.
def no_escape():
    total = 0
    for _ in range(1000):
        h = Hidden()
        total += id(h) & 7  # use but do not store
    return total

Hidden.counter = 0
no_escape()
assert Hidden.counter == 1000  # CPython baseline; JIT may reduce this.

# Case 2: escapes via weakref. JIT must NOT eliminate.
def escapes_via_weakref():
    wrs = []
    for _ in range(1000):
        h = Hidden()
        wrs.append(weakref.ref(h))
    return wrs

Hidden.counter = 0
wrs = escapes_via_weakref()
assert Hidden.counter == 1000, (
    f"only {Hidden.counter} allocations; weakref escape was wrongly elided"
)
gc.collect()
alive = sum(1 for r in wrs if r() is not None)
assert alive == 0, f"{alive} objects survived after scope exit"

