# -*- coding: utf-8 -*-
# stress test: osr_reentry_after_deopt
# category: osr
# opt_state: (runs across all 6 states)
#
# Target: Function deopts mid-loop. After deopt, the interpreter runs for a while, then the JIT re-optimizes and OSRs back in. The second optimization must be correct.
#
# Tags: ['OSR', 'reentry', 'reopt']
def work(values):
    acc = 0
    for v in values:
        acc += v
    return acc

# Warm up
ints = list(range(1000))
for _ in range(100):
    work(ints)

# Deopt
mixed = list(range(500)) + [0.5] * 500
assert work(mixed) == sum(mixed)

# Re-optimize
ints = list(range(2000))
for _ in range(100):
    work(ints)
assert work(ints) == sum(ints)

