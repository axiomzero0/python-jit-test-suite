# -*- coding: utf-8 -*-
# stress test: escape_conditionally_in_branch
# category: escape_analysis
#
# Target: An object escapes only on one branch of an if/else. A correct escape analysis must conservatively assume the object escapes on every path where escape is possible. A buggy analysis that only considered the non-escaping branch would corrupt the escaping branch.
#
# Tags: ['conditional-escape', 'escape-analysis', 'identity']
class Config:
    __slots__ = ("mode",)
    def __init__(self, m):
        self.mode = m

escaped = []

def work(escape):
    c = Config("normal")
    if escape:
        escaped.append(c)  # c escapes only on this branch
    return c.mode

# Non-escaping path.
assert work(False) == "normal"
assert len(escaped) == 0

# Escaping path.
assert work(True) == "normal"
assert len(escaped) == 1
assert escaped[0].mode == "normal"

# Each escaping call must allocate a distinct object.
prev = escaped[0]
work(True)
assert len(escaped) == 2
assert escaped[0] is prev
assert escaped[1] is not prev

