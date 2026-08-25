# -*- coding: utf-8 -*-
# stress test: osr_entry_mid_loop_with_locals
# category: osr
#
# Target: OSR entry happens after the loop has been running for a while. The compiled frame must reconstruct all live locals (`acc`, `i`, `tmp`, `flag`).
#
# Tags: ['OSR', 'entry', 'locals']
def work(n):
    acc = 0
    flag = False
    for i in range(n):
        tmp = i * 2
        acc += tmp
        if i == n // 2:
            flag = True
    return acc, flag, tmp

a, f, t = work(1000)
assert a == sum(i * 2 for i in range(1000))
assert f is True
assert t == 999 * 2

