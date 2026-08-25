# -*- coding: utf-8 -*-
# test_id: mem-0000028
# category: memory_gc
# semantic: memory_gc
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: deoptimized
# tags: ['GC', 'dag', 'does_not_escape', 'escape-analysis', 'memory']
shared = [1, 2, 3]
g = {'a': shared, 'b': shared, 'c': shared}
assert g['a'] is g['b'] is g['c']

