# -*- coding: utf-8 -*-
# stress test: osr_exit_during_call
# category: osr
#
# Target: OSR exit happens during a function call (the callee returns a value of an unexpected type). The compiled frame must deopt with the correct return value already on the stack.
#
# Tags: ['OSR', 'call', 'exit']
def callee(x):
    if x == 500:
        return "unexpected"
    return x * 2

def caller(n):
    acc = 0
    for i in range(n):
        r = callee(i)
        acc += r if isinstance(r, int) else 0
    return acc

assert caller(1000) == sum(i * 2 for i in range(500)) + sum(i * 2 for i in range(501, 1000))

