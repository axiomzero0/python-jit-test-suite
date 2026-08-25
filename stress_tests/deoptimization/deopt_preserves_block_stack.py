# -*- coding: utf-8 -*-
# stress test: deopt_preserves_block_stack
# category: deoptimization
#
# Target: Deopt happens inside a nested try/except/finally. The block stack must be reconstructed so the except/finally blocks run correctly.
#
# Tags: ['block-stack', 'deopt', 'finally']
def work():
    log = []
    try:
        for i in range(1000):
            if i == 500:
                # Trigger deopt by changing type
                x = "string"
            else:
                x = i
            log.append(x)
    except TypeError:
        log.append("type-error")
    finally:
        log.append("finally")
    return log

r = work()
assert len(r) == 1001
assert r[500] == "string"
assert r[-1] == "finally"

