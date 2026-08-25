# -*- coding: utf-8 -*-
# test_id: exc-0000037
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: generator
# opt_state: warm
# tags: ['deoptimization', 'exc_in_generator', 'exception']
def gen():
    yield 1
    raise ValueError('gen')
    yield 2
g = gen()
assert next(g) == 1
try:
    next(g)
except ValueError:
    pass

