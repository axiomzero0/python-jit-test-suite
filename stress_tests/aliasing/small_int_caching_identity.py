# -*- coding: utf-8 -*-
# stress test: small_int_caching_identity
# category: aliasing
# opt_state: (runs across all 6 states)
#
# Target: CPython pre-caches small ints in the range [-5, 256] so that any computation producing such a value yields the *same* object. A JIT that boxes ints on every arithmetic operation would break `is` checks against cached small ints. Values outside the cached range may be fresh objects.
#
# Tags: ['aliasing', 'cache', 'identity', 'int', 'stress']
# Inside the cached range: identity holds. We avoid `is <int_literal>`
# directly (which Python warns about) by routing through int() so the
# comparison is between two *computed* values that the JIT cannot fold.
cached_range = list(range(-5, 257))
for n in cached_range:
    a = int(n)
    b = int(n)
    assert a is b, f"identity failed for cached int {n}"

# Just past the cached range, identity is NOT guaranteed.
above = 257
x = int(above)
y = int(above)
assert x == y == 257
# Either identity is fine, but the language does not require it.
assert (x is y) in (True, False)

# Arithmetic results in the cached range still hit the cache.
for n in (0, 1, 100, 200, 256):
    computed = (n - 1) + 1
    assert computed is int(n)

# Identity-equality fast path: two equal interned-ish strings compare
# equal via `is`, but only because they share the cache.
s1 = "abc"
s2 = "abc"
assert s1 is s2   # CPython interns these literals at compile time.

