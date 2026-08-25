# -*- coding: utf-8 -*-
# stress test: speculate_global_constant_then_mutate
# category: type_speculation
#
# Target: JIT speculates the global `CONST` is the int 42 and may inline it as a constant. Then the global is mutated. The JIT must invalidate any compiled code that embedded the constant.
#
# Tags: ['global', 'invalidation', 'type-speculation']
CONST = 42

def read_const():
    return CONST + 1

# Warm up
for _ in range(1000):
    assert read_const() == 43

# Mutate global
CONST = 100
assert read_const() == 101

# Mutate again
CONST = -5
assert read_const() == -4

# Back
CONST = 42
assert read_const() == 43

