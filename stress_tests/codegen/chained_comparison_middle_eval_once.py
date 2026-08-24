# -*- coding: utf-8 -*-
# stress test: chained_comparison_middle_eval_once
# category: codegen
# opt_state: (runs across all 6 states)
#
# Target: Chained comparison `a < b < c` evaluates `b` exactly once, then compares it to both `a` and `c`. If `b` has side effects, those must fire only once.
#
# Tags: ['chained-comparison', 'codegen', 'eval-once']
calls = []

def b_value():
    calls.append('b')
    return 5

# True middle: b evaluated once
assert 1 < b_value() < 10
assert calls == ['b']
calls.clear()

# False middle: b evaluated once
assert not (1 < b_value() < 3)
assert calls == ['b']
calls.clear()

# Different comparison operators in same chain
assert 1 <= b_value() <= 10
assert calls == ['b']
calls.clear()

# Mixed: != in chain
assert 1 != b_value() != 100
assert calls == ['b']
calls.clear()

# Long chain
assert 0 < b_value() < 6 < 7 < 8
assert calls == ['b']

# Side effects in operands, verify ordering
log = []
def log_v(x):
    log.append(x)
    return x

# Each operand evaluated once, in order: a, b, c
log.clear()
result = log_v(1) < log_v(5) < log_v(10)
assert result is True
assert log == [1, 5, 10]

# Short-circuit: if first comparison is False, c is not evaluated
log.clear()
result = log_v(10) < log_v(5) < log_v(0)
assert result is False
assert log == [10, 5]  # c not evaluated

# Different operators
log.clear()
result = log_v(1) < log_v(5) <= log_v(5) < log_v(6)
assert result is True
assert log == [1, 5, 5, 6]

