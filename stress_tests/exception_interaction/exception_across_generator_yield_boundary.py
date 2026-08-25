# -*- coding: utf-8 -*-
# stress test: exception_across_generator_yield_boundary
# category: exception_interaction
#
# Target: A generator raises ValueError on iteration 500, caught internally by a try/except around the yield. The JIT-compiled generator body must deopt at the yield point, inject the exception, and resume correctly so the consumer sees the right accumulated values.
#
# Tags: ['exception', 'generator', 'propagation', 'yield']
def gen(n):
    acc = 0
    for i in range(n):
        try:
            if i == 500:
                raise ValueError("inner")
            acc += i
        except ValueError:
            acc -= 1
        yield acc

results = list(gen(1000))
assert len(results) == 1000

# Independently simulate expected values
expected = []
sim = 0
for i in range(1000):
    if i == 500:
        sim -= 1
    else:
        sim += i
    expected.append(sim)

assert results == expected
assert results[0] == 0
assert results[499] == sum(range(500))
assert results[500] == sum(range(500)) - 1
assert results[501] == sum(range(500)) - 1 + 501
assert results[-1] == sum(range(500)) - 1 + sum(range(501, 1000))

