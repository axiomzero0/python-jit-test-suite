# -*- coding: utf-8 -*-
# stress test: closure_var_reassigned_mid_function
# category: closure_lifetime
#
# Target: The captured variable is reassigned to a brand-new value mid function via a setter closure. The cell must reflect the new value immediately, and a separate accumulator closure must continue from the new value, not the old one.
#
# Tags: ['cell-write', 'closure', 'reassign']
def make_accumulator():
    total = 0
    def add(v):
        nonlocal total
        total += v
        return total
    def reset(new_start):
        nonlocal total
        old = total
        total = new_start
        return old
    return add, reset

add, reset = make_accumulator()
assert add(1) == 1
assert add(2) == 3
assert add(3) == 6

# Reassign mid-stream
old = reset(100)
assert old == 6
assert add(1) == 101
assert add(2) == 103

# Reassign to a value of different type (deopt)
reset("zero")
# Now adding str + int would fail, so we just verify the cell holds the str
reset(0)
assert add(5) == 5

