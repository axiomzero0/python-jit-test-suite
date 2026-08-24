# -*- coding: utf-8 -*-
# stress test: deopt_then_reopt_correct
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Function deopts, runs in interpreter, then re-optimizes. The second optimization must produce correct results even though the type profile now includes the deopt-triggering type.
#
# Tags: ['deopt', 'reopt', 'type-profile']
def work(values):
    acc = 0
    for v in values:
        acc += v
    return acc

# Warm up with ints
ints = list(range(100))
for _ in range(200):
    work(ints)

# Deopt with float
mixed = list(range(50)) + [0.5] * 50
assert work(mixed) == sum(mixed)

# Re-optimize with new profile (now includes float)
for _ in range(200):
    work(mixed)
assert work(mixed) == sum(mixed)

# And back to ints (deopt again)
assert work(ints) == sum(ints)

