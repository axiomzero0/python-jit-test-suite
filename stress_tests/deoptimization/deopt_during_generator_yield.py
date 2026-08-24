# -*- coding: utf-8 -*-
# stress test: deopt_during_generator_yield
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Generator yields from inside an optimized loop. Deopt happens at the yield point. The generator's suspended frame must be correctly reconstructed.
#
# Tags: ['deopt', 'generator', 'yield']
def gen(n):
    acc = 0
    for i in range(n):
        if i == 500:
            acc += 0.5  # type change -> deopt
        else:
            acc += i
        yield acc

results = list(gen(1000))
assert len(results) == 1000
assert results[0] == 0
assert results[499] == sum(range(500))
# At i=500: acc was sum(range(500)), then +0.5
assert results[500] == sum(range(500)) + 0.5
# At i=501: acc = sum(range(500)) + 0.5 + 501 (else branch)
assert results[501] == sum(range(500)) + 0.5 + 501
# Final: sum(range(500)) + 0.5 + sum(range(501, 1000))
expected_final = sum(range(500)) + 0.5 + sum(range(501, 1000))
assert results[-1] == expected_final, f"got {results[-1]}, expected {expected_final}"

