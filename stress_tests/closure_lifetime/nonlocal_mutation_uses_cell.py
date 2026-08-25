# -*- coding: utf-8 -*-
# stress test: nonlocal_mutation_uses_cell
# category: closure_lifetime
#
# Target: A closure mutates its captured variable via `nonlocal`. The JIT cannot keep the variable in a stack slot or as a constant; it must go through the cell every time. After many increments the counter must read the correct accumulated value, not a stale snapshot.
#
# Tags: ['cell', 'closure', 'mutation', 'nonlocal']
def make_counter():
    count = 0
    def inc():
        nonlocal count
        count += 1
        return count
    return inc

c = make_counter()
for _ in range(100):
    c()

assert c() == 101
assert c() == 102

# Independent counters get independent cells
c2 = make_counter()
assert c2() == 1
assert c() == 103

