# -*- coding: utf-8 -*-
# stress test: exception_in_finally_replaces_active
# category: exception_interaction
#
# Target: A finally block raises a new exception while another exception is propagating. The new exception replaces the original, and the original is saved as ``__context__``. A JIT must handle this exception-replacement semantics during finally execution.
#
# Tags: ['chain', 'context', 'exception', 'finally', 'replace']
def work():
    log = []
    for i in range(1000):
        try:
            if i == 500:
                raise ValueError("first")
        finally:
            if i == 500:
                raise TypeError("in-finally")  # replaces ValueError
        log.append(i)  # never reached for i == 500
    return log

try:
    work()
    assert False, "should raise TypeError"
except TypeError as e:
    assert str(e) == "in-finally"
    # The original ValueError is preserved as __context__
    assert isinstance(e.__context__, ValueError)
    assert str(e.__context__) == "first"
    # __cause__ is None (no explicit ``from``)
    assert e.__cause__ is None

