# -*- coding: utf-8 -*-
# stress test: deopt_with_boxed_unboxed_mixed
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: JIT unboxes some locals as int64, others as float64. Deopt must rebox each according to its spec.
#
# Tags: ['deopt', 'mixed-types', 'unbox']
def work():
    a = 0       # int
    b = 0.0     # float
    c = 0       # int
    c_changed = False
    for i in range(1000):
        a += i
        b += i * 0.5
        if not c_changed:
            c += i
        if i == 500:
            # Trigger deopt by changing types
            a = a + 0.5    # a becomes float
            c = "string"   # c becomes str
            c_changed = True
    return a, b, c

a, b, c = work()
assert isinstance(a, float), f"a is {type(a)}"
assert isinstance(b, float), f"b is {type(b)}"
assert c == "string", f"c is {c!r}"

# Verify values: a accumulated ints 0..999, then +0.5 at i=500
expected_a = sum(range(1000)) + 0.5
assert a == expected_a, f"a={a}, expected={expected_a}"
expected_b = sum(i * 0.5 for i in range(1000))
assert abs(b - expected_b) < 1e-9

