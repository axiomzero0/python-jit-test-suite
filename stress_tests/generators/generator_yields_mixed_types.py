# -*- coding: utf-8 -*-
# stress test: generator_yields_mixed_types
# category: generators
# opt_state: (runs across all 6 states)
#
# Target: Type speculation on the yielded value assumes a stable type. This generator deliberately yields int, then float, then str, then list, then dict across consecutive yields. The JIT's yield-site type profile must invalidate and the consumer must receive each value with its correct type.
#
# Tags: ['generator', 'type-speculation', 'yield']
def gen():
    yield 1
    yield 2.5
    yield "three"
    yield [4]
    yield {"five": 5}

values = list(gen())
assert values[0] == 1 and isinstance(values[0], int)
assert values[1] == 2.5 and isinstance(values[1], float)
assert values[2] == "three" and isinstance(values[2], str)
assert values[3] == [4] and isinstance(values[3], list)
assert values[4] == {"five": 5} and isinstance(values[4], dict)

# Re-running must keep producing the same mixed sequence (no stale
# speculation cached across generator instances).
again = list(gen())
assert again == values

