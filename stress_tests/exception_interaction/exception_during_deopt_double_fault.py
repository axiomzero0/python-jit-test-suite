# -*- coding: utf-8 -*-
# stress test: exception_during_deopt_double_fault
# category: exception_interaction
#
# Target: Double-fault scenario: while handling a ValueError, the except handler triggers a type-speculation deopt (x changes from int to str) and then raises a *different* exception (RuntimeError). The JIT must preserve the original exception as __context__ of the new one across the deopt boundary.
#
# Tags: ['chain', 'context', 'deopt', 'double-fault', 'exception']
def work():
    log = []
    contexts = []
    for i in range(1000):
        try:
            try:
                if i == 500:
                    raise ValueError("first")
                x = i
            except ValueError:
                # Trigger deopt via type change, then raise a new exception.
                x = "string"
                raise RuntimeError("second")
            log.append(x)
        except RuntimeError as e:
            contexts.append(e.__context__)
            log.append(("recovered", i))
            continue
    return log, contexts

log, contexts = work()
assert len(log) == 1000, len(log)
assert log[0] == 0
assert log[499] == 499
assert log[500] == ("recovered", 500)
assert log[501] == 501
assert log[999] == 999
assert len(contexts) == 1
assert isinstance(contexts[0], ValueError)
assert str(contexts[0]) == "first"

