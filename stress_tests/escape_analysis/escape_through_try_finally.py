# -*- coding: utf-8 -*-
# stress test: escape_through_try_finally
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: An object is allocated in a try block and referenced in the corresponding finally. The finally runs on every exit path (normal return, exception, early return), so the object's lifetime must span the try/finally boundary. A buggy analysis that scoped lifetime to just the try block would observe garbage in the finally.
#
# Tags: ['escape-analysis', 'exception', 'lifetime', 'try-finally']
class Resource:
    __slots__ = ("opened", "closed")
    def __init__(self):
        self.opened = False
        self.closed = False

def work():
    r = Resource()
    try:
        r.opened = True
        # r escapes via return AND must remain live in finally.
        return r
    finally:
        # r must still be the same heap object here.
        r.closed = True

r = work()
assert r.opened is True
assert r.closed is True   # finally ran after the try body

# Also exercise the exception path.
def work_raise():
    r = Resource()
    try:
        r.opened = True
        raise RuntimeError("boom")
    finally:
        r.closed = True
        # Stash for inspection; without this, r would be unreachable
        # after the re-raise and the test could not observe it.
        global _last_resource
        _last_resource = r

_last_resource = None
try:
    work_raise()
    assert False, "should have raised"
except RuntimeError:
    pass

assert _last_resource is not None
assert _last_resource.opened is True
assert _last_resource.closed is True

