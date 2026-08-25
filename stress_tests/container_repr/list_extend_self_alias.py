# -*- coding: utf-8 -*-
# stress test: list_extend_self_alias
# category: container_repr
#
# Target: List.extend() is called with the list itself as the argument. CPython's extend handles aliasing correctly by first materializing the iterable. The JIT must not double-iterate or read freed memory.
#
# Tags: ['aliasing', 'container', 'extend', 'list']
lst = [1, 2, 3]
lst.extend(lst)
assert lst == [1, 2, 3, 1, 2, 3]

# Extend with a slice of itself
lst2 = [10, 20, 30]
lst2.extend(lst2[:2])
assert lst2 == [10, 20, 30, 10, 20]

# += is in-place extend
lst3 = [1, 2, 3]
lst3 += lst3
assert lst3 == [1, 2, 3, 1, 2, 3]

# Extend with an iterator over a SNAPSHOT of itself (slice makes a copy)
lst4 = [1, 2, 3]
lst4.extend(iter(lst4[:]))
assert lst4 == [1, 2, 3, 1, 2, 3]

# Extend with a tuple (immutable copy, safe under aliasing)
lst6 = [1, 2, 3]
lst6.extend(tuple(lst6))
assert lst6 == [1, 2, 3, 1, 2, 3]

# Extend with a reversed view of itself (reversed returns a view but
# reads through the live sequence; reversing a 3-element list is finite)
lst7 = [1, 2, 3]
lst7.extend(reversed(lst7))
assert lst7 == [1, 2, 3, 3, 2, 1]

