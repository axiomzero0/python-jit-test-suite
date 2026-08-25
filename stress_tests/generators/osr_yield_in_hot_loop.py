# -*- coding: utf-8 -*-
# stress test: osr_yield_in_hot_loop
# category: generators
#
# Target: A generator yields from inside a hot loop that the JIT will OSR into. Each ``yield`` suspends the frame mid-loop; on resume the compiled frame must reconstruct the loop counter, the accumulator, and the bytecode position exactly. A JIT that caches loop state across a yield boundary will produce wrong intermediate values.
#
# Tags: ['OSR', 'generator', 'yield']
def gen(n):
    acc = 0
    for i in range(n):
        acc += i
        yield acc

# Large enough to trigger OSR inside the generator body.
g = gen(10000)
last = 0
for v in g:
    last = v
assert last == sum(range(10000))

# Spot-check that each resume produced the correct partial sum, proving
# the accumulator and loop counter survive the suspend/resume cycle.
vals = list(gen(1000))
assert vals[0] == 0
assert vals[1] == 1
assert vals[499] == sum(range(500))
assert vals[500] == sum(range(501))
assert vals[-1] == sum(range(1000))
assert len(vals) == 1000

