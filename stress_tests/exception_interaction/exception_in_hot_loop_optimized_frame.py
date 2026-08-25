# -*- coding: utf-8 -*-
# stress test: exception_in_hot_loop_optimized_frame
# category: exception_interaction
#
# Target: A ValueError is raised on iteration 500 inside a hot, type-stable loop that the JIT would normally compile. The JIT must deopt at the raise site and propagate the exception to the enclosing try/except without losing the accumulated loop state.
#
# Tags: ['exception', 'hot-loop', 'propagation', 'raise']
def work():
    acc = 0
    try:
        for i in range(1000):
            if i == 500:
                raise ValueError("mid")
            acc += i
    except ValueError:
        acc -= 1
    return acc

r = work()
# Only iterations 0..499 ran (exception breaks out of the loop at i=500).
# Then acc -= 1 in the except handler.
expected = sum(range(500)) - 1
assert r == expected, (r, expected)

