# -*- coding: utf-8 -*-
# stress test: augmented_assignment_iadd_dispatch
# category: codegen
# opt_state: (runs across all 6 states)
#
# Target: `x += y` first tries `type(x).__iadd__`. If x is mutable and defines __iadd__, the operation is in-place and returns x itself. For immutable types (int, str, tuple), __iadd__ falls back to __add__, producing a new object. A custom type can define __iadd__ to do in-place mutation.
#
# Tags: ['augmented', 'codegen', 'dispatch', 'iadd']
# list += uses __iadd__ (in-place extend)
lst = [1, 2, 3]
original_id = id(lst)
lst += [4, 5]
assert id(lst) == original_id  # Same object (in-place)
assert lst == [1, 2, 3, 4, 5]

# list += non-list iterable (still __iadd__, accepts any iterable)
lst = [1, 2]
lst += (3, 4)
assert lst == [1, 2, 3, 4]
lst += "ab"
assert lst == [1, 2, 3, 4, 'a', 'b']

# int += uses __add__ (immutable, new object)
n = 10
n += 5
assert n == 15

# Custom class with __iadd__ that returns self
class Acc:
    def __init__(self, v):
        self.v = v
    def __iadd__(self, other):
        self.v += other * 10
        return self
    def __add__(self, other):
        return Acc(self.v + other)

a = Acc(5)
a_id = id(a)
a += 2  # calls __iadd__
assert id(a) == a_id  # same object, mutated in place
assert a.v == 25  # 5 + 2*10

# Plain + creates new object via __add__
b = a + 3
assert b is not a
assert b.v == 28
assert a.v == 25  # unchanged

# Without __iadd__, += falls back to __add__ and rebinds
class NoIadd:
    def __init__(self, v):
        self.v = v
    def __add__(self, other):
        return NoIadd(self.v + other)

x = NoIadd(1)
x_id = id(x)
x += 10  # __add__ called, x rebound to new object
assert id(x) != x_id
assert x.v == 11

