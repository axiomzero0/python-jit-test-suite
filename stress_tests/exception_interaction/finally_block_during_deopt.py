# -*- coding: utf-8 -*-
# stress test: finally_block_during_deopt
# category: exception_interaction
#
# Target: Deopt is triggered mid-loop by a type change (int -> str). The loop body sits inside a try/finally. The finally block must execute with the reconstructed interpreter frame, including all locals appended to ``log`` before the deopt.
#
# Tags: ['block-stack', 'deopt', 'exception', 'finally']
def work():
    log = []
    try:
        for i in range(1000):
            if i == 500:
                x = "string"  # type change -> deopt
            else:
                x = i
            log.append(x)
    finally:
        log.append(("finally", len(log)))
    return log

r = work()
assert len(r) == 1001, len(r)
assert r[0] == 0
assert r[499] == 499
assert r[500] == "string"
assert r[501] == 501
assert r[999] == 999
assert r[-1] == ("finally", 1000)

