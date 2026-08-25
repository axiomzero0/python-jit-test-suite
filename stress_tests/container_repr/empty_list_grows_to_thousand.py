# -*- coding: utf-8 -*-
# stress test: empty_list_grows_to_thousand
# category: container_repr
#
# Target: A list starts empty and grows by one element per iteration until it holds 1000 ints. CPython's list internally reallocates the underlying PyObject* array at ~3/2 capacity steps. The JIT must update any cached length/capacity pair after each reallocation.
#
# Tags: ['container', 'list', 'resize']
lst = []
for i in range(1000):
    lst.append(i)

assert len(lst) == 1000
assert lst[0] == 0
assert lst[-1] == 999
assert lst[500] == 500
assert lst == list(range(1000))

# Spot-check after a slice
assert lst[100:105] == [100, 101, 102, 103, 104]

# Insert at front (forces repeated shifts)
lst.insert(0, -1)
assert lst[0] == -1
assert lst[1] == 0
assert len(lst) == 1001

# Pop from end
last = lst.pop()
assert last == 999
assert len(lst) == 1000

