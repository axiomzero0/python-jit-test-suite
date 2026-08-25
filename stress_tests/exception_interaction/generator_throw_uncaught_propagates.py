# -*- coding: utf-8 -*-
# stress test: generator_throw_uncaught_propagates
# category: exception_interaction
#
# Target: ``g.throw(ValueError)`` is called on a generator that does NOT catch the exception. The exception must propagate out of throw() to the caller, and the generator must be left in the closed state so subsequent next()/send() raises StopIteration.
#
# Tags: ['closed', 'exception', 'generator', 'propagation', 'throw']
def gen():
    acc = 0
    while True:
        x = yield acc
        acc += x

g = gen()
assert next(g) == 0       # prime
assert g.send(10) == 10   # acc = 0 + 10 = 10

# throw an exception the generator does not catch
try:
    g.throw(ValueError("not-caught"))
    assert False, "throw should propagate ValueError"
except ValueError as e:
    assert str(e) == "not-caught"

# generator is now closed
try:
    next(g)
    assert False, "closed generator should raise StopIteration"
except StopIteration:
    pass

# throw on a closed generator re-raises the thrown exception
try:
    g.throw(RuntimeError("after-close"))
    assert False
except RuntimeError as e:
    assert str(e) == "after-close"

