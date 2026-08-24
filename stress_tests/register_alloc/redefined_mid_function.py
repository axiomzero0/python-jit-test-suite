# -*- coding: utf-8 -*-
# stress test: redefined_mid_function
# category: register_alloc
# opt_state: (runs across all 6 states)
#
# Target: A variable is redefined in the middle of the function. In SSA form this is two distinct definitions; the allocator must treat them as independent live ranges and may assign them to different registers. A buggy allocator that reused the same register without checking liveness would corrupt earlier values that are still in use.
#
# Tags: ['live-range', 'redefinition', 'register-alloc', 'ssa']
def work(x):
    a = x * 2          # def 1: a = 2x
    b = a + 1          # b = 2x + 1 (uses def 1 of a)
    a = b * 3          # def 2: a = 6x + 3 (redefinition; def 1 dies here)
    c = a - 1          # c = 6x + 2 (uses def 2 of a)
    a = c + 10         # def 3: a = 6x + 12 (redefinition; def 2 dies here)
    return a + b + c   # (6x + 12) + (2x + 1) + (6x + 2) = 14x + 15

# Verify across a range of inputs to catch subtle bugs.
for x in [0, 1, 2, 5, 10, -3, 100, -100]:
    expected = 14 * x + 15
    got = work(x)
    assert got == expected, f"work({x}) = {got}, expected {expected}"

