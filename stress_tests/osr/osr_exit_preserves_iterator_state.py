# -*- coding: utf-8 -*-
# stress test: osr_exit_preserves_iterator_state
# category: osr
#
# Target: Hot loop iterating a list. OSR exit (deopt) happens mid-iteration. The iterator's internal position must be preserved so the interpreter continues from the right place.
#
# Tags: ['OSR', 'iterator', 'position']
def work(items):
    total = 0
    for i, x in enumerate(items):
        total += x
        if i == 500:
            total += 0.5  # deopt trigger
    return total

items = list(range(1000))
r = work(items)
expected = sum(items[:501]) + 0.5 + sum(items[501:])
assert r == expected

