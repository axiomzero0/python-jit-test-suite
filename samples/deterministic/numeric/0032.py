# -*- coding: utf-8 -*-
# test_id: num-0000032
# category: numeric
# semantic: numeric
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['add', 'loop_100', 'numeric', 'small_int', 'subnormal']
def main():
    s = 0
    x = 7
    y = 5e-324
    for i in range(100):
        s = (x + y)
    return s

