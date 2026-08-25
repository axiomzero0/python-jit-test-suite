# -*- coding: utf-8 -*-
# stress test: nested_closures_three_levels
# category: closure_lifetime
#
# Target: Three nested closures, each capturing a variable from the frame above it. The JIT must build a chain of cell references and resolve each capture through the appropriate frame, not flatten them into a single scope.
#
# Tags: ['cell-chain', 'closure', 'nested']
def outer(a):
    def middle(b):
        def inner(c):
            return a + b + c
        return inner
    return middle

f = outer(1)(2)
assert f(3) == 6
assert f(10) == 13

g = outer(100)(20)
assert g(3) == 123

# Many distinct inner closures
results = []
for i in range(10):
    for j in range(10):
        results.append(outer(i)(j)(0))
expected = [i + j for i in range(10) for j in range(10)]
assert results == expected

