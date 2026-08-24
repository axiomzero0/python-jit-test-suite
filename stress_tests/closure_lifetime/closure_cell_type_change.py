# -*- coding: utf-8 -*-
# stress test: closure_cell_type_change
# category: closure_lifetime
# opt_state: (runs across all 6 states)
#
# Target: The captured cell variable starts as int and is reassigned to str, then list, then dict. A JIT that speculates the cell holds an int (and unboxes it) must deopt and rebox on each type change, preserving the new value across subsequent reads.
#
# Tags: ['closure', 'deopt', 'rebox', 'type-change']
def make_reader_setter():
    state = 0
    def reader():
        return state
    def setter(v):
        nonlocal state
        state = v
    return reader, setter

r, s = make_reader_setter()

# Warm up with ints
for i in range(100):
    s(i)
    assert r() == i

# Now change type to str (deopt must rebox)
s("hello")
assert r() == "hello"

# Change to list
s([1, 2, 3])
assert r() == [1, 2, 3]
assert r() is not [1, 2, 3]  # same list object each call

# Change to dict
s({"k": "v"})
assert r() == {"k": "v"}

# Back to int
s(42)
assert r() == 42
assert isinstance(r(), int)

