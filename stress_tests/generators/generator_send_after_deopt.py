# -*- coding: utf-8 -*-
# stress test: generator_send_after_deopt
# category: generators
# opt_state: (runs across all 6 states)
#
# Target: ``send()`` injects a value into the generator at the yield point. The JIT may speculate that the sent value is always an int; sending a float mid-stream forces a deopt. The sent value must land in the right local and the accumulator must transition from int to float without losing precision or the running total.
#
# Tags: ['deopt', 'generator', 'send']
def gen():
    total = 0
    while True:
        v = yield total
        if v is None:
            return
        total += v

g = gen()
assert next(g) == 0          # prime: total starts at 0
assert g.send(10) == 10      # int speculation established
assert g.send(20) == 30      # still int
# Deopt trigger: sent value is now a float.
r = g.send(0.5)
assert r == 30.5
assert isinstance(r, float)
# After deopt the interpreter must keep accumulating correctly.
assert g.send(100) == 130.5
assert isinstance(g.send(0), float)
g.close()

