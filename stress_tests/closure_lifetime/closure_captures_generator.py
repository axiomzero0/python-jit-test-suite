# -*- coding: utf-8 -*-
# stress test: closure_captures_generator
# category: closure_lifetime
#
# Target: A closure captures a generator object. Each invocation of the closure advances the generator by one step. The cell must preserve the generator's suspended state across calls.
#
# Tags: ['closure', 'generator', 'suspended-state']
def make_gen_holder():
    gen = (i * 2 for i in range(5))
    def next_val():
        return next(gen)
    return next_val

nxt = make_gen_holder()
assert nxt() == 0
assert nxt() == 2
assert nxt() == 4
assert nxt() == 6
assert nxt() == 8

# Generator is exhausted; further calls must raise StopIteration
stop_count = 0
for _ in range(3):
    try:
        nxt()
    except StopIteration:
        stop_count += 1
assert stop_count == 3

# Each holder captures its own generator
nxt2 = make_gen_holder()
assert nxt2() == 0
assert nxt2() == 2

