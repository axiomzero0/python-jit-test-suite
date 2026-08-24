# -*- coding: utf-8 -*-
# stress test: closure_captures_class
# category: closure_lifetime
# opt_state: (runs across all 6 states)
#
# Target: A class is defined inside the enclosing function and captured by an inner closure. The class object must persist after the enclosing frame returns, and each call to the factory must produce instances of the captured class (not a fresh class).
#
# Tags: ['class-capture', 'closure', 'metaprogramming']
def make_counter_factory():
    class Counter:
        _instances = 0
        def __init__(self):
            Counter._instances += 1
            self.count = 0
        def inc(self):
            self.count += 1
            return self.count
    def factory():
        return Counter()
    return factory

mk = make_counter_factory()

c1 = mk()
assert c1.inc() == 1
assert c1.inc() == 2

c2 = mk()
assert c2.inc() == 1
assert c1.inc() == 3  # c1 unaffected

# All instances share the same captured class
assert type(c1) is type(c2)

# Class state persists across the closure
assert type(c1)._instances == 2

c3 = mk()
assert type(c3) is type(c1)
assert type(c1)._instances == 3

