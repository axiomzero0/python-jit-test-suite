# -*- coding: utf-8 -*-
# stress test: overlapping_lifetimes_nested_loops
# category: register_alloc
#
# Target: Two variables with overlapping lifetimes live across an outer and an inner loop. The inner variable dies at the end of each inner iteration but the outer variable lives across the entire inner loop. A buggy allocator that didn't model nested scopes correctly would either free the outer variable too early or hold the inner variable for too long, wasting registers.
#
# Tags: ['nested-loop', 'overlapping-lifetimes', 'register-alloc', 'scope']
def work(n, m):
    outer_sum = 0
    for i in range(n):
        # inner_acc's lifetime spans the entire inner loop, but
        # dies before the next outer iteration.
        inner_acc = 0
        for j in range(m):
            # outer_sum, inner_acc, i, j all live here.
            inner_acc += i * j
        outer_sum += inner_acc
    return outer_sum

assert work(5, 5) == sum(i * j for i in range(5) for j in range(5))
assert work(3, 4) == sum(i * j for i in range(3) for j in range(4))
assert work(0, 5) == 0   # outer loop never runs
assert work(5, 0) == 0   # inner loop never runs
assert work(10, 10) == sum(i * j for i in range(10) for j in range(10))

