# -*- coding: utf-8 -*-
# stress test: osr_exit_with_active_exception
# category: osr
#
# Target: Hot loop raises an exception on iteration 500. The OSR exit must propagate the exception correctly through any compiled frame, unwinding finally blocks as it goes.
#
# Tags: ['OSR', 'exception', 'exit', 'finally']
def work():
    try:
        for i in range(1000):
            if i == 500:
                raise ValueError("mid-loop")
        return "no-exception"
    except ValueError as e:
        return f"caught at i={i}: {e}"

r = work()
assert "caught at i=500" in r

