# -*- coding: utf-8 -*-
# stress test: decorate_method_at_runtime
# category: metaprog_invalidation
#
# Target: An existing method is wrapped with a decorator at runtime. Subsequent calls must invoke the wrapper, which itself calls the original. The IC for `c.f()` must invalidate to pick up the new wrapper as the resolved method.
#
# Tags: ['IC', 'decorator', 'invalidation']
class C:
    def f(self):
        return 1

c = C()
assert c.f() == 1

# Capture original method
original = C.f

def deco(fn):
    def wrapper(self):
        return fn(self) + 100
    return wrapper

# Wrap at runtime
C.f = deco(C.f)
assert c.f() == 101

# Double-wrap: wrapper calls previous wrapper, adding another 100
C.f = deco(C.f)
assert c.f() == 201

# Remove wrapping, restore original
C.f = original
assert c.f() == 1

