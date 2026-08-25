# -*- coding: utf-8 -*-
# stress test: aliasing_discovered_mid_hot_loop
# category: aliasing
#
# Target: A hot loop runs for many iterations with `xs` and `ys` being distinct objects (so the JIT may speculate they never alias and hoist `len(xs)` out of the loop). On a later iteration, the loop body aliases them (`ys = xs`) and then mutates `xs`; the JIT's hoisted length would now be stale.
#
# Tags: ['LICM', 'aliasing', 'container', 'hoisting', 'list', 'loop-invariant', 'stress']
def hot_loop(xs, ys, trigger):
    # `xs` and `ys` start out as distinct, equal-length lists. The JIT
    # may speculate that len(xs) and len(ys) are loop-invariant and
    # hoist them out of the loop. We break that invariant on `trigger`.
    seen_pairs = []
    for i in range(20):
        # These two reads must NOT be hoisted: the alias below changes
        # what len(ys) reports on the very next iteration.
        n_xs = len(xs)
        n_ys = len(ys)
        seen_pairs.append((n_xs, n_ys))
        if i == trigger:
            ys = xs              # ys now aliases xs
            xs.append("marker") # mutates the shared object
            # n_ys for THIS iteration was captured before the alias;
            # but the next iteration must see the growth.
            continue
        if i > trigger + 1:
            break
    return seen_pairs

xs0 = list(range(5))
ys0 = list(range(5))
pairs = hot_loop(xs0, ys0, trigger=3)

# Before the alias: both lengths are 5.
assert pairs[:4] == [(5, 5)] * 4
# On the trigger iteration we capture 5,5 THEN alias+append, so the
# recorded pair for iter 3 is still (5, 5) (length read happened first).
assert pairs[3] == (5, 5)
# After the alias: ys aliases xs, which now has 6 elements.
assert pairs[4] == (6, 6), pairs[4]
assert pairs[5] == (6, 6), pairs[5]
# The marker landed in xs0 (and thus in the now-aliased ys).
assert "marker" in xs0
assert len(xs0) == 6

