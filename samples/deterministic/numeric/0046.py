# -*- coding: utf-8 -*-
# test_id: num-0000046
# category: numeric
# semantic: numeric
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['add', 'loop_10', 'nan', 'numeric', 'small_int']
def main():
    s = 0
    x = 7
    y = nan
    for i in range(10):
        s = (x + y)
    return s

