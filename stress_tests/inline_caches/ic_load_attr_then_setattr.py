# -*- coding: utf-8 -*-
# stress test: ic_load_attr_then_setattr
# category: inline_caches
#
# Target: JIT caches `o.x` as an instance attribute at offset N. Then __setattr__ is overridden on the class. The IC must invalidate and route future `o.x = ...` through __setattr__.
#
# Tags: ['IC', 'descriptor', 'setattr']
class A:
    pass

a = A()
a.x = 1

def get_x(o):
    return o.x

def set_x(o, v):
    o.x = v

for _ in range(1000):
    set_x(a, 1)
    assert get_x(a) == 1

# Override __setattr__
calls = []
class B:
    def __setattr__(self, name, value):
        calls.append((name, value))
        super().__setattr__(name, value * 10)

b = B()
set_x(b, 5)
assert calls == [("x", 5)]
assert get_x(b) == 50

