# -*- coding: utf-8 -*-
# test_id: num-0000028
# category: numeric
# semantic: numeric
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['add', 'large_float', 'loop_1000', 'numeric', 'small_int']
def main():
    s = 0
    x = 7
    y = 1e+308
    for i in range(1000):
        s = (x + y)
    return s

