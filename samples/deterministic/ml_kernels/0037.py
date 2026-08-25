# -*- coding: utf-8 -*-
# test_id: ml-0000037
# category: ml_kernels
# semantic: ml_kernels
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['elementwise', 'int', 'ml', 'reduction', 'size_128', 'vectorization']
def main():
    a = [i for i in range(128)]
    b = [i for i in range(128)]
    out = [a[i] * b[i] + 1.0 for i in range(128)]
    return out[-1]

