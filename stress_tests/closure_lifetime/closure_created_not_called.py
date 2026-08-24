# -*- coding: utf-8 -*-
# stress test: closure_created_not_called
# category: closure_lifetime
# opt_state: (runs across all 6 states)
#
# Target: A closure is created and assigned, but the inner closure that uses the cell is never called for a long time. The JIT must keep the cell (and the captured big data) alive even if no read has occurred, since a future call would need it.
#
# Tags: ['GC', 'cell-lifetime', 'closure', 'lazy-call']
def make_closures():
    big_data = list(range(1000))
    def used():
        return sum(big_data)
    def unused_for_a_while():
        return len(big_data)
    return used, unused_for_a_while

u, un = make_closures()

# Warm up by calling `used` many times
total = 0
for _ in range(200):
    total += u()
assert total == 200 * sum(range(1000))

# `unused_for_a_while` has never been called yet.
# Now invoke it; the cell must still hold big_data.
assert un() == 1000

# Both closures see the same captured list
assert u() == sum(range(1000))
assert un() == len(list(range(1000)))

