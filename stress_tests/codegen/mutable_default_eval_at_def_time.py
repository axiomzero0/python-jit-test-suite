# -*- coding: utf-8 -*-
# stress test: mutable_default_eval_at_def_time
# category: codegen
#
# Target: Default argument expressions are evaluated ONCE, at function definition time, not on each call. The same object is reused across calls. This is the classic gotcha: `def f(x=[])` accumulates state across calls.
#
# Tags: ['codegen', 'default-arg', 'shared-default']
# The default list is built once and shared
def f(x=[]):
    x.append(1)
    return x

assert f() == [1]
assert f() == [1, 1]  # same list
assert f() == [1, 1, 1]

# The default object is the same across all calls
default_id = id(f.__defaults__[0])
f()
assert id(f.__defaults__[0]) == default_id

# Same gotcha with dict default
def g(d={}):
    d['count'] = d.get('count', 0) + 1
    return d
assert g() == {'count': 1}
assert g() == {'count': 2}
assert g() == {'count': 3}

# Same gotcha with set default
def h(s=set()):
    s.add(len(s))
    return s
result1 = h()
result2 = h()
result3 = h()
assert len(result3) == 3
assert result1 is result2 is result3

# Sentinel pattern: use None to get a fresh default per call
def safe(x=None):
    if x is None:
        x = []
    x.append(1)
    return x
assert safe() == [1]
assert safe() == [1]  # new list each call
assert safe() is not safe()

# Mutable default evaluated at def time, not call time
counter = [0]
def make():
    counter[0] += 1
    return counter[0]
def k(x=make()):
    return x
# make() was called once, at def time
assert k() == 1
assert k() == 1  # default unchanged
# counter was incremented once
assert counter[0] == 1
# Define another function -> make() called again
def m(x=make()):
    return x
assert m() == 2  # counter[0] is now 2
assert counter[0] == 2

