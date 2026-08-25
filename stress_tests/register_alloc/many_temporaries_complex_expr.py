# -*- coding: utf-8 -*-
# stress test: many_temporaries_complex_expr
# category: register_alloc
#
# Target: A single expression introduces many simultaneously-live temporaries. The allocator must hold all of them at once (or spill and reload) to evaluate the expression. A buggy allocator that undercounted temporaries would reuse a register too early and corrupt the result.
#
# Tags: ['expression', 'pressure', 'register-alloc', 'temporaries']
def work(a, b, c, d, e, f, g, h):
    # Many intermediate temporaries; all are live until the final sum.
    t1 = a + b
    t2 = c + d
    t3 = e + f
    t4 = g + h
    t5 = t1 * t2
    t6 = t3 * t4
    t7 = t5 - t6
    t8 = a * c
    t9 = b * d
    t10 = e * g
    t11 = f * h
    t12 = t8 + t9
    t13 = t10 + t11
    t14 = t12 - t13
    return t7 + t14

# Sanity-check with positive inputs.
a, b, c, d, e, f, g, h = 1, 2, 3, 4, 5, 6, 7, 8
expected = (((a + b) * (c + d) - (e + f) * (g + h)) +
            ((a * c + b * d) - (e * g + f * h)))
assert work(1, 2, 3, 4, 5, 6, 7, 8) == expected

# And with negatives to catch sign-handling bugs.
A, B, C, D, E, F, G, H = -1, -2, -3, -4, -5, -6, -7, -8
expected_neg = (((A + B) * (C + D) - (E + F) * (G + H)) +
                ((A * C + B * D) - (E * G + F * H)))
assert work(-1, -2, -3, -4, -5, -6, -7, -8) == expected_neg

# And zeros.
assert work(0, 0, 0, 0, 0, 0, 0, 0) == 0

