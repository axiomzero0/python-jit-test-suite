# -*- coding: utf-8 -*-
# test_id: mem-0000049
# category: memory_gc
# semantic: memory_gc
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['GC', 'cycle', 'does_not_escape', 'escape-analysis', 'memory']
a = []
b = [a]
a.append(b)
assert a[0] is b and b[0] is a

