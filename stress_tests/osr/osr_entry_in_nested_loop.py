# -*- coding: utf-8 -*-
# stress test: osr_entry_in_nested_loop
# category: osr
#
# Target: OSR entry into the *inner* loop of a nested loop structure. The compiled frame must know which loop is being entered and reconstruct both loop counters.
#
# Tags: ['OSR', 'nested-loop']
def nested(n):
    total = 0
    for i in range(n):
        for j in range(n):
            total += i * j
    return total

assert nested(100) == sum(i * j for i in range(100) for j in range(100))

