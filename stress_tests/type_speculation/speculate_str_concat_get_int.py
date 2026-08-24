# -*- coding: utf-8 -*-
# stress test: speculate_str_concat_get_int
# category: type_speculation
# opt_state: (runs across all 6 states)
#
# Target: JIT speculates `a + b` is str+str (fast path via PyUnicode_Concat). Then int+int is passed. The deopt must call the correct nb_add slot.
#
# Tags: ['binop', 'megamorphic', 'type-speculation']
def add(a, b):
    return a + b

# Warm up str+str
for _ in range(1000):
    add("a", "b")

# Now int+int
assert add(1, 2) == 3
assert add(2**63, 1) == 2**63 + 1

# And float+float
assert add(1.5, 2.5) == 4.0

# And list+list
assert add([1], [2]) == [1, 2]

