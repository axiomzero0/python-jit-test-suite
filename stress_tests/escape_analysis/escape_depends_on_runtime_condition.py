# -*- coding: utf-8 -*-
# stress test: escape_depends_on_runtime_condition
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: Whether an object escapes is determined by a runtime value the JIT cannot predict at compile time. A correct analysis must conservatively assume the object escapes and heap-allocate it on every call. A buggy analysis that speculated on the non-escaping case would corrupt the state observed through the escaped reference.
#
# Tags: ['conditional-escape', 'escape-analysis', 'identity', 'runtime-condition']
class Buffer:
    __slots__ = ("size", "data")
    def __init__(self, size):
        self.size = size
        self.data = list(range(size))

kept = None

def work(keep):
    b = Buffer(5)
    b.data[0] = 99
    if keep:
        global kept
        kept = b  # escapes conditionally, based on runtime flag
    return sum(b.data)

# Non-escaping path.
total = work(False)
assert total == 99 + 1 + 2 + 3 + 4
assert kept is None

# Escaping path.
total = work(True)
assert total == 99 + 1 + 2 + 3 + 4
assert kept is not None
assert kept.size == 5
assert kept.data[0] == 99
assert kept.data == [99, 1, 2, 3, 4]

