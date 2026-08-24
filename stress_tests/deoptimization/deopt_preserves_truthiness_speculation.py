# -*- coding: utf-8 -*-
# stress test: deopt_preserves_truthiness_speculation
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: JIT speculates `if x:` is testing an int (truthy if nonzero). Then x is a custom object with __bool__. Deopt must call __bool__.
#
# Tags: ['bool', 'deopt', 'truthiness']
class Weird:
    def __init__(self, v):
        self.v = v
    def __bool__(self):
        return self.v % 2 == 0

def check(x):
    if x:
        return "truthy"
    return "falsy"

# Warm up with ints
for i in range(1000):
    check(i)

# Now Weird objects
# Weird(0): 0 % 2 == 0 -> True -> "truthy"
assert check(Weird(0)) == "truthy"
# Weird(1): 1 % 2 == 0 -> False -> "falsy"
assert check(Weird(1)) == "falsy"
# Weird(2): 2 % 2 == 0 -> True -> "truthy"
assert check(Weird(2)) == "truthy"

# int 0 -> falsy, int 1 -> truthy
assert check(0) == "falsy"
assert check(1) == "truthy"

