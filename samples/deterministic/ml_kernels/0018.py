# -*- coding: utf-8 -*-
# test_id: ml-0000018
# category: ml_kernels
# semantic: ml_kernels
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['elementwise', 'float', 'ml', 'reduction', 'size_1024', 'vectorization']
def main():
    a = [float(i) for i in range(1024)]
    b = [float(i) for i in range(1024)]
    out = [a[i] * b[i] + 1.0 for i in range(1024)]
    return out[-1]

