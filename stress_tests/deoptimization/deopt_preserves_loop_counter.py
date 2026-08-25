# -*- coding: utf-8 -*-
# stress test: deopt_preserves_loop_counter
# category: deoptimization
#
# Target: Deopt happens mid-loop. The loop counter `i` must have the correct value in the reconstructed interpreter frame.
#
# Tags: ['deopt', 'loop-counter']
def work():
    seen_i = []
    for i in range(1000):
        seen_i.append(i)
        if i == 500:
            x = "trigger"
        else:
            x = i
    return seen_i

seen = work()
assert seen[500] == 500
assert seen[0] == 0
assert seen[-1] == 999

