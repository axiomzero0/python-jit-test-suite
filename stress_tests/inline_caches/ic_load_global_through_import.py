# -*- coding: utf-8 -*-
# stress test: ic_load_global_through_import
# category: inline_caches
#
# Target: JIT caches `math.sqrt`. Then `math` is re-imported (creating a new module object). The IC must invalidate.
#
# Tags: ['IC', 'global', 'import', 'reload']
import math

def call_sqrt(x):
    return math.sqrt(x)

for _ in range(1000):
    call_sqrt(4.0)

# Re-import math (creates new module reference, but builtins handle this)
import sys
old_math = sys.modules.get('math')
import importlib
importlib.reload(math)

assert call_sqrt(4.0) == 2.0
assert call_sqrt(16.0) == 4.0

