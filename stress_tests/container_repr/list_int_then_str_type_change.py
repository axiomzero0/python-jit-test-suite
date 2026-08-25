# -*- coding: utf-8 -*-
# stress test: list_int_then_str_type_change
# category: container_repr
#
# Target: A list of ints is built up; then a string is appended. The element type spec changes from 'list[int]' to 'list[object]'. The JIT must invalidate any specialized fast path that assumed homogeneous int elements.
#
# Tags: ['container', 'list', 'type-change']
lst = [1, 2, 3]
for i in range(4, 100):
    lst.append(i)

# Now append a string (type spec breaks)
lst.append("hello")
# After [1,2,3] + range(4,100) (96 ints) + "hello" = 100 elements
assert len(lst) == 100
assert lst[:5] == [1, 2, 3, 4, 5]
assert lst[-1] == "hello"
assert lst[99] == "hello"

# Append more types
lst.extend([10.5, None, True, (1, 2)])
assert lst[-4:] == [10.5, None, True, (1, 2)]
assert lst[-1] == (1, 2)
assert lst[-3] is None

# Spot-check that ints are still intact (lst[i] == i+1 for i in 0..98)
assert lst[50] == 51
assert lst[0] == 1

# Convert to a typed structure (sum only works on numerics; bool excluded
# explicitly because isinstance(True, int) is True)
numeric_sum = sum(x for x in lst if isinstance(x, (int, float)) and not isinstance(x, bool))
# Ints 1..99 plus the float 10.5; True is bool so excluded
assert numeric_sum == sum(range(1, 100)) + 10.5

