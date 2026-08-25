# -*- coding: utf-8 -*-
# stress test: long_lived_used_at_start_and_end
# category: register_alloc
#
# Target: A variable is defined at the start of the function, not used for a long stretch in the middle, then used again at the very end. Its live range spans the entire function. A naive allocator would pin it to a register for the whole function, wasting the register; a good allocator would split the range and spill it during the middle. Either way, the value must survive.
#
# Tags: ['live-range', 'long-lived', 'register-alloc', 'spill']
def work():
    x = 42  # used at the start (definition) and the end (use)
    # Lots of unrelated computation in between that does not touch x.
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    mid = a + b + c + d + e + f + g + h
    p = mid * 2
    q = p + 1
    r = q * 3
    s = r - 7
    # x is finally used again here; its value must still be 42.
    return x + s

# Compute the expected value by hand to avoid relying on the JIT.
mid = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8        # = 36
p = mid * 2                                # = 72
q = p + 1                                  # = 73
r = q * 3                                  # = 219
s = r - 7                                  # = 212
expected = 42 + s                          # = 254
assert work() == expected
assert work() == 254

