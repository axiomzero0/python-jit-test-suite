# -*- coding: utf-8 -*-
# test_id: mem-0000021
# category: memory_gc
# semantic: memory_gc
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: very_hot
# tags: ['GC', 'escape-analysis', 'escapes_return', 'memory', 'tree']
def make_tree(depth):
    if depth == 0:
        return None
    return [make_tree(depth - 1), make_tree(depth - 1)]
G = make_tree(6)
assert G is not None

