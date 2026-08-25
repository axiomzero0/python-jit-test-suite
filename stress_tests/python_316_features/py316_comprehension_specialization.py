# -*- coding: utf-8 -*-
# stress test: py316_comprehension_specialization
# category: python_316_features
#
# Target: List/dict/set comprehensions are specialized in 3.16. Verify they produce correct results across types.
#
# Tags: ['PEP-659', 'comprehension', 'py3.16', 'specialization']
r = [i * 2 for i in range(100) if i % 3 == 0]
assert r == [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 132, 138, 144, 150, 156, 162, 168, 174, 180, 186, 192, 198]

d = {str(i): i * i for i in range(50)}
assert len(d) == 50
assert d["0"] == 0
assert d["49"] == 2401

s = {i % 7 for i in range(100)}
assert s == {0, 1, 2, 3, 4, 5, 6}

matrix = [[i * j for j in range(5)] for i in range(5)]
assert matrix[0] == [0, 0, 0, 0, 0]
assert matrix[4] == [0, 4, 8, 12, 16]
assert matrix[2][3] == 6

gen = (i ** 2 for i in range(10) if i % 2 == 0)
assert list(gen) == [0, 4, 16, 36, 64]

