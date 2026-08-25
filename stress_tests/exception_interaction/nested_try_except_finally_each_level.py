# -*- coding: utf-8 -*-
# stress test: nested_try_except_finally_each_level
# category: exception_interaction
#
# Target: Three nested try/except/finally blocks. An exception raised in the innermost try is caught by the middle except, which re-raises a different exception, caught by the outer except. The finally blocks must run in the correct order as exceptions propagate. A JIT must reconstruct the full block stack on deopt.
#
# Tags: ['block-stack', 'exception', 'finally', 'nested-try', 'rethrow']
def work():
    log = []
    try:                                   # outer
        try:                               # middle
            try:                           # inner
                for i in range(1000):
                    if i == 500:
                        raise ValueError("inner")
            finally:                       # inner-finally
                log.append("inner-finally")
        except ValueError:                # middle-except
            log.append("inner-caught")
            raise TypeError("rethrown")
        finally:                           # middle-finally
            log.append("middle-finally")
    except TypeError:                      # outer-except
        log.append("outer-caught")
    finally:                               # outer-finally
        log.append("outer-finally")
    return log

r = work()
expected = [
    "inner-finally",
    "inner-caught",
    "middle-finally",
    "outer-caught",
    "outer-finally",
]
assert r == expected, r

