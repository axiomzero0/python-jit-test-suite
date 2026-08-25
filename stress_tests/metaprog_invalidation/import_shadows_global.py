# -*- coding: utf-8 -*-
# stress test: import_shadows_global
# category: metaprog_invalidation
#
# Target: A name is bound in the module namespace as a local value. A subsequent `from X import name` rebinds that name to a different value. LOAD_NAME / LOAD_GLOBAL must observe the new binding.
#
# Tags: ['IC', 'import', 'invalidation', 'shadow']
# Bind a local "pi"
pi = 3
assert pi == 3

# Import a name that shadows the local
from math import pi as pi

# `pi` is now bound to math.pi, not the integer 3
assert pi != 3
assert abs(pi - 3.14159265358979) < 1e-9

# Rebind via a different import path
import math
assert math.pi is pi

# Local reassignment overrides the import
pi = 3
assert pi == 3

# And the math module's value is unchanged
assert math.pi > 3.14

