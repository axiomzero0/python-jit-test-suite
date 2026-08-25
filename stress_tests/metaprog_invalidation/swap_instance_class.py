# -*- coding: utf-8 -*-
# stress test: swap_instance_class
# category: metaprog_invalidation
#
# Target: An instance's __class__ is reassigned at runtime, swapping its method dispatch table. CPython forbids reassigning a class's metaclass after creation, so this is the closest executable analogue: changing which class an instance believes it belongs to, which flips all attribute lookups.
#
# Tags: ['instance-class', 'invalidation', 'swap']
class Base:
    pass

class A(Base):
    kind = 'A'
    def f(self):
        return 1

class B(Base):
    kind = 'B'
    def f(self):
        return 2

obj = A()
results = []
results.append(obj.f())
results.append(obj.kind)

# Swap to B
obj.__class__ = B
results.append(obj.f())
results.append(obj.kind)

# Swap back to A
obj.__class__ = A
results.append(obj.f())
results.append(obj.kind)

assert results == [1, 'A', 2, 'B', 1, 'A']
assert isinstance(obj, A)
assert not isinstance(obj, B)

