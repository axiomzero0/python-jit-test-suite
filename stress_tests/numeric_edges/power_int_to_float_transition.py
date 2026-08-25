# -*- coding: utf-8 -*-
# stress test: power_int_to_float_transition
# category: numeric_edges
#
# Target: The ** operator changes result type with the exponent: int**positive_int stays int, int**negative_int becomes float, and a negative base with a fractional exponent becomes complex. A JIT must dispatch on operand types.
#
# Tags: ['numeric', 'power', 'type-transition']
import math
# 2 ** 0 stays int.
assert 2 ** 0 == 1
assert type(2 ** 0) is int
# 2 ** positive int stays int (arbitrary precision).
assert type(2 ** 10) is int
assert 2 ** 10 == 1024
# 2 ** negative int -> float.
assert 2 ** -1 == 0.5
assert type(2 ** -1) is float
assert type(2 ** -2) is float
# 0 ** 0 == 1 by definition.
assert 0 ** 0 == 1
# Negative base with a fractional exponent -> complex.
result = (-1) ** 0.5
assert isinstance(result, complex)
assert abs(result.imag - 1.0) < 1e-12
# 10 ** 0.5 -> float.
assert type(10 ** 0.5) is float
assert abs((10 ** 0.5) ** 2 - 10.0) < 1e-12
# Three-arg pow (modular exponentiation) only accepts ints.
assert pow(2, 10, 1000) == 24
assert type(pow(2, 10, 1000)) is int
assert pow(2, -1, 5) == 3      # modular inverse of 2 mod 5 (2*3 == 6 == 1)

