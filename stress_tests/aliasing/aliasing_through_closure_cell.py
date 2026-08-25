# -*- coding: utf-8 -*-
# stress test: aliasing_through_closure_cell
# category: aliasing
#
# Target: A closure captures a list by reference. Mutating the list from inside the closure must be visible to the enclosing scope and vice versa. A JIT that box-to-scalar optimizes the closure variable without recognizing the alias would miss updates in either direction.
#
# Tags: ['aliasing', 'closure', 'container', 'escape-analysis', 'list', 'stress']
def make_appender():
    buf = []
    def append(x):
        buf.append(x)
        return len(buf)
    def snapshot():
        return list(buf)
    return append, snapshot, buf

append, snapshot, captured_buf = make_appender()
assert append(1) == 1
assert append(2) == 2
assert snapshot() == [1, 2]
# The closure-captured buf IS the one returned to the caller.
assert captured_buf == [1, 2]
assert captured_buf is not snapshot()  # snapshot returns a copy
# Mutating through the caller's alias is visible to the closure.
captured_buf.append(99)
assert snapshot() == [1, 2, 99]
assert append(3) == 4
assert captured_buf == [1, 2, 99, 3]

