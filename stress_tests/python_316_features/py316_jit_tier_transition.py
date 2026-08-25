# -*- coding: utf-8 -*-
# stress test: py316_jit_tier_transition
# category: python_316_features
#
# Target: CPython 3.13+ has a tiered JIT: interpreter -> baseline JIT -> optimizing JIT. Verify tier transitions are transparent.
#
# Tags: ['JIT', 'PEP-659', 'py3.16', 'tier-transition']
def hot_function(n):
    s = 0
    for i in range(n):
        s += i
    return s

assert hot_function(10) == 45

for _ in range(10):
    assert hot_function(100) == 4950

for _ in range(1000):
    assert hot_function(1000) == 499500

for _ in range(10000):
    hot_function(1000)

assert hot_function(1000) == 499500
assert hot_function(100) == 4950
assert hot_function(10) == 45

