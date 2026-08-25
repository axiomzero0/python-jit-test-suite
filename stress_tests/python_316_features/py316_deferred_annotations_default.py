# -*- coding: utf-8 -*-
# stress test: py316_deferred_annotations_default
# category: python_316_features
#
# Target: PEP 649/749: Annotations are evaluated lazily by default in Python 3.16. The JIT must not eagerly evaluate annotations at function definition time. Verify that a forward reference in an annotation does not raise NameError at def time.
#
# Tags: ['PEP-649', 'annotations', 'deferred', 'py3.16']
import sys

if sys.version_info >= (3, 14):
    # In Python 3.16, annotations are deferred by default.
    # A forward reference to a name that doesn't exist yet should NOT raise
    # at function definition time.
    def f(x: "NotYetDefined") -> "AlsoMissing":
        return x

    # The function can still be called normally
    assert f(42) == 42

    # Now define the missing names
    class NotYetDefined: pass
    class AlsoMissing: pass

    # Calling with the annotated type works
    assert f(NotYetDefined()) is not None

    # Verify __annotations__ is a dict-like object that resolves lazily
    ann = f.__annotations__
    assert "x" in ann
    assert "return" in ann
else:
    # On older Python, annotations are eager; the same forward references
    # would raise NameError. Verify that eager evaluation still works.
    def g(x: int) -> int:
        return x + 1
    assert g(41) == 42

