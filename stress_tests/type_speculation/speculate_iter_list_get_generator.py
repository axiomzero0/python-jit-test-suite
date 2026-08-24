# -*- coding: utf-8 -*-
# stress test: speculate_iter_list_get_generator
# category: type_speculation
# opt_state: (runs across all 6 states)
#
# Target: JIT speculates `for x in obj` iterates a list (fast path via PyList_Type). Then a generator is passed. The JIT must deopt and use the generator's __next__ protocol.
#
# Tags: ['generator', 'iterator', 'type-speculation']
def consume(obj):
    total = 0
    for x in obj:
        total += x
    return total

# Warm up with list
lst = list(range(100))
for _ in range(1000):
    consume(lst)

# Now pass a generator
def gen(n):
    for i in range(n):
        yield i

assert consume(gen(100)) == 4950
assert consume(gen(10)) == 45

