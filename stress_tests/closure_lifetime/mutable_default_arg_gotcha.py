# -*- coding: utf-8 -*-
# stress test: mutable_default_arg_gotcha
# category: closure_lifetime
#
# Target: The classic `def f(x=[])` gotcha: the default is evaluated once at def time and shared across all calls. A JIT that re-evaluates the default per call (or allocates a fresh list per call) would diverge from CPython semantics.
#
# Tags: ['closure', 'default-arg', 'shared-default']
def make_appender():
    def append_to(x, acc=[]):
        acc.append(x)
        return acc
    return append_to

app = make_appender()
assert app(1) == [1]
assert app(2) == [1, 2]
assert app(3) == [1, 2, 3]

# The default list is the same object across calls
default_id = id(app.__defaults__[0])
app(4)
assert id(app.__defaults__[0]) == default_id

# Same gotcha with dict default
def make_incrementer():
    def incr(key, counts={}):
        counts[key] = counts.get(key, 0) + 1
        return counts[key]
    return incr

incr = make_incrementer()
assert incr('a') == 1
assert incr('a') == 2
assert incr('b') == 1
assert incr('a') == 3

# Independent functions get independent defaults
incr2 = make_incrementer()
assert incr2('a') == 1

