# -*- coding: utf-8 -*-
# test_id: num-0000020
# category: numeric
# semantic: numeric
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['add', 'loop_1', 'numeric', 'small_float', 'small_int']
def main():
    s = 0
    x = 7
    y = 1.5
    for i in range(1):
        s = (x + y)
    return s

