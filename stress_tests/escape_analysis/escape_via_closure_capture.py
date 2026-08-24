# -*- coding: utf-8 -*-
# stress test: escape_via_closure_capture
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: An object is captured by a nested closure that outlives the outer frame. The closure cell holds a strong reference, so the object must be heap-allocated. A scalar-replacement that ignored closure capture would corrupt the captured state across calls.
#
# Tags: ['closure', 'escape-analysis', 'escape-via-closure', 'identity']
class Counter:
    __slots__ = ("n",)
    def __init__(self):
        self.n = 0

def make_counter(start=0):
    c = Counter()
    c.n = start
    def inc():
        c.n += 1   # mutates the captured object
        return c.n
    return inc  # c escapes via the closure

inc1 = make_counter()
assert inc1() == 1
assert inc1() == 2
assert inc1() == 3

# Independent closure => independent captured state.
inc2 = make_counter(100)
assert inc2() == 101
assert inc1() == 4
assert inc2() == 102

