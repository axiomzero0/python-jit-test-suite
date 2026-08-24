# -*- coding: utf-8 -*-
# stress test: ternary_short_circuit
# category: codegen
# opt_state: (runs across all 6 states)
#
# Target: Ternary `a if cond else b` must only evaluate the chosen branch. The other branch must not be evaluated, so any side effects in it must not fire. Nested ternaries must short-circuit at each level.
#
# Tags: ['codegen', 'short-circuit', 'ternary']
calls = []

def true_branch():
    calls.append('T')
    return 'T'

def false_branch():
    calls.append('F')
    return 'F'

# True condition: only true_branch called
assert (true_branch() if True else false_branch()) == 'T'
assert calls == ['T']
calls.clear()

# False condition: only false_branch called
assert (true_branch() if False else false_branch()) == 'F'
assert calls == ['F']
calls.clear()

# Nested ternary (ladder)
def sign(x):
    return 'pos' if x > 0 else ('zero' if x == 0 else 'neg')

assert sign(5) == 'pos'
assert sign(0) == 'zero'
assert sign(-3) == 'neg'
assert calls == []  # nothing called in this ladder

# Side effect in condition is fine
counter = [0]
def cond():
    counter[0] += 1
    return True
result = 'A' if cond() else 'B'
assert result == 'A'
assert counter[0] == 1

# Falsy non-bool condition
assert ('yes' if 0 else 'no') == 'no'
assert ('yes' if '' else 'no') == 'no'
assert ('yes' if [] else 'no') == 'no'
assert ('yes' if 1 else 'no') == 'yes'
assert ('yes' if [0] else 'no') == 'yes'

