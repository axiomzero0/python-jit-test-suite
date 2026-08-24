# -*- coding: utf-8 -*-
# stress test: deopt_preserves_walrus_binding
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Walrus operator `:=` binds a variable in an enclosing scope. Deopt must preserve the binding.
#
# Tags: ['binding', 'deopt', 'walrus']
def work():
    results = []
    for i in range(1000):
        if (n := i * 2) > 500:
            results.append(n)
        if i == 500:
            x = "trigger"
    return results

r = work()
# n = i * 2; n > 500 means i > 250, so i in range(251, 1000)
assert len(r) == 749
assert r[0] == 502    # i=251 -> n=502
assert r[-1] == 1998  # i=999 -> n=1998

