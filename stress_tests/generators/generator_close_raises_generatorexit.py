# -*- coding: utf-8 -*-
# stress test: generator_close_raises_generatorexit
# category: generators
#
# Target: ``close()`` must raise ``GeneratorExit`` at the suspended yield point so that any enclosing ``finally`` runs. A JIT that tears down the generator frame without synthesizing the GeneratorExit will skip cleanup. Also verifies that closing an already-finished generator is a silent no-op.
#
# Tags: ['GeneratorExit', 'close', 'finally', 'generator']
cleanup = []

def gen():
    try:
        while True:
            yield 1
    finally:
        cleanup.append("finally")
    # Unreachable, but documents intent.
    yield 2

g = gen()
assert next(g) == 1
assert next(g) == 1
g.close()
assert cleanup == ["finally"]

# Closing an already-closed generator must be a no-op (no second finally).
g.close()
assert cleanup == ["finally"]

# Closing a never-started generator must not run the body at all.
g2 = gen()
g2.close()
assert cleanup == ["finally"]

