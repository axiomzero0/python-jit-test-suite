# -*- coding: utf-8 -*-
# stress test: deopt_preserves_list_after_object
# category: deoptimization
#
# Target: Loop appends ints to a list. On iteration 500, a string is appended. The list's element type spec must be invalidated.
#
# Tags: ['deopt', 'element-type', 'list']
def work():
    acc = []
    for i in range(1000):
        if i == 500:
            acc.append("string")
        else:
            acc.append(i)
    return acc

r = work()
assert len(r) == 1000
assert r[0] == 0
assert r[499] == 499
assert r[500] == "string"
assert r[501] == 501
assert r[-1] == 999

