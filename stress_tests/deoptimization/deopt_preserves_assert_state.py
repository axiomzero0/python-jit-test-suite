# -*- coding: utf-8 -*-
# stress test: deopt_preserves_assert_state
# category: deoptimization
#
# Target: Assertion inside a hot loop. Deopt must preserve the assertion's failure behavior.
#
# Tags: ['assert', 'deopt']
def work():
    for i in range(1000):
        assert i >= 0
        if i == 500:
            x = "trigger"
    return "ok"

assert work() == "ok"

