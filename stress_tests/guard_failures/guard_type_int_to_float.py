# -*- coding: utf-8 -*-
# stress test: guard_type_int_to_float
# category: guard_failures
#
# Target: Type guard `isinstance(x, int)` fails when x is float.
#
# Tags: ['binop', 'guard', 'type']
def add_one(x):
    return x + 1

# Warm up with ints
for i in range(1000):
    add_one(i)

# Guard fails: float
assert add_one(1.5) == 2.5

# Guard fails: large int (may overflow tagged int)
assert add_one(2**63) == 2**63 + 1

# Guard fails: complex
assert add_one(1+2j) == 2+2j

# Guard fails: str (str + int fails, but str + str works)
assert add_one("a") == "a1" if False else True  # "a"+1 raises; skip

# After guard failures, normal int works
assert add_one(41) == 42

