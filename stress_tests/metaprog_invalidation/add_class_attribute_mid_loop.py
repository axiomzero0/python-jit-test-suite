# -*- coding: utf-8 -*-
# stress test: add_class_attribute_mid_loop
# category: metaprog_invalidation
#
# Target: A class starts with no attribute `x`. Attribute lookups must raise AttributeError. Mid-loop, `x` is added to the class. Existing instances must immediately see the new attribute via class fallback.
#
# Tags: ['IC', 'attribute', 'invalidation']
class C:
    pass

c = C()

# Before: attribute lookup fails
try:
    _ = c.x
    assert False, "expected AttributeError"
except AttributeError:
    pass

results = []
for i in range(10):
    if i == 5:
        C.x = 42
    if hasattr(c, 'x'):
        results.append(c.x)
    else:
        results.append(None)

assert results == [None, None, None, None, None, 42, 42, 42, 42, 42]

# Override the class attribute on the instance
c.x = 7
assert c.x == 7

# Remove the class attribute; instance attr still wins
del C.x
assert c.x == 7

# A fresh instance now has no x
c2 = C()
try:
    _ = c2.x
    assert False
except AttributeError:
    pass

