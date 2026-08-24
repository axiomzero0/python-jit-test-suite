# -*- coding: utf-8 -*-
# stress test: guard_division_by_zero
# category: guard_failures
# opt_state: (runs across all 6 states)
#
# Target: Division guard `b != 0` fails when b is 0.
#
# Tags: ['division', 'guard', 'zero']
def divide(a, b):
    return a / b

for i in range(1, 100):
    divide(100, i)

# Guard fails
for _ in range(5):
    try:
        divide(1, 0)
        assert False
    except ZeroDivisionError:
        pass

# After guard failure, normal division should work
assert divide(10, 2) == 5.0
assert divide(100, 4) == 25.0

