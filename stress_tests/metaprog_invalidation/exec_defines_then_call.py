# -*- coding: utf-8 -*-
# stress test: exec_defines_then_call
# category: metaprog_invalidation
#
# Target: exec() is used to define functions and classes in a fresh namespace. The defined objects are then retrieved and invoked. The JIT cannot have any precompiled cache for objects that did not exist when the surrounding code was compiled.
#
# Tags: ['dynamic-def', 'exec', 'invalidation']
ns = {}
code = """
def greet(name):
    return f'hello, {name}!'

class Counter:
    def __init__(self):
        self.n = 0
    def inc(self):
        self.n += 1
        return self.n
"""
exec(code, ns)

greet = ns['greet']
Counter = ns['Counter']

assert greet('world') == 'hello, world!'

c = Counter()
assert c.inc() == 1
assert c.inc() == 2
assert c.inc() == 3

# Add more to the namespace and call immediately
exec('VALUE = 42', ns)
assert ns['VALUE'] == 42

exec('def double(x): return x * 2', ns)
assert ns['double'](21) == 42

# Define a class that inherits from the previously-defined Counter
exec('class LoudCounter(Counter):\n    def inc(self):\n        return super().inc() * 10', ns)
lc = ns['LoudCounter']()
assert lc.inc() == 10
assert lc.inc() == 20
assert lc.inc() == 30

