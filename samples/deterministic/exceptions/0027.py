# -*- coding: utf-8 -*-
# test_id: exc-0000027
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: very_hot
# tags: ['deoptimization', 'except_in_loop', 'exception']
caught = 0
for i in range(10):
    try:
        if i % 2 == 0:
            raise ValueError(i)
    except ValueError:
        caught += 1
assert caught == 5

