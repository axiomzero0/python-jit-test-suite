# -*- coding: utf-8 -*-
# stress test: spill_at_call_site
# category: register_alloc
# opt_state: (runs across all 6 states)
#
# Target: Several variables are live across a call to a non-trivial callee. The calling convention may clobber caller-saved registers, so the allocator must either spill the live values to the stack or move them to callee-saved registers around the call. A buggy allocator that didn't model call clobbers would lose values across the call.
#
# Tags: ['call-site', 'caller-saved', 'register-alloc', 'spill']
def helper(x):
    # A non-trivial callee: enough work that the JIT cannot elide it.
    s = 0
    for i in range(x):
        s += i
    return s

def work():
    a = 10
    b = 20
    c = 30
    d = 40
    # All four are live across the call to helper.
    result = helper(5)
    return a + b + c + d + result

# helper(5) = 0 + 1 + 2 + 3 + 4 = 10
assert work() == 10 + 20 + 30 + 40 + 10
assert work() == 110

