# -*- coding: utf-8 -*-
# stress test: aliased_objects_same_lifetime
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: Two objects allocated in the same frame reference each other (circular aliasing). Both must be heap-allocated because each is reachable from the other. A buggy analysis that treated them as independent could incorrectly scalar-replace one and break the circular alias chain observed by the caller.
#
# Tags: ['aliasing', 'circular-reference', 'escape-analysis', 'identity']
class Node:
    __slots__ = ("value", "peer")
    def __init__(self, v):
        self.value = v
        self.peer = None

def make_pair():
    a = Node(1)
    b = Node(2)
    a.peer = b
    b.peer = a  # circular reference
    return a  # b is reachable via a.peer

n = make_pair()
assert n.value == 1
assert n.peer.value == 2
# Circular aliasing must be preserved.
assert n.peer.peer is n

# Mutation through the alias must be visible from the other side.
n.peer.value = 99
assert n.peer.value == 99
assert n.peer.peer.value == 1  # n.value unchanged
assert n.peer.peer.peer is n.peer  # navigate back to b

