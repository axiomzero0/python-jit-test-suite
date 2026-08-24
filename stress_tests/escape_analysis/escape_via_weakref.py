# -*- coding: utf-8 -*-
# stress test: escape_via_weakref
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: An object is referenced through a weakref. The weakref implementation requires a heap-allocated object so that the GC can notify the weakref when the object dies. A scalar-replacement that eliminated the heap object would cause the weakref to return None prematurely, breaking any code that relies on liveness checks.
#
# Tags: ['GC', 'escape-analysis', 'identity', 'lifetime', 'weakref']
import weakref

class Cached:
    # __weakref__ slot is required for the class to participate in
    # weak references when __slots__ is in use.
    __slots__ = ("key", "value", "__weakref__")
    def __init__(self, k, v):
        self.key = k
        self.value = v

def work():
    c = Cached("answer", 42)
    ref = weakref.ref(c)
    # c must stay alive as a heap object while we hold the weakref.
    # If the JIT had eliminated c, ref() would return None here.
    assert ref() is not None
    assert ref().value == 42
    # The weakref must point to the same object as c.
    assert ref() is c
    # Mutations through c must be visible through the weakref.
    c.value = 100
    assert ref().value == 100
    return ref().value

assert work() == 100

# Verify the weakref dies once the strong reference goes away.
def make_only_weak():
    c = Cached("ephemeral", 7)
    ref = weakref.ref(c)
    return ref

import gc
ref = make_only_weak()
gc.collect()
# c is unreachable, so the weakref should now be dead.
assert ref() is None

