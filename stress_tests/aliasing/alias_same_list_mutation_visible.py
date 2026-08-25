# -*- coding: utf-8 -*-
# stress test: alias_same_list_mutation_visible
# category: aliasing
#
# Target: Two names bound to the same list object: a mutation through one name must be visible through the other. A JIT that speculates `a` and `b` are distinct objects (e.g. because they have separate SSA names) would mis-observe `a` after the append.
#
# Tags: ['aliasing', 'container', 'list', 'stress']
a = [1, 2, 3]
b = a
b.append(4)
assert a == [1, 2, 3, 4]
assert b == [1, 2, 3, 4]
assert a is b
b.extend([5, 6])
assert a == [1, 2, 3, 4, 5, 6]
b[0] = 99
assert a[0] == 99
assert a == [99, 2, 3, 4, 5, 6]

