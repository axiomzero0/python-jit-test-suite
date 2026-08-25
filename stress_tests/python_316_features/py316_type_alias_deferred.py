# -*- coding: utf-8 -*-
# stress test: py316_type_alias_deferred
# category: python_316_features
#
# Target: PEP 695 / 749: Type aliases (the `type` statement) are lazily evaluated. The JIT must not eagerly resolve them.
#
# Tags: ['PEP-695', 'PEP-749', 'py3.16', 'type-alias']
import sys

if sys.version_info >= (3, 12):
    # PEP 695: type statement creates a TypeAliasType (lazy)
    type Vector = list[int]

    # The alias can be used in annotations
    def f(x: Vector) -> Vector:
        return x + [1]

    assert f([1, 2, 3]) == [1, 2, 3, 1]

    # The alias is a TypeAliasType object, not the resolved type
    assert hasattr(Vector, "__value__") or hasattr(Vector, "__name__")
else:
    # Older Python: use TypeAlias via typing
    from typing import TypeAlias
    Vector: TypeAlias = list
    def f(x: Vector) -> Vector:
        return x + [1]
    assert f([1, 2, 3]) == [1, 2, 3, 1]

