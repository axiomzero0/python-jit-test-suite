# -*- coding: utf-8 -*-
# stress test: recursive_closure_via_cell
# category: closure_lifetime
# opt_state: (runs across all 6 states)
#
# Target: A closure captures itself via the cell so it can recurse. The JIT must not assume the captured name is bound to a constant function pointer; it must dereference the cell on every recursive call.
#
# Tags: ['closure', 'recursion', 'self-capture']
def make_factorial():
    def fact(n):
        if n <= 1:
            return 1
        return n * fact(n - 1)
    return fact

f = make_factorial()
assert f(0) == 1
assert f(1) == 1
assert f(5) == 120
assert f(10) == 3628800
assert f(20) == 2432902008176640000

# Recursion via cell must handle deep stacks (within Python's default limit)
import sys
limit = sys.getrecursionlimit()
assert f(min(100, limit - 100)) > 0

# Two independent recursive closures
g = make_factorial()
assert g(5) == 120

