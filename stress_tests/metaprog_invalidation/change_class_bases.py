# -*- coding: utf-8 -*-
# stress test: change_class_bases
# category: metaprog_invalidation
#
# Target: Assigning to C.__bases__ swaps the base class. The MRO must be recomputed and method dispatch must reflect the new base. A JIT that cached the old MRO would dispatch to the wrong method.
#
# Tags: ['IC', 'MRO', 'bases', 'invalidation']
class A:
    def f(self):
        return 'A'

class B:
    def f(self):
        return 'B'

class C(A):
    pass

c = C()
assert c.f() == 'A'
assert C.__mro__ == (C, A, object)

# Swap base
C.__bases__ = (B,)
assert c.f() == 'B'
assert C.__mro__ == (C, B, object)

# Swap back
C.__bases__ = (A,)
assert c.f() == 'A'
assert C.__mro__ == (C, A, object)

