# -*- coding: utf-8 -*-
# stress test: escape_via_exception_arg
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: An object is raised as the argument of an exception. The exception object (and its args) is reachable from any frame that catches the exception, so the JIT must preserve the heap allocation. A scalar-replaced object would be visible to the catch block as stale or invalid memory, breaking the catch handler.
#
# Tags: ['escape-analysis', 'escape-via-exception', 'exception', 'identity']
class Result:
    __slots__ = ("code", "msg")
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

def work(fail):
    r = Result(0, "ok")
    if fail:
        raise ValueError(r)  # r escapes via exception arg
    return r

# Normal path: r escapes via return.
ok = work(False)
assert ok.code == 0
assert ok.msg == "ok"

# Exception path: r must be the heap object carried by the exception.
try:
    work(True)
    assert False, "should have raised"
except ValueError as exc:
    r = exc.args[0]
    assert isinstance(r, Result)
    assert r.code == 0
    assert r.msg == "ok"
    # Mutating the caught object must persist.
    r.code = 99
    assert r.code == 99

