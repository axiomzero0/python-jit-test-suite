# -*- coding: utf-8 -*-
# stress test: mutation_during_list_iteration_append
# category: aliasing
#
# Target: Appending to a list while iterating over it with a for-loop is *well-defined* for lists in CPython (the iterator indexes into the list and re-reads its length each step, so the loop will visit newly-appended items until terminated explicitly). A JIT that snapshots `len(xs)` before the loop would either stop early or skip items.
#
# Tags: ['aliasing', 'container', 'list', 'mutation-during-iter', 'stress']
xs = [0]
seen = []
for x in xs:
    seen.append(x)
    if x < 5:
        xs.append(x + 1)
# Each iteration observes the freshly appended element.
assert seen == [0, 1, 2, 3, 4, 5]
assert xs == [0, 1, 2, 3, 4, 5]

