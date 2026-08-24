# -*- coding: utf-8 -*-
# stress test: guard_multiple_failures_in_sequence
# category: guard_failures
# opt_state: (runs across all 6 states)
#
# Target: Multiple guards fail in sequence. Each failure should trigger deopt, and the interpreter should handle the next failure correctly.
#
# Tags: ['guard', 'multiple', 'sequence']
def work(values):
    results = []
    for v in values:
        try:
            r1 = v + 1
        except TypeError:
            r1 = "type-error"
        try:
            r2 = v[0]
        except TypeError:
            r2 = "type-error"
        results.append((r1, r2))
    return results

r = work([1, "hello", [10, 20], 3.14])
# v=1: 1+1=2, 1[0] -> TypeError
assert r[0] == (2, "type-error")
# v="hello": "hello"+1 -> TypeError, "hello"[0]="h"
assert r[1] == ("type-error", "h")
# v=[10,20]: [10,20]+1 -> TypeError, [10,20][0]=10
assert r[2] == ("type-error", 10)
# v=3.14: 3.14+1=4.14, 3.14[0] -> TypeError
assert abs(r[3][0] - 4.14) < 1e-9
assert r[3][1] == "type-error"

