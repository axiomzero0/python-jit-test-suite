# -*- coding: utf-8 -*-
# stress test: mono_to_poly_int_to_float
# category: type_speculation
# opt_state: (runs across all 6 states)
#
# Target: JIT speculates `x + 1` is int+int based on first 100 calls. The 101st call passes a float, forcing deopt. The deopt must preserve the correct intermediate value and re-execute in the interpreter with float semantics.
#
# Tags: ['deopt', 'guard-failure', 'type-speculation']
def f(x):
    return x + 1

# Warm up monomorphic
results = []
for i in range(100):
    results.append(f(i))

# Speculation breaks here
results.append(f(1.5))
results.append(f(2.5))

# Continue with new type profile
for i in range(100):
    results.append(f(float(i)))

assert results[0] == 1
assert results[100] == 2.5
assert results[-1] == 100.0

