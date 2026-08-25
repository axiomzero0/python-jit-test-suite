# -*- coding: utf-8 -*-
# stress test: multiple_assignment_eval_once
# category: codegen
#
# Target: `a = b = c = expr` evaluates `expr` exactly once and binds all three names to that single object. Mutations through any name affect all of them (they are aliases).
#
# Tags: ['assignment', 'codegen', 'eval-once']
calls = []

def get_value():
    calls.append('called')
    return [1, 2, 3]

a = b = c = get_value()
assert calls == ['called']  # Only one call
assert a is b is c  # All aliases of the same object
assert a == [1, 2, 3]

# Mutating one affects all (same object)
a.append(4)
assert b == [1, 2, 3, 4]
assert c == [1, 2, 3, 4]

# Independent evaluations produce distinct objects
calls.clear()
m = get_value()
n = get_value()
assert calls == ['called', 'called']  # Two calls
assert m is not n  # Different objects
m.append(99)
assert n == [1, 2, 3]  # n unaffected

# Chain with attribute and subscript targets
class Obj:
    pass
obj = Obj()
d = {'k': None}
obj.x = d['k'] = value = 42
assert obj.x == 42
assert d['k'] == 42
assert value == 42
# All refer to the same int (immutable, but same object due to one eval)
assert obj.x is d['k'] is value

# Longer chain
p = q = r = s = [1, 2]
assert p is q is r is s
p.append(3)
assert q == [1, 2, 3]
assert r == [1, 2, 3]
assert s == [1, 2, 3]

