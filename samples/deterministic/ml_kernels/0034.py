# -*- coding: utf-8 -*-
# test_id: ml-0000034
# category: ml_kernels
# semantic: ml_kernels
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['elementwise', 'int', 'ml', 'reduction', 'size_32', 'vectorization']
def main():
    a = [i for i in range(32)]
    b = [i for i in range(32)]
    out = [a[i] * b[i] + 1.0 for i in range(32)]
    return out[-1]

