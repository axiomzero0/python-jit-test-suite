# -*- coding: utf-8 -*-
# stress test: generator_survives_gc
# category: generators
#
# Target: A generator is suspended partway through (its frame holds live references to locals). A GC cycle runs while it is suspended. The generator frame must survive collection and all its locals must remain valid on resume. A JIT that over-eagerly reclaims or relocates the suspended frame will corrupt the resumed state.
#
# Tags: ['GC', 'generator', 'suspension', 'weakref']
import gc
import weakref

def gen():
    big = list(range(1000))   # a non-trivial local that the frame pins
    for i in range(10):
        yield big[i]

g = gen()
first = next(g)
second = next(g)

# Hold only a weak ref to the generator and force a full collection.
ref = weakref.ref(g)
# Allocate a lot of garbage to pressure the collector.
_ = [list(range(100)) for _ in range(2000)]
gc.collect()

assert ref() is g, "generator must not be collected while suspended"
third = next(g)
assert first == 0 and second == 1 and third == 2

# Resume after GC: the remaining values must come from the original `big`.
rest = list(g)
assert rest == [3, 4, 5, 6, 7, 8, 9]

