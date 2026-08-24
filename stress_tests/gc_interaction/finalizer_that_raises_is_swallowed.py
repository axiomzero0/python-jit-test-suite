# -*- coding: utf-8 -*-
# stress test: finalizer_that_raises_is_swallowed
# category: gc_interaction
# opt_state: (runs across all 6 states)
#
# Target: An exception raised in __del__ must be swallowed by the runtime (printed to stderr, not propagated). If the JIT's finalizer dispatch let the exception escape into the dealloc path, the caller would see a spurious RuntimeError.
#
# Tags: ['GC', 'exception', 'finalizer']
import contextlib
import gc
import io

class BadFinalizer:
    count = 0
    def __del__(self):
        BadFinalizer.count += 1
        raise RuntimeError("boom in finalizer")

def work():
    for _ in range(100):
        f = BadFinalizer()

err = io.StringIO()
with contextlib.redirect_stderr(err):
    work()
    gc.collect()

# Finalizer ran for every object.
assert BadFinalizer.count == 100, (
    f"finalizer ran {BadFinalizer.count} times, expected 100"
)
# Exception was printed to stderr, not propagated (reaching here proves it).
output = err.getvalue()
assert (
    "Exception ignored" in output
    or "RuntimeError" in output
    or "boom" in output
), f"expected error in stderr, got: {output!r}"

