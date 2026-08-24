# -*- coding: utf-8 -*-
# stress test: large_list_comprehension_resizes
# category: container_repr
# opt_state: (runs across all 6 states)
#
# Target: A list comprehension builds a 10000-element list. CPython's BUILD_LIST_FROM_OP performs several internal reallocations during the comprehension. A nested comprehension builds a matrix; both must produce correct contents after all resizes.
#
# Tags: ['comprehension', 'container', 'list', 'resize']
lst = [x * x for x in range(10000)]
assert len(lst) == 10000
assert lst[0] == 0
assert lst[9999] == 9999 ** 2
assert lst[5000] == 25000000
assert sum(lst) == sum(x * x for x in range(10000))

# Nested comprehension -> matrix
matrix = [[i * j for j in range(10)] for i in range(10)]
assert len(matrix) == 10
assert all(len(row) == 10 for row in matrix)
assert matrix[3][4] == 12
assert matrix[5][5] == 25
assert matrix[0][0] == 0
assert matrix[9][9] == 81

# Condition in comprehension
evens = [x for x in range(100) if x % 2 == 0]
assert len(evens) == 50
assert evens[0] == 0
assert evens[-1] == 98

# Multiple for clauses
flattened = [i * 10 + j for i in range(3) for j in range(3)]
assert flattened == [0, 1, 2, 10, 11, 12, 20, 21, 22]

