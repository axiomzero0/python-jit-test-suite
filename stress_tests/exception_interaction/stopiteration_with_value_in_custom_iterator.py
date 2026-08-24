# -*- coding: utf-8 -*-
# stress test: stopiteration_with_value_in_custom_iterator
# category: exception_interaction
# opt_state: (runs across all 6 states)
#
# Target: A custom iterator raises ``StopIteration(value)``. The for loop must discard the value and terminate cleanly. Manual ``next()`` must expose ``.value``. Inside a generator, ``return X`` is equivalent to ``raise StopIteration(X)``. A JIT that speculates StopIteration has no value would break.
#
# Tags: ['StopIteration', 'exception', 'generator', 'iterator', 'value']
class CustomIter:
    def __init__(self, n):
        self.n = n
        self.i = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self.i >= self.n:
            raise StopIteration("done-at-" + str(self.n))
        v = self.i
        self.i += 1
        return v

# for-loop discards StopIteration value
def work():
    total = 0
    for v in CustomIter(1000):
        total += v
    return total

r = work()
assert r == sum(range(1000))

# manual next() exposes .value
it = CustomIter(5)
vals = []
while True:
    try:
        vals.append(next(it))
    except StopIteration as e:
        assert e.value == "done-at-5"
        break
assert vals == [0, 1, 2, 3, 4]

# generator ``return X`` -> StopIteration.value == X
def gen():
    yield 1
    yield 2
    return "gen-return"

g = gen()
assert next(g) == 1
assert next(g) == 2
try:
    next(g)
    assert False, "should raise StopIteration"
except StopIteration as e:
    assert e.value == "gen-return"

# ``yield from`` swallows the inner StopIteration; the inner return
# value becomes the value of the ``yield from`` expression, NOT the
# outer generator's StopIteration value.
def inner():
    yield 1
    return "from-inner"

def outer():
    result = yield from inner()   # result == "from-inner"
    yield result                   # yields "from-inner"
    yield 2

g2 = outer()
assert next(g2) == 1
assert next(g2) == "from-inner"
assert next(g2) == 2
try:
    next(g2)
    assert False, "should raise StopIteration"
except StopIteration as e:
    # outer had no ``return X``, so StopIteration value is None
    assert e.value is None

