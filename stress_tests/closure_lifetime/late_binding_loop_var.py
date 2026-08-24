# -*- coding: utf-8 -*-
# stress test: late_binding_loop_var
# category: closure_lifetime
# opt_state: (runs across all 6 states)
#
# Target: Closures capture the loop variable cell by reference, not by value. By the time the lambdas are called, the loop has finished and the cell holds the final value. A JIT that speculates the cell holds a fixed value per closure must deopt when all closures return the same late-bound value.
#
# Tags: ['cell', 'closure', 'late-binding']
def make_fns():
    fns = []
    for i in range(3):
        fns.append(lambda: i)
    return fns

fns = make_fns()
# All closures see the final value of i (late binding)
results = [f() for f in fns]
assert results == [2, 2, 2]

# Contrast: capture current value via default argument
def make_fns2():
    fns = []
    for i in range(3):
        fns.append(lambda i=i: i)
    return fns

fns2 = make_fns2()
assert [f() for f in fns2] == [0, 1, 2]

