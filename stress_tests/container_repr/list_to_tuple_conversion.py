# -*- coding: utf-8 -*-
# stress test: list_to_tuple_conversion
# category: container_repr
# opt_state: (runs across all 6 states)
#
# Target: A list is converted to a tuple via tuple(lst). The two containers have different internal representations (list has a mutable PyObject* array with capacity; tuple has an immutable array of fixed size). Mutating the source list after conversion must not affect the tuple.
#
# Tags: ['container', 'conversion', 'list', 'tuple']
lst = [1, 2, 3, 4, 5]
t = tuple(lst)
assert t == (1, 2, 3, 4, 5)
assert isinstance(t, tuple)
assert isinstance(lst, list)

# Mutate the list; tuple must be unaffected
lst.append(6)
lst[0] = 99
assert lst == [99, 2, 3, 4, 5, 6]
assert t == (1, 2, 3, 4, 5)

# Tuples from various sources
assert tuple("abc") == ('a', 'b', 'c')
assert tuple(range(5)) == (0, 1, 2, 3, 4)
assert tuple(x * 2 for x in [1, 2, 3]) == (2, 4, 6)
assert tuple([]) == ()
assert tuple([(1, 2), (3, 4)]) == ((1, 2), (3, 4))

# tuple() on a tuple returns the same object (immutable)
t2 = (1, 2, 3)
assert tuple(t2) is t2

# tuple from a set (order may vary but elements are preserved)
s = {1, 2, 3}
ts = tuple(s)
assert sorted(ts) == [1, 2, 3]

