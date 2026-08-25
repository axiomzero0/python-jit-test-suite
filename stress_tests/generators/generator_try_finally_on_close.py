# -*- coding: utf-8 -*-
# stress test: generator_try_finally_on_close
# category: generators
#
# Target: ``try/finally`` wrapping a ``yield`` must run the finally block on ``close()`` (GeneratorExit), on normal exhaustion, and on exception propagation. A JIT that models the block stack incorrectly during generator teardown will skip the finally or run it twice.
#
# Tags: ['close', 'exception', 'finally', 'generator']
log = []

def gen():
    try:
        yield 1
        yield 2
        yield 3
    finally:
        log.append("cleanup")

# Case 1: close() mid-iteration runs finally exactly once.
g = gen()
assert next(g) == 1
assert next(g) == 2
g.close()
assert log == ["cleanup"]

# Case 2: normal exhaustion also runs finally exactly once.
log.clear()
g2 = gen()
assert list(g2) == [1, 2, 3]
assert log == ["cleanup"]

# Case 3: an exception raised inside the body propagates and finally runs.
log.clear()
def gen_exc():
    try:
        yield 1
        raise ValueError("inside")
    finally:
        log.append("cleanup")

g3 = gen_exc()
next(g3)
try:
    next(g3)
except ValueError:
    pass
assert log == ["cleanup"]

