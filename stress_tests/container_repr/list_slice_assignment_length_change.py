# -*- coding: utf-8 -*-
# stress test: list_slice_assignment_length_change
# category: container_repr
#
# Target: Slice assignment replaces a sublist with another of different length, growing or shrinking the list. Extended slice assignment (with step) requires the replacement to have exactly the same length as the slice.
#
# Tags: ['container', 'list', 'mutation', 'slice']
lst = [1, 2, 3, 4, 5]

# Replace middle with more elements (grow)
lst[1:4] = [10, 20, 30, 40, 50]
assert lst == [1, 10, 20, 30, 40, 50, 5]

# Replace with fewer (shrink)
lst[1:6] = [99]
assert lst == [1, 99, 5]

# Replace with empty (delete middle)
lst[:] = [1, 2, 3, 4, 5]
lst[1:4] = []
assert lst == [1, 5]

# Replace whole list
lst[:] = [10, 20, 30]
assert lst == [10, 20, 30]

# Extended slice (step) - must match length exactly
lst = [0] * 10
lst[2:8:2] = [10, 20, 30]
assert lst == [0, 0, 10, 0, 20, 0, 30, 0, 0, 0]

# Extended slice with wrong length raises
try:
    lst[::2] = [1, 2, 3, 4]  # 5 positions, 4 values
    assert False, "expected ValueError"
except ValueError:
    pass

# Negative-step slice assignment
lst = [1, 2, 3, 4, 5]
lst[::-1] = [10, 20, 30, 40, 50]
assert lst == [50, 40, 30, 20, 10]

