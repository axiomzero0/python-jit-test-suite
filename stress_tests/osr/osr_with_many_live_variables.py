# -*- coding: utf-8 -*-
# stress test: osr_with_many_live_variables
# category: osr
# opt_state: (runs across all 6 states)
#
# Target: OSR with 10+ live variables. Stress-tests the register spill/reload logic during state reconstruction.
#
# Tags: ['OSR', 'live-variables', 'registers']
def work(n):
    a = b = c = d = e = f = g = h = i = j = 0
    for x in range(n):
        a += x
        b += x * 2
        c += x * 3
        d += x * 4
        e += x * 5
        f += x * 6
        g += x * 7
        h += x * 8
        i += x * 9
        j += x * 10
    return (a, b, c, d, e, f, g, h, i, j)

result = work(1000)
expected = (sum(x * k for x in range(1000)) for k in range(1, 11))
assert result == tuple(expected)

