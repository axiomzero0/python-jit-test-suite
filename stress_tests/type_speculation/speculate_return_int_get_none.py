# -*- coding: utf-8 -*-
# stress test: speculate_return_int_get_none
# category: type_speculation
#
# Target: JIT speculates `f()` returns int and may unbox it. The 101st call returns None. The deopt must rebox and propagate None correctly to the caller.
#
# Tags: ['return-type', 'type-speculation', 'unbox']
flag = [False]

def f(x):
    if x < 100:
        return x * 2
    return None

# Warm up returning int
for i in range(100):
    f(i)

# Now return None
assert f(100) is None
assert f(200) is None

# And back to int
assert f(50) == 100

