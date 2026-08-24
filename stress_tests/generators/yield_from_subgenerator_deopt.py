# -*- coding: utf-8 -*-
# stress test: yield_from_subgenerator_deopt
# category: generators
# opt_state: (runs across all 6 states)
#
# Target: Outer generator delegates to an inner generator via ``yield from``. The inner generator deopts mid-stream (a value of a different type flows through). The deopt must happen in the inner frame while the outer frame stays suspended, and every value must still be forwarded to the consumer in order.
#
# Tags: ['deopt', 'generator', 'yield-from']
def inner(values):
    for v in values:
        yield v * 2

def outer(values):
    yield from inner(values)

# Mix ints with a float exactly in the middle to force a deopt in `inner`.
data = list(range(500)) + [0.5] + list(range(500, 1000))
result = list(outer(data))
expected = [v * 2 for v in data]
assert result == expected
assert isinstance(result[0], int)
assert isinstance(result[500], float)
assert isinstance(result[501], int)
assert len(result) == len(data)

