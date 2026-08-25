# -*- coding: utf-8 -*-
# stress test: guard_range_overflow
# category: guard_failures
#
# Target: Range guard `0 <= i < len` fails when i is out of bounds.
#
# Tags: ['bound', 'guard', 'index', 'range']
def get(x, i):
    return x[i]

lst = list(range(100))
for i in range(100):
    get(lst, i)

# Guard fails: positive out of bounds
for idx in [100, 200]:
    try:
        get(lst, idx)
        assert False, f"should raise for {idx}"
    except IndexError:
        pass

# Negative index out of bounds
try:
    get(lst, -101)
    assert False, "should raise"
except IndexError:
    pass

# Valid negative indices
assert get(lst, -1) == 99
assert get(lst, -100) == 0

# After guard failures, normal access works
assert get(lst, 50) == 50

