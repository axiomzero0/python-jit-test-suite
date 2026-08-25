# -*- coding: utf-8 -*-
# stress test: escape_in_recursive_function
# category: escape_analysis
#
# Target: A recursive function allocates a fresh object per frame and links it to the result of the recursive call. Each frame's object must be heap-allocated because it is returned to the parent frame and observed as a distinct identity. A buggy analysis that folded frames together would corrupt the chain.
#
# Tags: ['escape-analysis', 'identity', 'lifetime', 'recursion']
class Frame:
    __slots__ = ("depth", "parent")
    def __init__(self, depth, parent=None):
        self.depth = depth
        self.parent = parent

def build_chain(n):
    if n <= 0:
        return None
    parent = build_chain(n - 1)
    f = Frame(n, parent)  # fresh object per frame
    return f

chain = build_chain(5)
assert chain.depth == 5
assert chain.parent.depth == 4
assert chain.parent.parent.depth == 3
assert chain.parent.parent.parent.depth == 2
assert chain.parent.parent.parent.parent.depth == 1
assert chain.parent.parent.parent.parent.parent is None

# Count the chain length.
count = 0
node = chain
while node is not None:
    count += 1
    node = node.parent
assert count == 5

# Each Frame is a distinct heap object.
assert chain is not chain.parent
assert chain.parent is not chain.parent.parent

