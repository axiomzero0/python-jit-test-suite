# -*- coding: utf-8 -*-
# stress test: deopt_preserves_starred_assignment
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Starred unpacking `a, *b, c = ...`. Deopt must preserve the list `b`.
#
# Tags: ['deopt', 'starred', 'unpack']
def work():
    results = []
    for i in range(1000):
        seq = list(range(i, i + 10))
        a, *b, c = seq
        results.append((a, b, c))
        if i == 500:
            x = "trigger"
    return results

r = work()
assert r[0] == (0, [1, 2, 3, 4, 5, 6, 7, 8], 9)
assert r[500] == (500, [501, 502, 503, 504, 505, 506, 507, 508], 509)
assert r[-1] == (999, [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007], 1008)

