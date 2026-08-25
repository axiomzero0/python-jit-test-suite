# -*- coding: utf-8 -*-
# stress test: deopt_preserves_recursion_depth
# category: deoptimization
#
# Target: Recursive function. Deopt happens at depth N. The interpreter must continue with the correct recursion depth and locals at each level.
#
# Tags: ['deopt', 'depth', 'recursion']
import sys

# Raise the limit so sum_to(1000) doesn't hit it
sys.setrecursionlimit(10000)

def sum_to(n):
    if n <= 0:
        return 0
    return n + sum_to(n - 1)

assert sum_to(100) == 5050
assert sum_to(500) == 125250
assert sum_to(1000) == 500500

# Edge cases
assert sum_to(0) == 0
assert sum_to(1) == 1

