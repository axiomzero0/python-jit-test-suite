# -*- coding: utf-8 -*-
# stress test: list_slice_is_independent_copy
# category: aliasing
# opt_state: (runs across all 6 states)
#
# Target: Negative case: `xs[:]` returns a fresh list, so mutations to the slice must NOT propagate to the original. A JIT that incorrectly treats slicing as an alias would break this.
#
# Tags: ['aliasing', 'container', 'list', 'shallow-copy', 'slice', 'stress']
xs = [1, 2, 3]
copy = xs[:]
copy.append(4)
assert xs == [1, 2, 3]
assert copy == [1, 2, 3, 4]
assert copy is not xs
copy[0] = 999
assert xs[0] == 1
# But full slice keeps element aliasing for mutable items.
inner = [10]
outer = [inner, 20]
outer_copy = outer[:]
outer_copy[0].append(11)
assert outer[0] == [10, 11]   # element aliasing preserved
assert outer_copy[0] is outer[0]
outer_copy[1] = 999
assert outer[1] == 20          # outer list itself is independent

