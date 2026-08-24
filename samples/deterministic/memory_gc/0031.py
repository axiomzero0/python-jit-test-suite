# -*- coding: utf-8 -*-
# test_id: mem-0000031
# category: memory_gc
# semantic: memory_gc
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['GC', 'dag', 'escape-analysis', 'escapes_global', 'memory']
shared = [1, 2, 3]
g = {'a': shared, 'b': shared, 'c': shared}
assert g['a'] is g['b'] is g['c']

