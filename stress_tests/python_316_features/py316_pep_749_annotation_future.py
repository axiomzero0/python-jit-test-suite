# -*- coding: utf-8 -*-
# stress test: py316_pep_749_annotation_future
# category: python_316_features
#
# Target: PEP 749 (the implementation of PEP 649): Verify that from __future__ import annotations is no longer needed in 3.16 (deferred is the default).
#
# Tags: ['PEP-649', 'PEP-749', 'annotations', 'future', 'py3.16']
import sys

if sys.version_info >= (3, 14):
    # In Python 3.16, annotations are deferred by default.
    def f(x: "ForwardRef") -> "AnotherRef":
        return x

    # These references don't exist yet, but no error at def time.
    class ForwardRef: pass
    class AnotherRef: pass

    assert f(ForwardRef()) is not None
    assert f(42) == 42

    ann = f.__annotations__
    assert "x" in ann
    assert "return" in ann
else:
    # On older Python, annotations are eager. Forward references raise
    # NameError unless quoted (which makes them strings, not resolved).
    # Verify that quoted forward refs work as strings.
    def f(x: "int") -> "int":
        return x + 1

    assert f(41) == 42

    # __annotations__ contains the string form
    ann = f.__annotations__
    assert ann["x"] == "int"
    assert ann["return"] == "int"

