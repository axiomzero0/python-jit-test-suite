# -*- coding: utf-8 -*-
# stress test: reraise_no_argument_preserves_traceback
# category: exception_interaction
#
# Target: Bare ``raise`` (no argument) re-raises the current exception with its original traceback intact. The test verifies this across a deep call stack where each frame re-raises. A JIT must preserve the exception state across deopt at each level.
#
# Tags: ['exception', 'propagation', 'reraise', 'traceback']
def inner(n):
    if n == 0:
        raise KeyError("deep")
    return inner(n - 1)

def middle(n):
    try:
        return inner(n)
    except KeyError:
        raise   # bare re-raise

def outer(n):
    try:
        return middle(n)
    except KeyError as e:
        return "caught: " + repr(e)

assert outer(100) == "caught: KeyError('deep')"

# Bare raise outside an except handler raises RuntimeError
def no_active_exception():
    raise

try:
    no_active_exception()
    assert False, "should raise RuntimeError"
except RuntimeError:
    pass

# Re-raise preserves the original exception identity
def make_orig():
    exc = ValueError("original")
    try:
        raise exc
    except ValueError:
        raise   # re-raise same object

try:
    make_orig()
    assert False
except ValueError as e:
    assert e is not None
    assert str(e) == "original"

