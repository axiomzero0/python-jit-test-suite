# -*- coding: utf-8 -*-
# stress test: deopt_preserves_iteration_state
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Loop iterating a list. Deopt happens. The list iterator's internal index must be preserved.
#
# Tags: ['deopt', 'index', 'iterator']
def work(lst):
    seen = []
    for i, x in enumerate(lst):
        seen.append(x)
        if i == 500:
            y = "trigger"
    return seen

lst = list(range(1000))
seen = work(lst)
assert seen == lst

