# -*- coding: utf-8 -*-
# stress test: bool_is_int_subclass
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: bool is a subclass of int (True == 1, False == 0) but is a distinct singleton type. Arithmetic promotes bool to int, bitwise ops keep bool, and bools work as list indices. A JIT that treats bool and int as identical would miss the type transitions.
#
# Tags: ['bool', 'numeric', 'promotion', 'subclass']
# bool is a subclass of int: True == 1, False == 0.
assert isinstance(True, int)
assert isinstance(False, int)
assert issubclass(bool, int)
assert True == 1
assert False == 0
# Arithmetic promotes bool to int.
assert True + True == 2
assert type(True + True) is int
assert True * 3 == 3
assert False * 99 == 0
assert 1 + True == 2
assert 10 - False == 10
# bool values are singletons (identity).
assert True is True
assert False is False
# But the int 1 is NOT the singleton True (different objects).
one = 1
zero = 0
assert one is not True
assert zero is not False
# Bools behave as indices.
assert [10, 20, 30][True] == 20
assert [10, 20, 30][False] == 10
# sum() over bools counts the Trues.
assert sum([True, False, True, True]) == 3
assert sum([True, True]) == 2
# Bitwise ops on bools return bools (bool defines its own __and__/__or__).
assert (True & False) is False
assert (True | False) is True
assert (True & True) is True
# Negation promotes to int.
assert -True == -1
assert type(-True) is int

