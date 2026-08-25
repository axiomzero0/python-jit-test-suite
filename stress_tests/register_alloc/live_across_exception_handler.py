# -*- coding: utf-8 -*-
# stress test: live_across_exception_handler
# category: register_alloc
#
# Target: Variables defined before a try block are used inside the corresponding except handler. The allocator must keep them live across the exception edge, which is hard to model because the edge is rarely taken. A buggy allocator that didn't account for exception edges would spill them at the try boundary and lose them when the exception fires.
#
# Tags: ['exception-edge', 'handler', 'register-alloc', 'spill']
def work(x):
    a = 10
    b = 20
    try:
        if x < 0:
            raise ValueError("negative")
        c = a + b + x
        return c
    except ValueError:
        # a and b must still be live here.
        return a + b

assert work(5) == 35      # 10 + 20 + 5
assert work(-1) == 30     # exception path: 10 + 20
assert work(0) == 30      # 10 + 20 + 0
assert work(100) == 130   # 10 + 20 + 100

