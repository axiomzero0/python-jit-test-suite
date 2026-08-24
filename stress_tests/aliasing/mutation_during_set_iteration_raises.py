# -*- coding: utf-8 -*-
# stress test: mutation_during_set_iteration_raises
# category: aliasing
# opt_state: (runs across all 6 states)
#
# Target: Same as the dict case but for sets: adding or removing an element during iteration must raise RuntimeError. The JIT must keep a generation/version guard on the set.
#
# Tags: ['RuntimeError', 'aliasing', 'container', 'mutation-during-iter', 'set', 'stress']
s = set(range(5))
caught = []
try:
    for x in s:
        if x == 2:
            s.add(100)
except RuntimeError:
    caught.append("add")
s = set(range(5))
try:
    for x in s:
        if x == 2:
            s.discard(3)
except RuntimeError:
    caught.append("discard")
assert caught == ["add", "discard"], caught

