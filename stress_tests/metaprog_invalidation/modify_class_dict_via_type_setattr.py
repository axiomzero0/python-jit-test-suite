# -*- coding: utf-8 -*-
# stress test: modify_class_dict_via_type_setattr
# category: metaprog_invalidation
#
# Target: Class state is mutated via type.__setattr__, which is the C-level path used by `C.x = ...`. Inline caches that cached the absence of an attribute must invalidate so the next lookup finds the new attribute.
#
# Tags: ['IC', 'invalidation', 'type-setattr']
class C:
    pass

c = C()
# Initial: no class attribute, no instance attribute
try:
    _ = c.x
    assert False, "expected AttributeError"
except AttributeError:
    pass

# Direct type-level mutation
type.__setattr__(C, 'x', 42)
assert c.x == 42

# Mutate again
type.__setattr__(C, 'x', 99)
assert c.x == 99

# Add a method via type.__setattr__
type.__setattr__(C, 'greet', lambda self: 'hi')
assert c.greet() == 'hi'

# Delete via type.__delattr__
type.__delattr__(C, 'x')
try:
    _ = c.x
    assert False, "expected AttributeError after deletion"
except AttributeError:
    pass

