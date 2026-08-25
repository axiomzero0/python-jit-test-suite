# -*- coding: utf-8 -*-
# stress test: ic_builtin_replace
# category: inline_caches
#
# Target: JIT may inline `len()` as a direct call to PyObject_Length. Then `len` is rebound in the module namespace. The IC must fall back to LOAD_GLOBAL.
#
# Tags: ['IC', 'builtin', 'monkey-patch']
def call_len(x):
    return len(x)

for _ in range(1000):
    assert call_len([1,2,3]) == 3

# Rebind len locally (module-level)
import builtins
old_len = builtins.len

class FakeLen:
    def __call__(self, x):
        return 999

builtins.len = FakeLen()
try:
    assert call_len([1,2,3]) == 999
finally:
    builtins.len = old_len

assert call_len([1,2,3]) == 3

