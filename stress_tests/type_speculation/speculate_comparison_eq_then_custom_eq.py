# -*- coding: utf-8 -*-
# stress test: speculate_comparison_eq_then_custom_eq
# category: type_speculation
#
# Target: JIT speculates `a == b` uses the default __eq__ (pointer comparison). Then a class with custom __eq__ is passed. The deopt must call the custom __eq__.
#
# Tags: ['comparison', 'descriptor', 'type-speculation']
def eq(a, b):
    return a == b

# Warm up with ints
for _ in range(1000):
    eq(1, 1)

class Weird:
    def __eq__(self, other):
        return True  # always equal

w = Weird()
assert eq(w, 1) is True
assert eq(1, w) is True  # __eq__ reflected
assert eq(w, w) is True

