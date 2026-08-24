# -*- coding: utf-8 -*-
# test_id: ml-0000027
# category: ml_kernels
# semantic: ml_kernels
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: very_hot
# tags: ['elementwise', 'int', 'ml', 'reduction', 'size_8', 'vectorization']
def main():
    a = [i for i in range(8)]
    b = [i for i in range(8)]
    out = [a[i] * b[i] + 1.0 for i in range(8)]
    return out[-1]

