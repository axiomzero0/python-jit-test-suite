# -*- coding: utf-8 -*-
# stress test: speculate_function_call_then_callable_obj
# category: type_speculation
# opt_state: (runs across all 6 states)
#
# Target: JIT speculates `f()` is a direct function call. Then a callable object (with __call__) is passed. The deopt must use the tp_call slot instead of the inlined function pointer.
#
# Tags: ['callable', 'tp_call', 'type-speculation']
def real_fn():
    return 42

class Callable:
    def __call__(self):
        return 99

def invoke(f):
    return f()

# Warm up with real function
for _ in range(1000):
    invoke(real_fn)

# Now callable object
assert invoke(Callable()) == 99

