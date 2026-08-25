# -*- coding: utf-8 -*-
# stress test: escape_via_list_append
# category: escape_analysis
#
# Target: An object is appended to a list that outlives the frame. The list holds a strong reference, so the object must be heap-allocated. A buggy analysis that only considered direct returns would incorrectly eliminate the allocation and the list would hold garbage.
#
# Tags: ['container', 'escape-analysis', 'escape-via-list', 'identity']
class Item:
    __slots__ = ("idx", "tag")
    def __init__(self, idx, tag):
        self.idx = idx
        self.tag = tag

def build_items(n):
    items = []
    for i in range(n):
        it = Item(i, "tag-{}".format(i))
        items.append(it)  # escapes via list
    return items

result = build_items(5)
assert len(result) == 5
assert result[0].idx == 0
assert result[0].tag == "tag-0"
assert result[4].idx == 4
assert result[4].tag == "tag-4"

# Distinct identities.
assert result[0] is not result[1]

# Mutation must be local to each element.
result[0].idx = 999
assert result[1].idx == 1

