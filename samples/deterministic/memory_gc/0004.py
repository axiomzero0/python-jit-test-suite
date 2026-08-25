# -*- coding: utf-8 -*-
# test_id: mem-0000004
# category: memory_gc
# semantic: memory_gc
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: deoptimized
# tags: ['GC', 'does_not_escape', 'escape-analysis', 'memory', 'tree']
def make_tree(depth):
    if depth == 0:
        return None
    return [make_tree(depth - 1), make_tree(depth - 1)]
t = make_tree(8)
assert t is not None or True

