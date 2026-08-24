# -*- coding: utf-8 -*-
# stress test: add_data_descriptor_to_class
# category: metaprog_invalidation
# opt_state: (runs across all 6 states)
#
# Target: A class starts with a plain instance attribute. A data descriptor is then added to the class with the same name. Data descriptors take precedence over instance __dict__, so subsequent attribute access must invoke the descriptor's __get__ rather than reading the instance dict.
#
# Tags: ['IC', 'descriptor', 'invalidation', 'precedence']
class C:
    pass

c = C()
c.x = 1  # plain instance attribute
assert c.x == 1

# Add a data descriptor to the class
class Desc:
    def __get__(self, obj, owner):
        if obj is None:
            return self
        return 999
    def __set__(self, obj, val):
        # Silently store elsewhere; not in obj.__dict__
        obj.__dict__['x_shadow'] = val

C.x = Desc()

# Data descriptor shadows the instance attribute
assert c.x == 999
# The instance __dict__ still has the old value, but it's hidden
assert c.__dict__.get('x') == 1

# Assignment invokes the descriptor's __set__, not __dict__ update
c.x = 42
assert c.__dict__.get('x_shadow') == 42
assert c.x == 999  # still hits the descriptor

# Remove the descriptor; instance attr reappears
del C.x
assert c.x == 1

