# -*- coding: utf-8 -*-
# stress test: generator_partial_iteration_delayed_resume
# category: generators
#
# Target: A generator is advanced a few steps, then left suspended while substantial unrelated work runs (including creating and exhausting many other generators). On resume the original generator's frame must be intact. A JIT that reuses generator frame slots aggressively can corrupt the dormant frame.
#
# Tags: ['generator', 'resume', 'suspension']
def gen():
    for i in range(5):
        yield i

g = gen()
first = next(g)    # 0
second = next(g)    # 1

# Lots of unrelated generator activity that could pressure frame caches.
others = [list(gen()) for _ in range(500)]
assert all(len(o) == 5 for o in others)
assert others[0] == [0, 1, 2, 3, 4]

# Resume the original generator: its state must be untouched.
third = next(g)    # 2
fourth = next(g)   # 3
fifth = next(g)    # 4

assert (first, second, third, fourth, fifth) == (0, 1, 2, 3, 4)

try:
    next(g)
    raise AssertionError("expected StopIteration")
except StopIteration:
    pass

# Resuming an exhausted generator must keep raising StopIteration.
try:
    next(g)
    raise AssertionError("expected StopIteration again")
except StopIteration:
    pass

