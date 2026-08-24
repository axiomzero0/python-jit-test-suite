# -*- coding: utf-8 -*-
# stress test: nested_generators
# category: generators
# opt_state: (runs across all 6 states)
#
# Target: A generator that yields from another generator builds two suspended frames chained together. The outer frame's yield-from state (which sub-generator it's delegating to) must be preserved across each resume so values flow through in the right order with the outer's own bookend yields.
#
# Tags: ['generator', 'nesting', 'yield-from']
def inner(n):
    for i in range(n):
        yield ("inner", i)

def outer(n):
    yield ("outer-start", -1)
    yield from inner(n)
    yield ("outer-end", n)

result = list(outer(5))
assert result[0] == ("outer-start", -1)
assert result[1] == ("inner", 0)
assert result[2] == ("inner", 1)
assert result[5] == ("inner", 4)
assert result[6] == ("outer-end", 5)
assert len(result) == 7

# Verify send() is forwarded to the delegated sub-generator, and the
# sub-generator's return value becomes the yield-from result.
def sink():
    acc = 0
    while True:
        v = yield acc
        if v is None:
            return acc
        acc += v

def wrapper():
    total = yield from sink()
    yield ("total", total)

w = wrapper()
assert next(w) == 0          # sink yields acc=0
assert w.send(5) == 5       # acc -> 5, yields 5
assert w.send(10) == 15     # acc -> 15, yields 15
# send(None) makes sink `return acc` (15); yield-from binds total=15;
# wrapper then yields ("total", 15).
assert w.send(None) == ("total", 15)
# wrapper is now exhausted.
try:
    next(w)
    raise AssertionError("expected StopIteration")
except StopIteration:
    pass

