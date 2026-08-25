# -*- coding: utf-8 -*-
# stress test: custom_exception_init_raises
# category: exception_interaction
#
# Target: A custom Exception subclass has an ``__init__`` that raises RuntimeError when called with a specific argument. The ``raise BadException('bad')`` statement first evaluates the constructor (which raises RuntimeError), so RuntimeError propagates — not BadException. A JIT must not cache the exception type and skip the constructor.
#
# Tags: ['__init__', 'chain', 'constructor', 'exception', 'hierarchy']
class BadException(Exception):
    def __init__(self, *args):
        if args and args[0] == "bad":
            raise RuntimeError("in-init")
        super().__init__(*args)

def work():
    for i in range(1000):
        if i == 500:
            raise BadException("bad")
    return "ok"

try:
    work()
    assert False, "should raise RuntimeError (from __init__)"
except RuntimeError as e:
    assert str(e) == "in-init"

# Normal case: __init__ does not raise
def work2():
    for i in range(1000):
        if i == 500:
            raise BadException("ok")
    return "ok"

try:
    work2()
    assert False, "should raise BadException"
except BadException as e:
    assert e.args == ("ok",)
    assert isinstance(e, Exception)

# Verify the exception hierarchy is intact
assert issubclass(BadException, Exception)
assert issubclass(BadException, BaseException)

