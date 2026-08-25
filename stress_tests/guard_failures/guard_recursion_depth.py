# -*- coding: utf-8 -*-
# stress test: guard_recursion_depth
# category: guard_failures
#
# Target: Recursion limit guard fails when depth is exceeded.
#
# Tags: ['depth', 'guard', 'recursion']
import sys

def recurse(n):
    if n <= 0:
        return 0
    return 1 + recurse(n - 1)

# Safe depth
assert recurse(100) == 100

# Exceed limit
try:
    recurse(sys.getrecursionlimit() + 100)
    assert False, "should have raised RecursionError"
except RecursionError:
    pass

# After recovery, normal recursion works
assert recurse(50) == 50

