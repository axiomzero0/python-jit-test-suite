# -*- coding: utf-8 -*-
# stress test: dynamic_class_via_type_call
# category: metaprog_invalidation
#
# Target: A new class is created by calling type(name, bases, dict) and used immediately. The JIT cannot have any precompiled cache for this brand-new class; lookups must resolve via the freshly built MRO.
#
# Tags: ['dynamic-class', 'invalidation', 'type-call']
class Base:
    def hello(self):
        return 'base'

def make_class(name, methods):
    return type(name, (Base,), methods)

C = make_class('C', {'hello': lambda self: 'derived'})
c = C()
assert c.hello() == 'derived'
assert isinstance(c, Base)

# Build many distinct classes in a loop
classes = []
for i in range(10):
    methods = {'hello': lambda self, n=i: f'class-{n}'}
    classes.append(make_class(f'C{i}', methods))

for i, cls in enumerate(classes):
    inst = cls()
    assert inst.hello() == f'class-{i}'
    assert isinstance(inst, Base)

# Each class is distinct
assert len({id(c) for c in classes}) == 10

