# -*- coding: utf-8 -*-
# stress test: speculate_int_overflow_to_bigint
# category: type_speculation
#
# Target: JIT speculates `x * 2` fits in a machine int (PyLong with ob_digit count = 1). After many iterations with small ints, we pass a value that causes overflow into multi-digit bigint. The JIT must either deopt or have a correct overflow check in the generated code.
#
# Tags: ['bigint', 'overflow', 'type-speculation']
def double(x):
    return x * 2

# Warm up with small ints
for i in range(1000):
    double(i)

# Now force overflow
r1 = double(2**62)
r2 = double(2**63)
r3 = double(2**64)
r4 = double(2**127)

assert r1 == 2**63
assert r2 == 2**64
assert r3 == 2**65
assert r4 == 2**128

# Type of result changed mid-stream
assert type(double(1)) is int
assert type(double(2**63)) is int  # Python ints are arbitrary precision

