# -*- coding: utf-8 -*-
# test_id: ml-0000010
# category: ml_kernels
# semantic: ml_kernels
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['elementwise', 'float', 'ml', 'reduction', 'size_32', 'vectorization']
def main():
    a = [float(i) for i in range(32)]
    b = [float(i) for i in range(32)]
    out = [a[i] * b[i] + 1.0 for i in range(32)]
    return out[-1]

