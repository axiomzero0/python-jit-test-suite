# -*- coding: utf-8 -*-
# stress test: many_live_variables_exceed_registers
# category: register_alloc
#
# Target: Twenty-four variables are all simultaneously live across a single use point. This far exceeds the available physical registers on any mainstream architecture, so the allocator must spill most of them to the stack. A buggy allocator that didn't track live ranges would clobber values or read uninitialized memory.
#
# Tags: ['live-range', 'pressure', 'register-alloc', 'spill']
def work():
    a0 = 0
    a1 = 1
    a2 = 2
    a3 = 3
    a4 = 4
    a5 = 5
    a6 = 6
    a7 = 7
    a8 = 8
    a9 = 9
    a10 = 10
    a11 = 11
    a12 = 12
    a13 = 13
    a14 = 14
    a15 = 15
    a16 = 16
    a17 = 17
    a18 = 18
    a19 = 19
    a20 = 20
    a21 = 21
    a22 = 22
    a23 = 23
    # All 24 variables are live here; the allocator must spill most
    # of them and reload each at the point of use.
    return (a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9 +
            a10 + a11 + a12 + a13 + a14 + a15 + a16 + a17 +
            a18 + a19 + a20 + a21 + a22 + a23)

expected = sum(range(24))
assert work() == expected
assert work() == 276

