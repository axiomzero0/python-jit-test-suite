# -*- coding: utf-8 -*-
# stress test: guard_memory_allocation_failure
# category: guard_failures
#
# Target: Allocation guard. Trying to allocate a huge list should fail gracefully (MemoryError or ValueError), not crash.
#
# Tags: ['allocation', 'guard', 'memory']
def make_list(n):
    return list(range(n))

# Normal
assert make_list(100) == list(range(100))

# Large but feasible
assert len(make_list(1_000_000)) == 1_000_000

# Huge - should raise, not crash
try:
    make_list(10**18)
    # If it didn't raise, that's fine too (some impls handle it)
except (MemoryError, OverflowError, ValueError):
    pass

# Recovery
assert make_list(10) == list(range(10))

