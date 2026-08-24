# -*- coding: utf-8 -*-
# stress test: closure_shares_mutable_list
# category: closure_lifetime
# opt_state: (runs across all 6 states)
#
# Target: Two closures share a cell that holds a mutable list. Mutation through one closure must be visible to the other, since they share the same cell (and hence the same list object).
#
# Tags: ['closure', 'mutable', 'shared-cell']
def make_append_get_pair():
    shared = []
    def append(v):
        shared.append(v)
        return len(shared)
    def get():
        return list(shared)
    return append, get

a, g = make_append_get_pair()

assert a(1) == 1
assert a(2) == 2
assert g() == [1, 2]

# Mutation through `a` is visible to `g` (same list, same cell)
a(3)
a(4)
assert g() == [1, 2, 3, 4]

# Independent pairs get independent cells/lists
a2, g2 = make_append_get_pair()
a2(99)
assert g2() == [99]
assert g() == [1, 2, 3, 4]  # unchanged

