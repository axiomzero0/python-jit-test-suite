# -*- coding: utf-8 -*-
# stress test: escape_via_global_assignment
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: An object is stored into a module-level global. The JIT must NOT scalar-replace it: the object outlives the frame and is observable from any code that reads the global. A naive analysis that only scans local uses would miss this escape channel and break identity / mutation semantics.
#
# Tags: ['escape-analysis', 'escape-via-global', 'identity']
class Box:
    __slots__ = ("value",)
    def __init__(self, v):
        self.value = v

last_box = None

def make_box(v):
    global last_box
    b = Box(v)
    last_box = b  # b escapes via the global
    return b.value

assert make_box(1) == 1
assert last_box.value == 1
assert make_box(2) == 2
assert last_box.value == 2

# Distinct heap identities per call: the previous global must be
# untouched when a new Box is stored.
first = last_box        # first -> Box(2)
make_box(3)             # last_box -> Box(3)
assert first is not last_box
assert first.value == 2     # original box untouched by make_box(3)
assert last_box.value == 3

