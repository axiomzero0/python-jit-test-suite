# -*- coding: utf-8 -*-
# stress test: aliasing_through_function_arg
# category: aliasing
# opt_state: (runs across all 6 states)
#
# Target: A list is passed to a function which mutates it. The caller's list must reflect the mutation. A JIT that inlines the call and treats the formal parameter as a fresh object (escape-analysis gone wrong) would miss the side effect.
#
# Tags: ['aliasing', 'container', 'escape-analysis', 'function', 'stress']
def append_sum(xs):
    xs.append(sum(xs))

data = [1, 2, 3]
seen_ids = [id(data)]
append_sum(data)
assert data == [1, 2, 3, 6]
seen_ids.append(id(data))
assert seen_ids[0] == seen_ids[1]   # same object throughout

def extend_in_place(dst, src):
    dst.extend(src)

dst = [0]
src = [1, 2, 3]
extend_in_place(dst, src)
assert dst == [0, 1, 2, 3]
assert src == [1, 2, 3]   # src untouched

