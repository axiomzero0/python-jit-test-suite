# -*- coding: utf-8 -*-
# stress test: osr_exit_with_finally
# category: osr
#
# Target: Hot loop inside a try/finally. OSR exit (deopt) happens inside the loop. The finally block must execute with the correct reconstructed state.
#
# Tags: ['OSR', 'exit', 'finally', 'unwind']
def work():
    finally_ran = [False]
    try:
        acc = 0
        for i in range(1000):
            acc += i
            if i == 500:
                # Simulate a deopt trigger (different type)
                acc += 0.5
    finally:
        finally_ran[0] = True
    return acc, finally_ran[0]

acc, ran = work()
assert ran is True
assert acc == sum(range(501)) + 0.5 + sum(range(501, 1000))

