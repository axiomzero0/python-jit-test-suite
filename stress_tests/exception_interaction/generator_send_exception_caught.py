# -*- coding: utf-8 -*-
# stress test: generator_send_exception_caught
# category: exception_interaction
#
# Target: Consumer calls ``g.send(i)`` 999 times and ``g.throw(ValueError)`` once. The generator catches the thrown exception, adjusts state, and resumes. A JIT that compiled the generator body must deopt at the yield and inject the thrown exception at the correct suspension point.
#
# Tags: ['exception', 'generator', 'injection', 'send', 'throw']
def gen():
    acc = 0
    while True:
        try:
            x = yield acc
            acc += x
        except ValueError:
            acc -= 1

g = gen()
next(g)  # prime: runs to first yield, returns acc=0

results = []
for i in range(1000):
    if i == 500:
        results.append(g.throw(ValueError("boom")))
    else:
        results.append(g.send(i))

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
assert len(results) == 1000
g.close()

