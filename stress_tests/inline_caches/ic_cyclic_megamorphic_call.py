# -*- coding: utf-8 -*-
# stress test: ic_cyclic_megamorphic_call
# category: inline_caches
# opt_state: (runs across all 6 states)
#
# Target: Cycle through 8 different types at a single call site. This stress-tests the megamorphic IC's hash-table lookup path and ensures no entry is dropped.
#
# Tags: ['IC', 'hash-table', 'megamorphic']
classes = [type(f"T{i}", (), {"f": lambda self, i=i: i}) for i in range(8)]

def call(o):
    return o.f()

objs = [c() for c in classes]
expected = [i for i in range(8)] * 200
actual = [call(o) for _ in range(200) for o in objs]

assert actual == expected

