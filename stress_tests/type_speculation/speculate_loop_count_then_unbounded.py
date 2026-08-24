# -*- coding: utf-8 -*-
# stress test: speculate_loop_count_then_unbounded
# category: type_speculation
# opt_state: (runs across all 6 states)
#
# Target: JIT speculates `range(N)` produces a known-size iterator and may unroll the loop. Then a generator of unknown size is passed. The deopt must handle the unbounded iteration.
#
# Tags: ['iterator', 'loop-count', 'type-speculation']
def total(it):
    s = 0
    for x in it:
        s += x
    return s

# Warm up with range (known size)
for _ in range(100):
    total(range(100))

# Now generator (unknown size)
def gen():
    i = 0
    while i < 73:  # weird bound
        yield i
        i += 1

assert total(gen()) == sum(range(73))

# And a list
assert total(list(range(50))) == 1225

# And a string (iterates chars)
assert total(ord(c) for c in "abc") == ord('a') + ord('b') + ord('c')

