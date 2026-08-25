# -*- coding: utf-8 -*-
# stress test: py316_class_annotations_deferred
# category: python_316_features
#
# Target: Class-level annotations are also deferred in 3.16. Accessing __annotations__ on a class triggers evaluation.
#
# Tags: ['PEP-649', 'class-annotations', 'py3.16']
import sys

if sys.version_info >= (3, 14):
    eval_log = []

    def record(name):
        eval_log.append(name)
        return name

    class C:
        x: record("x")
        y: record("y")
        z: record("z")

    # Annotations should not have been evaluated yet
    assert eval_log == []

    # Accessing __annotations__ triggers evaluation
    ann = C.__annotations__
    assert sorted(eval_log) == ["x", "y", "z"]
    assert set(ann.keys()) == {"x", "y", "z"}
else:
    # On older Python, class annotations are eager
    eval_log = []

    def record(name):
        eval_log.append(name)
        return name

    class C:
        x: record("x")
        y: record("y")
        z: record("z")

    # All annotations should have been evaluated at class creation
    assert "x" in eval_log
    assert "y" in eval_log
    assert "z" in eval_log
    assert set(C.__annotations__.keys()) == {"x", "y", "z"}

