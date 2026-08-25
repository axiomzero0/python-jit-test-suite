# -*- coding: utf-8 -*-
# stress test: closure_escapes_via_return
# category: closure_lifetime
#
# Target: The enclosing frame returns the closure. After the frame is gone, the cell must persist on the heap. A JIT that stack-allocates the cell would free it on return, leaving the captured value dangling.
#
# Tags: ['cell-lifetime', 'closure', 'escape', 'heap']
def make_adder(n):
    def add(x):
        return x + n
    return add

add5 = make_adder(5)
add10 = make_adder(10)

# The enclosing frames are gone; the captured `n` must persist.
for i in range(100):
    assert add5(i) == i + 5
    assert add10(i) == i + 10

assert add5(1000) == 1005
assert add10(1000) == 1010

# Each closure has its own cell with a distinct value
assert add5(0) != add10(0)

