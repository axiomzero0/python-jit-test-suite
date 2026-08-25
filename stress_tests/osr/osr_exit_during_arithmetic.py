# -*- coding: utf-8 -*-
# stress test: osr_exit_during_arithmetic
# category: osr
#
# Target: Hot loop runs optimized for 1000 iterations. On iteration 1001, a type speculation fails (int -> float). The OSR exit must reconstruct the loop state with the correct float value of `acc`.
#
# Tags: ['OSR', 'exit', 'type-speculation']
def accumulate(values):
    acc = 0
    for v in values:
        acc += v  # speculation: int+int
    return acc

# All ints for warmup
ints = list(range(1000))
assert accumulate(ints) == sum(ints)

# Now mix in a float — deopt on iteration 1001
mixed = list(range(1000)) + [0.5, 0.5]
r = accumulate(mixed)
assert r == sum(mixed)
assert isinstance(r, float)

