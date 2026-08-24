# -*- coding: utf-8 -*-
# stress test: stopiteration_value_becomes_yield_from_result
# category: generators
# opt_state: (runs across all 6 states)
#
# Target: When a sub-generator terminates, the value it carries on its StopIteration becomes the result of the enclosing ``yield from`` expression. A JIT that drops the StopIteration value (or binds ``None``) will get the wrong result. Tested both via ``return`` in a generator and via a plain iterator that explicitly raises ``StopIteration(value)``.
#
# Tags: ['StopIteration', 'generator', 'yield-from']
def sub():
    yield 1
    yield 2
    return "final-value"

def outer():
    result = yield from sub()
    yield ("got", result)

assert list(outer()) == [1, 2, ("got", "final-value")]

# Directly observe the StopIteration.value to confirm the mechanism.
g = sub()
assert next(g) == 1
assert next(g) == 2
try:
    next(g)
except StopIteration as e:
    assert e.value == "final-value"
else:
    raise AssertionError("expected StopIteration")

# A non-generator iterator that raises StopIteration(value) must also
# feed its value into yield from.
class CustomIter:
    def __init__(self, items, final):
        self._items = list(items)
        self._final = final
        self._i = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self._i < len(self._items):
            v = self._items[self._i]
            self._i += 1
            return v
        raise StopIteration(self._final)

def outer2():
    result = yield from CustomIter([1, 2, 3], "done")
    yield result

assert list(outer2()) == [1, 2, 3, "done"]

