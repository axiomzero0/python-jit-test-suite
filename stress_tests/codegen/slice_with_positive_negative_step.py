# -*- coding: utf-8 -*-
# stress test: slice_with_positive_negative_step
# category: codegen
#
# Target: Slicing supports start, stop, and step, where step may be negative (reverse). The JIT must handle the empty-range edge cases and the boundary conditions for negative step.
#
# Tags: ['codegen', 'reverse', 'slice', 'step']
lst = list(range(10))  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Positive step
assert lst[::2] == [0, 2, 4, 6, 8]
assert lst[1::2] == [1, 3, 5, 7, 9]
assert lst[::3] == [0, 3, 6, 9]
assert lst[1:8:2] == [1, 3, 5, 7]

# Negative step (reverse)
assert lst[::-1] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
assert lst[::-2] == [9, 7, 5, 3, 1]
assert lst[::-3] == [9, 6, 3, 0]
assert lst[8:0:-1] == [8, 7, 6, 5, 4, 3, 2, 1]
assert lst[8:0:-2] == [8, 6, 4, 2]
assert lst[-1::-1] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
assert lst[-1:-5:-1] == [9, 8, 7, 6]

# Empty slices
assert lst[5:5] == []
assert lst[5:2] == []  # positive step, start > stop
assert lst[2:5:-1] == []  # negative step, start < stop
assert lst[10:0] == []  # start >= len

# Out-of-bounds are clamped
assert lst[5:100] == [5, 6, 7, 8, 9]
assert lst[-100:3] == [0, 1, 2]
assert lst[100:200] == []

# String slicing
s = "abcdefg"
assert s[::-1] == "gfedcba"
assert s[::2] == "aceg"
assert s[1:-1:2] == "bdf"
assert s[6:0:-2] == "gec"  # indices 6,4,2 (stop=0 is excluded)

# Tuple slicing
t = (10, 20, 30, 40, 50)
assert t[::-1] == (50, 40, 30, 20, 10)
assert t[::2] == (10, 30, 50)
assert t[1:4:2] == (20, 40)

# Step of 1 (most common)
assert lst[2:5:1] == [2, 3, 4]
assert lst[::1] == lst

# Assignment to extended slice (must match length)
lst2 = [0] * 10
lst2[2:8:2] = [10, 20, 30]
assert lst2 == [0, 0, 10, 0, 20, 0, 30, 0, 0, 0]

# Negative step assignment
lst3 = list(range(5))
lst3[::-1] = list(range(5))
assert lst3 == [4, 3, 2, 1, 0]

