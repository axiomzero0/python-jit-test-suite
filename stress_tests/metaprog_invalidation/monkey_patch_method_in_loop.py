# -*- coding: utf-8 -*-
# stress test: monkey_patch_method_in_loop
# category: metaprog_invalidation
#
# Target: A method call site runs monomorphic for several iterations so the JIT caches `C.f`. Mid-loop the class method is replaced with a new function. The IC must invalidate and subsequent calls must dispatch to the new method.
#
# Tags: ['IC', 'invalidation', 'monkey-patch']
class C:
    def f(self):
        return 1

c = C()
results = []
for i in range(10):
    results.append(c.f())
    if i == 4:
        C.f = lambda self: 99

# First 5 calls saw the original; last 5 saw the patch
assert results[:5] == [1, 1, 1, 1, 1]
assert results[5:] == [99, 99, 99, 99, 99]

# After the loop, the patch persists
assert c.f() == 99

# Restore original
C.f = lambda self: 1
assert c.f() == 1

