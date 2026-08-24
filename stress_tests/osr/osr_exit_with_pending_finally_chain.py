# -*- coding: utf-8 -*-
# stress test: osr_exit_with_pending_finally_chain
# category: osr
# opt_state: (runs across all 6 states)
#
# Target: Three nested try/finally blocks. OSR exit happens in the innermost loop. All three finally blocks must execute in the correct order during unwind.
#
# Tags: ['OSR', 'exception', 'finally', 'unwind']
order = []

def work():
    try:
        try:
            try:
                for i in range(1000):
                    if i == 500:
                        raise RuntimeError("deopt trigger")
            finally:
                order.append("inner")
        finally:
            order.append("middle")
    finally:
        order.append("outer")

try:
    work()
except RuntimeError:
    pass

# All three finally blocks must execute in order, even though the
# exception propagates out of work(). The "outer" append runs in the
# finally, then the RuntimeError escapes.
assert order == ["inner", "middle", "outer"]

