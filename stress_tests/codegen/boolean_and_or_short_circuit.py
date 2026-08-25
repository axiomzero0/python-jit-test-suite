# -*- coding: utf-8 -*-
# stress test: boolean_and_or_short_circuit
# category: codegen
#
# Target: `and` returns the first falsy operand (or the last truthy one), short-circuiting so RHS is not evaluated if LHS determines the result. `or` is the dual. Result is the operand value, not coerced to bool.
#
# Tags: ['and-or', 'codegen', 'short-circuit']
calls = []

def t():
    calls.append('t')
    return True

def f():
    calls.append('f')
    return False

# `and` short-circuits on False: only f() called
assert (f() and t()) is False
assert calls == ['f']
calls.clear()

# `or` short-circuits on True: only t() called
assert (t() or f()) is True
assert calls == ['t']
calls.clear()

# Truthy non-bool returned as-is
def five():
    calls.append('five')
    return 5
assert (five() or t()) == 5
assert calls == ['five']  # t not called
calls.clear()

# `and` returns last truthy or first falsy
assert (5 and 6 and 7) == 7
assert (0 and 5) == 0
assert (5 and 0 and 7) == 0

# `or` returns first truthy or last falsy
assert (0 or '' or 7) == 7
assert (0 or '') == ''
assert (0 or None or False) is False

# Side effect ordering with mixed operators
log = []
def log_v(name, v):
    log.append(name)
    return v

# and: evaluates left-to-right, stops at first falsy
log.clear()
result = log_v('a', 1) and log_v('b', 0) and log_v('c', 1)
assert result == 0
assert log == ['a', 'b']

# or: evaluates left-to-right, stops at first truthy
log.clear()
result = log_v('a', 0) or log_v('b', 1) or log_v('c', 0)
assert result == 1
assert log == ['a', 'b']

