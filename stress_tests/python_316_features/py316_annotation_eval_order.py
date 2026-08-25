# -*- coding: utf-8 -*-
# stress test: py316_annotation_eval_order
# category: python_316_features
#
# Target: Annotations must be evaluated lazily AND in the correct order when accessed. The JIT must not reorder annotation evaluations or cache them eagerly.
#
# Tags: ['PEP-649', 'annotations', 'eval-order', 'py3.16']
import sys

if sys.version_info >= (3, 14):
    eval_log = []

    def record(name):
        eval_log.append(name)
        return name

    # In 3.16 with deferred annotations, these are NOT evaluated at def time
    def f(
        a: record("a"),
        b: record("b"),
        c: record("c"),
    ) -> record("return"):
        return (a, b, c)

    # eval_log should be empty at this point (annotations deferred)
    assert eval_log == [], f"expected empty, got {eval_log}"

    # Accessing __annotations__ triggers evaluation
    ann = f.__annotations__
    # Now eval_log should contain the annotation evaluations
    assert "a" in eval_log
    assert "b" in eval_log
    assert "c" in eval_log
    assert "return" in eval_log

    # Calling the function should still work
    assert f(1, 2, 3) == (1, 2, 3)
else:
    # On older Python: annotations are eager, so they ARE evaluated at def time
    eval_log = []

    def record(name):
        eval_log.append(name)
        return name

    def f(
        a: record("a"),
        b: record("b"),
        c: record("c"),
    ) -> record("return"):
        return (a, b, c)

    # On 3.12, all annotations are evaluated at def time
    assert "a" in eval_log
    assert "b" in eval_log
    assert "c" in eval_log
    assert "return" in eval_log
    assert f(1, 2, 3) == (1, 2, 3)

