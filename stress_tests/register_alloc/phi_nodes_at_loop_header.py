# -*- coding: utf-8 -*-
# stress test: phi_nodes_at_loop_header
# category: register_alloc
#
# Target: A variable takes different values depending on which predecessor entered the loop header (the preheader initializes it; the back-edge updates it). The SSA form represents this with a phi node. The allocator must assign a register (or spill slot) that's consistent across both predecessors. A buggy allocator that didn't model phis would read garbage on the second iteration.
#
# Tags: ['loop-header', 'phi', 'register-alloc', 'ssa']
def work(start, n):
    # `total` is a phi at the loop header:
    #   - from preheader: total = start
    #   - from back-edge: total = total + i
    total = start
    for i in range(n):
        total += i
    return total

assert work(0, 10) == sum(range(10))
assert work(100, 10) == 100 + sum(range(10))
assert work(0, 0) == 0          # loop never runs; phi picks the preheader value
assert work(-5, 5) == -5 + sum(range(5))
assert work(1000, 100) == 1000 + sum(range(100))

