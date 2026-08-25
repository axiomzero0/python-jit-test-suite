# -*- coding: utf-8 -*-
# stress test: modify_closure_cell_contents
# category: metaprog_invalidation
#
# Target: A function's __closure__ cells are modified in place by external code, changing the captured value. Subsequent invocations must observe the new value. The JIT cannot inline the captured value as a constant.
#
# Tags: ['cell-mutation', 'closure', 'invalidation']
def make_adder(n):
    def add(x):
        return x + n
    return add

f = make_adder(10)
assert f(5) == 15

# Inspect the closure
assert len(f.__closure__) == 1
cell = f.__closure__[0]
assert cell.cell_contents == 10

# Mutate the cell directly
cell.cell_contents = 100
assert f(5) == 105

# Mutate again, including type change.
# add(x) returns x + n where n is the cell value, so f("cd") = "cd" + "ab"
cell.cell_contents = "ab"
assert f("cd") == "cdab"

# Mutate to a list (list + list concatenation)
# add(x) returns x + n, so f([3, 4]) = [3, 4] + [1, 2]
cell.cell_contents = [1, 2]
assert f([3, 4]) == [3, 4, 1, 2]

# Restore
cell.cell_contents = 10
assert f(5) == 15

