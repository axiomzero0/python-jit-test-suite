# -*- coding: utf-8 -*-
# stress test: escape_via_opaque_callback
# category: escape_analysis
#
# Target: An object is passed to a callback resolved through a module-level global at runtime. Because the JIT cannot statically resolve the call target, it must conservatively treat the call as a potential escape point. A flow-insensitive analysis that assumed the inlined callback was the only one would break when the callback swaps and stores the argument.
#
# Tags: ['escape-analysis', 'escape-via-callback', 'identity', 'indirect-call']
# A callable resolved at runtime via a global; the JIT cannot
# statically inline the target.
_handler = None

def set_handler(h):
    global _handler
    _handler = h

class Payload:
    __slots__ = ("data",)
    def __init__(self, d):
        self.data = d

def work():
    p = Payload(42)
    # Indirect call through a global; p may escape.
    return _handler(p)

# First handler: reads p but doesn't store it.
set_handler(lambda p: p.data * 2)
assert work() == 84

# Swap handler at runtime; the JIT must re-resolve and still treat
# p as potentially escaping.
set_handler(lambda p: p.data + 100)
assert work() == 142

# Handler that actually stores p, proving the escape is real.
stored = []
def storing_handler(p):
    stored.append(p)
    return p.data
set_handler(storing_handler)
assert work() == 42
assert len(stored) == 1
assert stored[0].data == 42
assert stored[0] is not None

