# -*- coding: utf-8 -*-
# stress test: del_exception_swallowed_by_gc
# category: exception_interaction
# opt_state: (runs across all 6 states)
#
# Target: ``__del__`` raises RuntimeError during garbage collection. CPython must print a warning to stderr but NOT propagate the exception. A JIT that runs ``__del__`` in a compiled frame must not let the exception escape into the mutator. All destructors must still run.
#
# Tags: ['GC', '__del__', 'exception', 'finalizer', 'swallow']
import gc
import sys
import io

del_log = []

class Tracker:
    def __init__(self, i):
        self.i = i
    def __del__(self):
        del_log.append(self.i)
        raise RuntimeError("in-del-" + str(self.i))

# Capture stderr so the "Exception ignored in __del__" messages
# don't pollute the test output.
_old_stderr = sys.stderr
sys.stderr = io.StringIO()
try:
    def work():
        items = [Tracker(i) for i in range(100)]
        del items   # drops all refs -> __del__ runs for each
        gc.collect()
        return "ok"

    r = work()
finally:
    _captured = sys.stderr.getvalue()
    sys.stderr = _old_stderr

# The RuntimeError inside __del__ must NOT propagate out of work().
assert r == "ok"
# CPython prints "Exception ignored in:" warnings for __del__ exceptions
assert "Exception ignored" in _captured
assert "in-del-0" in _captured
assert "in-del-99" in _captured
# Every Tracker's __del__ must have run exactly once.
assert len(del_log) == 100, len(del_log)
assert set(del_log) == set(range(100))

