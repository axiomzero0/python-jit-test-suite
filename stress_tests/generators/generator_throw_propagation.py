# -*- coding: utf-8 -*-
# stress test: generator_throw_propagation
# category: generators
# opt_state: (runs across all 6 states)
#
# Target: ``throw()`` must raise the supplied exception *inside* the generator's suspended frame at the exact yield point, not in the caller. A JIT that handles throw by unwinding the caller's frame will skip the generator's own except handlers and return the wrong value.
#
# Tags: ['exception', 'generator', 'throw']
class Boom(Exception):
    pass

def gen():
    received = []
    while True:
        try:
            x = yield
            received.append(x)
        except Boom:
            received.append("caught")
            return received

g = gen()
next(g)          # prime, suspend at `x = yield`
g.send(1)
g.send(2)
# throw() raises Boom at the yield point; the try/except inside the
# generator must catch it, append "caught", and return received.
try:
    g.throw(Boom, "explode")
except StopIteration as e:
    assert e.value == [1, 2, "caught"]
else:
    raise AssertionError("expected StopIteration carrying the return value")

