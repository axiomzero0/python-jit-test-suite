# -*- coding: utf-8 -*-
# stress test: osr_entry_at_loop_back_edge
# category: osr
#
# Target: OSR entry at the loop back-edge (the typical entry point). This verifies that the JIT can replace the interpreter frame at exactly the right instruction (the back-edge jump).
#
# Tags: ['OSR', 'back-edge']
def work(n):
    s = 0
    for i in range(n):
        s += i
    return s

# Large enough to trigger OSR
assert work(100_000) == sum(range(100_000))

