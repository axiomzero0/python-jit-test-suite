# -*- coding: utf-8 -*-
# stress test: closure_cell_deleted_then_accessed
# category: closure_lifetime
#
# Target: A closure cell is deleted via `nonlocal x; del x`. Subsequent reads of the same cell from a sibling closure must raise NameError (the cell is now empty). A JIT that elides the cell-empty check would return a stale or garbage value.
#
# Tags: ['NameError', 'cell-empty', 'closure', 'del']
def make_getter_deleter():
    x = 10
    def get():
        return x
    def delete():
        nonlocal x
        del x
    return get, delete

g, d = make_getter_deleter()
assert g() == 10

# Delete the cell binding
d()

# Subsequent reads must raise NameError
raised = 0
for _ in range(5):
    try:
        g()
    except NameError:
        raised += 1
assert raised == 5

# Re-creating a fresh closure restores the cell
g2, d2 = make_getter_deleter()
assert g2() == 10

