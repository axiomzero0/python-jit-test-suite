# -*- coding: utf-8 -*-
# stress test: escape_via_generator_yield
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: An object is yielded from a generator. The generator frame is suspended across yields, holding references to all locals including the just-yielded object. The JIT must heap-allocate yielded objects because the consumer can observe their identity after resumption.
#
# Tags: ['escape-analysis', 'escape-via-generator', 'generator', 'identity']
class Snapshot:
    __slots__ = ("value",)
    def __init__(self, v):
        self.value = v

def gen_snapshots(n):
    for i in range(n):
        s = Snapshot(i)
        yield s  # escapes via yield

result = list(gen_snapshots(3))
assert len(result) == 3
assert result[0].value == 0
assert result[1].value == 1
assert result[2].value == 2

# Distinct identities (heap-allocated per yield).
assert result[0] is not result[1]
assert result[1] is not result[2]

# Mutations are local.
result[0].value = 999
assert result[1].value == 1

