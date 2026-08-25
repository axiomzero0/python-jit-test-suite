# -*- coding: utf-8 -*-
# stress test: recursive_generator_indirect
# category: generators
#
# Target: A generator that ``yield from``s itself recursively (tree flattening) builds a chain of suspended generator frames as deep as the recursion. Each frame must stay independently resumable and values must percolate up the chain in order. A deep single-leaf tree stresses the runtime's ability to manage a tall stack of dormant generator frames.
#
# Tags: ['generator', 'recursion', 'yield-from']
def walk_tree(node):
    """Recursively yield every leaf in a nested-list tree."""
    if isinstance(node, list):
        for child in node:
            yield from walk_tree(child)
    else:
        yield node

tree = [1, [2, [3, 4], 5], [6, [7, [8, 9]]], 10]
assert list(walk_tree(tree)) == list(range(1, 11))

# A balanced binary-ish tree of known depth.
def build(depth):
    if depth == 0:
        return depth
    return [build(depth - 1), build(depth - 1)]

leaves = list(walk_tree(build(8)))
assert leaves == [0] * (2 ** 8)
assert len(leaves) == 256

# Deeply nested single-leaf tree: 200 suspended generator frames stacked.
deep = 42
for _ in range(200):
    deep = [deep]
assert list(walk_tree(deep)) == [42]

