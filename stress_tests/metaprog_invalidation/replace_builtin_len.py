# -*- coding: utf-8 -*-
# stress test: replace_builtin_len
# category: metaprog_invalidation
# opt_state: (runs across all 6 states)
#
# Target: The `len` builtin is replaced in the builtins module. LOAD_GLOBAL for `len` must re-resolve through builtins and pick up the new value. A JIT that cached `len = builtins.len` would dispatch to the original.
#
# Tags: ['IC', 'builtins', 'global', 'invalidation']
import builtins

orig_len = builtins.len
results = []
try:
    # Sanity: original works
    assert len([1, 2, 3]) == 3

    # Replace with a stub
    builtins.len = lambda x: -1
    results.append(len([1, 2, 3]))

    # Replace with another stub
    builtins.len = lambda x: 999
    results.append(len("hello"))

    # Restore mid-program; subsequent calls use original
    builtins.len = orig_len
    results.append(len([1, 2, 3]))
finally:
    # Always restore to avoid breaking the rest of the suite
    builtins.len = orig_len

assert results == [-1, 999, 3]
assert len([1, 2, 3]) == 3
assert len("hello") == 5

