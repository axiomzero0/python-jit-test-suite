# -*- coding: utf-8 -*-
# stress test: generator_closure_var_changes_between_yields
# category: generators
# opt_state: (runs across all 6 states)
#
# Target: The generator reads a closure-cell variable on each resume. Between yields the cell is mutated via a setter. A JIT that hoists the cell read out of the loop (caching the value at compile time) will serve stale values after the mutation.
#
# Tags: ['cell', 'closure', 'generator', 'nonlocal']
def make_gen():
    state = 0

    def gen():
        nonlocal state
        while True:
            # Must re-read `state` from the cell on EVERY resume.
            yield state

    def set_state(v):
        nonlocal state
        state = v

    return gen, set_state

gen, set_state = make_gen()
g = gen()

assert next(g) == 0
set_state(42)
assert next(g) == 42          # closure cell was mutated between yields
set_state("changed-type")
assert next(g) == "changed-type"
set_state([1, 2, 3])
assert next(g) == [1, 2, 3]

# A fresh generator sees the latest cell value, not a cached one.
g2 = gen()
assert next(g2) == [1, 2, 3]
g.close()
g2.close()

