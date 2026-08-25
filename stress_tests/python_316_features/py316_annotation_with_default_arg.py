# -*- coding: utf-8 -*-
# stress test: py316_annotation_with_default_arg
# category: python_316_features
#
# Target: Default argument values are evaluated eagerly at def time, but annotations are deferred. The JIT must distinguish these two evaluation timings.
#
# Tags: ['PEP-649', 'annotations', 'defaults', 'py3.16']
import sys

eval_log = []

def record(s, v=None):
    eval_log.append((s, v))
    return v if v is not None else s

if sys.version_info >= (3, 14):
    # Default ARG is evaluated eagerly; annotation is deferred
    def f(x: record("ann_x") = record("default_x", 99)):
        return x

    # At this point, only the default value should have been evaluated
    assert ("default_x", 99) in eval_log
    assert ("ann_x", None) not in eval_log

    # Calling without args uses the default
    assert f() == 99

    # Calling with an arg uses the arg
    assert f(42) == 42

    # Accessing annotations triggers deferred evaluation
    ann = f.__annotations__
    assert any(s == "ann_x" for s, _ in eval_log)
else:
    # On older Python, BOTH are evaluated eagerly at def time
    def f(x: record("ann_x") = record("default_x", 99)):
        return x

    assert ("default_x", 99) in eval_log
    assert ("ann_x", None) in eval_log  # eager on 3.12

    assert f() == 99
    assert f(42) == 42

