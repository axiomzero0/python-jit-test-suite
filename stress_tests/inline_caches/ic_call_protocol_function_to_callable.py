# -*- coding: utf-8 -*-
# stress test: ic_call_protocol_function_to_callable
# category: inline_caches
# opt_state: (runs across all 6 states)
#
# Target: Call site caches a Python function (PyFunction_Type with vectorcall). Then a callable object is passed, which uses tp_call instead. The IC must transition.
#
# Tags: ['IC', 'callable', 'vectorcall']
def fn(x):
    return x + 1

class Caller:
    def __call__(self, x):
        return x + 100

def invoke(f, x):
    return f(x)

for _ in range(1000):
    assert invoke(fn, 0) == 1

c = Caller()
assert invoke(c, 0) == 100
assert invoke(c, 41) == 141

# Back to function
assert invoke(fn, 41) == 42

