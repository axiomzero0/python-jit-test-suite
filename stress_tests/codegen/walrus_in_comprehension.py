# -*- coding: utf-8 -*-
# stress test: walrus_in_comprehension
# category: codegen
# opt_state: (runs across all 6 states)
#
# Target: The walrus operator inside a comprehension binds to the enclosing function scope (not the comprehension's implicit scope). After the comprehension runs, the bound name is visible in the enclosing scope and holds the last assigned value.
#
# Tags: ['codegen', 'comprehension', 'walrus']
data = [1, 2, 3, 4, 5, 6]

# Walrus in expression position
results = [(y := x * 2, y + 1) for x in data]
assert results == [(2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13)]
# `y` is bound in the enclosing scope to the last value
assert y == 12

# Walrus in filter condition
nums = [1, 2, 3, 4, 5]
filtered = [v for x in nums if (v := x * x) > 5]
assert filtered == [9, 16, 25]
assert v == 25

# Walrus in dict comprehension
d = {x: (s := x + 1) for x in range(3)}
assert d == {0: 1, 1: 2, 2: 3}
assert s == 3

# Walrus in set comprehension
s_set = {(y := x * 10) for x in range(3)}
assert s_set == {0, 10, 20}
assert y == 20

# Walrus binding used later in the same expression
xs = [1, -2, 3, -4]
signs = [(sign := ('pos' if x > 0 else 'neg'), x) for x in xs]
assert signs == [('pos', 1), ('neg', -2), ('pos', 3), ('neg', -4)]
assert sign == 'neg'  # last value

