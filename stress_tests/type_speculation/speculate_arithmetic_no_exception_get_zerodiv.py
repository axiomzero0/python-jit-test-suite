# -*- coding: utf-8 -*-
# stress test: speculate_arithmetic_no_exception_get_zerodiv
# category: type_speculation
#
# Target: JIT speculates `a / b` never raises and may elide the exception check. Then b=0 is passed, raising ZeroDivisionError. The deopt must catch this.
#
# Tags: ['exception', 'type-speculation', 'zerodiv']
def divide(a, b):
    return a / b

# Warm up with non-zero
for i in range(1, 100):
    divide(100, i)

# Now zero
for _ in range(5):
    try:
        divide(1, 0)
        assert False, "should have raised"
    except ZeroDivisionError:
        pass

# Back to normal
assert divide(10, 2) == 5.0

