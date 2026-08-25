# -*- coding: utf-8 -*-
# stress test: two_closures_share_one_cell
# category: closure_lifetime
#
# Target: Two closures defined in the same frame share the same cell for a captured variable. Mutation through one closure is immediately visible to the other. The JIT cannot keep a private cached copy of the value in either closure.
#
# Tags: ['aliasing', 'closure', 'shared-cell']
def make_get_set():
    x = 1
    def get():
        return x
    def set_(v):
        nonlocal x
        x = v
        return x
    return get, set_

g, s = make_get_set()
assert g() == 1

# Mutation through `s` is visible to `g`
assert s(42) == 42
assert g() == 42

# Type change is also visible
s("abc")
assert g() == "abc"

s(None)
assert g() is None

s(0)
assert g() == 0

