# -*- coding: utf-8 -*-
# stress test: cyclic_aliasing_self_reference
# category: aliasing
# opt_state: (runs across all 6 states)
#
# Target: Construct two containers that reference each other (a cycle). The JIT must not assume acyclic reference graphs and must not loop forever when traversing. Equality and repr must terminate.
#
# Tags: ['aliasing', 'container', 'cycle', 'list', 'stress']
a = []
b = [a]
a.append(b)
# a == [[...]] and b == [[[...]]] -- cyclic
assert a[0] is b
assert b[0] is a
assert a[0][0] is a
# Append through one alias, observe through the other
a.append("tag")
assert b[0][1] == "tag"
assert len(b[0]) == 2
# repr is well-defined (recursive)
s = repr(a)
assert "..." in s

