# -*- coding: utf-8 -*-
# stress test: osr_entry_into_recursive_function
# category: osr
# opt_state: (runs across all 6 states)
#
# Target: OSR into a recursive function. The compiled frame must preserve the call chain so the recursion can return correctly.
#
# Tags: ['OSR', 'recursion']
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

# Large enough to trigger OSR in the top-level call
assert fib(30) == 832040
assert fib(35) == 9227465

