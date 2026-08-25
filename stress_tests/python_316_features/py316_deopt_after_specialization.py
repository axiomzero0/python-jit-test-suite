# -*- coding: utf-8 -*-
# stress test: py316_deopt_after_specialization
# category: python_316_features
#
# Target: When a specialized bytecode deopts (because the specialization no longer applies), the deopt must preserve correctness.
#
# Tags: ['PEP-659', 'deopt', 'py3.16', 'specialization']
def add(a, b):
    return a + b

for _ in range(1000):
    add(1, 2)

assert add(1.5, 2.5) == 4.0
assert add("a", "b") == "ab"
assert add([1], [2]) == [1, 2]

for _ in range(1000):
    add(1, 2)

assert add(1, 2) == 3

