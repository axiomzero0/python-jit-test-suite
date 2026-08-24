# -*- coding: utf-8 -*-
# stress test: osr_exit_to_generator
# category: osr
# opt_state: (runs across all 6 states)
#
# Target: Hot loop inside a generator. OSR exit happens while the generator is suspended at a yield. The generator's frame must be correctly reconstructed when resumed.
#
# Tags: ['OSR', 'generator', 'yield']
def gen(n):
    acc = 0
    for i in range(n):
        acc += i
        if i == 500:
            acc += 0.5  # type change -> deopt
        yield acc

g = gen(1000)
results = list(g)
assert len(results) == 1000
assert results[0] == 0
assert results[499] == sum(range(500))
assert results[500] == sum(range(501)) + 0.5
assert results[-1] == sum(range(1000)) + 0.5

