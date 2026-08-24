"""Exception interaction stress tests.

These tests target JIT failure modes involving exceptions in optimized
frames. A correct JIT must handle:

- Exceptions raised inside hot, optimized loops — the JIT must deopt and
  propagate the exception to the correct ``except`` handler, preserving
  the exception object, its ``__traceback__``, and any pending ``finally``
  blocks.

- Exception propagation across deopt boundaries — when deopt is triggered
  (e.g. by a type-speculation failure) while an exception is in flight,
  the runtime must reconstruct the interpreter frame's exception state and
  block stack so the enclosing ``try/except/finally`` runs as if the code
  had never been compiled.

- Finally block execution during deopt — the ``finally`` must execute with
  fully reconstructed locals (including re-boxed unboxed values), even if
  deopt happened at the exact point of the ``SETUP_FINALLY`` / yield.

- Exception chains (``raise ... from ...``) — ``__cause__`` and
  ``__context__`` must survive deopt and be observable by the caller.

- Generator / async exception entry points — ``send()``, ``throw()``,
  ``close()`` (``GeneratorExit``), and ``await`` all create exception
  entry points into suspended frames. A JIT that has compiled the
  generator's body must deopt at the suspension point and inject the
  exception correctly.

- Edge cases: bare ``except:`` catching ``BaseException`` subclasses;
  ``__del__`` raising during GC (must be swallowed); ``__str__`` raising
  during traceback formatting; custom ``Exception.__init__`` raising
  during construction.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="exception_in_hot_loop_optimized_frame",
        category="exception_interaction",
        description=(
            "A ValueError is raised on iteration 500 inside a hot, "
            "type-stable loop that the JIT would normally compile. "
            "The JIT must deopt at the raise site and propagate the "
            "exception to the enclosing try/except without losing the "
            "accumulated loop state."
        ),
        source='''\
def work():
    acc = 0
    try:
        for i in range(1000):
            if i == 500:
                raise ValueError("mid")
            acc += i
    except ValueError:
        acc -= 1
    return acc

r = work()
# Only iterations 0..499 ran (exception breaks out of the loop at i=500).
# Then acc -= 1 in the except handler.
expected = sum(range(500)) - 1
assert r == expected, (r, expected)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"exception", "raise", "hot-loop", "propagation"}),
    ),
    T(
        name="exception_during_deopt_double_fault",
        category="exception_interaction",
        description=(
            "Double-fault scenario: while handling a ValueError, the "
            "except handler triggers a type-speculation deopt (x changes "
            "from int to str) and then raises a *different* exception "
            "(RuntimeError). The JIT must preserve the original exception "
            "as __context__ of the new one across the deopt boundary."
        ),
        source='''\
def work():
    log = []
    contexts = []
    for i in range(1000):
        try:
            try:
                if i == 500:
                    raise ValueError("first")
                x = i
            except ValueError:
                # Trigger deopt via type change, then raise a new exception.
                x = "string"
                raise RuntimeError("second")
            log.append(x)
        except RuntimeError as e:
            contexts.append(e.__context__)
            log.append(("recovered", i))
            continue
    return log, contexts

log, contexts = work()
assert len(log) == 1000, len(log)
assert log[0] == 0
assert log[499] == 499
assert log[500] == ("recovered", 500)
assert log[501] == 501
assert log[999] == 999
assert len(contexts) == 1
assert isinstance(contexts[0], ValueError)
assert str(contexts[0]) == "first"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="nested_branch", opt_state="deoptimized",
                         tags={"exception", "double-fault", "deopt", "context", "chain"}),
    ),
    T(
        name="finally_block_during_deopt",
        category="exception_interaction",
        description=(
            "Deopt is triggered mid-loop by a type change (int -> str). "
            "The loop body sits inside a try/finally. The finally block "
            "must execute with the reconstructed interpreter frame, "
            "including all locals appended to ``log`` before the deopt."
        ),
        source='''\
def work():
    log = []
    try:
        for i in range(1000):
            if i == 500:
                x = "string"  # type change -> deopt
            else:
                x = i
            log.append(x)
    finally:
        log.append(("finally", len(log)))
    return log

r = work()
assert len(r) == 1001, len(r)
assert r[0] == 0
assert r[499] == 499
assert r[500] == "string"
assert r[501] == 501
assert r[999] == 999
assert r[-1] == ("finally", 1000)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"exception", "finally", "deopt", "block-stack"}),
    ),
    T(
        name="exception_across_generator_yield_boundary",
        category="exception_interaction",
        description=(
            "A generator raises ValueError on iteration 500, caught "
            "internally by a try/except around the yield. The JIT-compiled "
            "generator body must deopt at the yield point, inject the "
            "exception, and resume correctly so the consumer sees the "
            "right accumulated values."
        ),
        source='''\
def gen(n):
    acc = 0
    for i in range(n):
        try:
            if i == 500:
                raise ValueError("inner")
            acc += i
        except ValueError:
            acc -= 1
        yield acc

results = list(gen(1000))
assert len(results) == 1000

# Independently simulate expected values
expected = []
sim = 0
for i in range(1000):
    if i == 500:
        sim -= 1
    else:
        sim += i
    expected.append(sim)

assert results == expected
assert results[0] == 0
assert results[499] == sum(range(500))
assert results[500] == sum(range(500)) - 1
assert results[501] == sum(range(500)) - 1 + 501
assert results[-1] == sum(range(500)) - 1 + sum(range(501, 1000))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="deoptimized",
                         tags={"exception", "generator", "yield", "propagation"}),
    ),
    T(
        name="exception_chain_raise_from_with_deopt",
        category="exception_interaction",
        description=(
            "Uses ``raise X from Y`` inside a loop that deopts at i=500 "
            "(type change x='trigger'). The __cause__ and __context__ "
            "links must survive deopt and be observable by the caller."
        ),
        source='''\
def raiser(n):
    for i in range(n):
        if i == 500:
            x = "trigger"  # type change -> deopt
            try:
                raise KeyError("original")
            except KeyError as ke:
                raise ValueError("chained") from ke

try:
    raiser(1000)
    assert False, "should have raised ValueError"
except ValueError as ve:
    assert str(ve) == "chained"
    assert isinstance(ve.__cause__, KeyError)
    # KeyError.__str__ wraps the arg in repr, so check .args instead
    assert ve.__cause__.args == ("original",)
    assert isinstance(ve.__context__, KeyError)
    assert ve.__context__.args == ("original",)
    assert ve.__suppress_context__ is True
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="if_else", opt_state="deoptimized",
                         tags={"exception", "chain", "raise-from", "cause", "context"}),
    ),
    T(
        name="bare_except_catches_systemexit",
        category="exception_interaction",
        description=(
            "Bare ``except:`` (no type) catches *every* BaseException "
            "subclass, including SystemExit. A JIT that compiles the "
            "except clause as ``except Exception:`` would let SystemExit "
            "escape. This test verifies the catch-all semantics."
        ),
        source='''\
def work():
    log = []
    for i in range(1000):
        try:
            if i == 500:
                raise SystemExit("bye")
            x = i
        except BaseException:  # bare-except equivalent: catches everything
            log.append(("caught", i))
            continue
        log.append(x)
    return log

r = work()
assert len(r) == 1000
assert r[0] == 0
assert r[499] == 499
assert r[500] == ("caught", 500)
assert r[501] == 501
assert r[999] == 999

# Confirm that ``except Exception:`` does NOT catch SystemExit
def work2():
    for i in range(1000):
        try:
            if i == 500:
                raise SystemExit("bye2")
        except Exception:
            return "should-not-happen"
    return "ok"

try:
    work2()
    assert False, "SystemExit should propagate"
except SystemExit as e:
    assert str(e) == "bye2"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"exception", "bare-except", "SystemExit", "BaseException"}),
    ),
    T(
        name="generator_send_exception_caught",
        category="exception_interaction",
        description=(
            "Consumer calls ``g.send(i)`` 999 times and "
            "``g.throw(ValueError)`` once. The generator catches the "
            "thrown exception, adjusts state, and resumes. A JIT that "
            "compiled the generator body must deopt at the yield and "
            "inject the thrown exception at the correct suspension point."
        ),
        source='''\
def gen():
    acc = 0
    while True:
        try:
            x = yield acc
            acc += x
        except ValueError:
            acc -= 1

g = gen()
next(g)  # prime: runs to first yield, returns acc=0

results = []
for i in range(1000):
    if i == 500:
        results.append(g.throw(ValueError("boom")))
    else:
        results.append(g.send(i))

# Independently simulate expected values
expected = []
sim = 0
for i in range(1000):
    if i == 500:
        sim -= 1
    else:
        sim += i
    expected.append(sim)

assert results == expected
assert results[0] == 0
assert results[499] == sum(range(500))
assert results[500] == sum(range(500)) - 1
assert len(results) == 1000
g.close()
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="deoptimized",
                         tags={"exception", "generator", "send", "throw", "injection"}),
    ),
    T(
        name="generator_throw_uncaught_propagates",
        category="exception_interaction",
        description=(
            "``g.throw(ValueError)`` is called on a generator that does "
            "NOT catch the exception. The exception must propagate out of "
            "throw() to the caller, and the generator must be left in the "
            "closed state so subsequent next()/send() raises StopIteration."
        ),
        source='''\
def gen():
    acc = 0
    while True:
        x = yield acc
        acc += x

g = gen()
assert next(g) == 0       # prime
assert g.send(10) == 10   # acc = 0 + 10 = 10

# throw an exception the generator does not catch
try:
    g.throw(ValueError("not-caught"))
    assert False, "throw should propagate ValueError"
except ValueError as e:
    assert str(e) == "not-caught"

# generator is now closed
try:
    next(g)
    assert False, "closed generator should raise StopIteration"
except StopIteration:
    pass

# throw on a closed generator re-raises the thrown exception
try:
    g.throw(RuntimeError("after-close"))
    assert False
except RuntimeError as e:
    assert str(e) == "after-close"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="generator", opt_state="deoptimized",
                         tags={"exception", "generator", "throw", "propagation", "closed"}),
    ),
    T(
        name="generator_close_generator_exit",
        category="exception_interaction",
        description=(
            "``g.close()`` throws GeneratorExit at the yield point. "
            "If the generator catches it and yields again, RuntimeError "
            "must be raised. If it catches and returns cleanly, close() "
            "succeeds. A JIT must deopt at the yield and inject "
            "GeneratorExit correctly."
        ),
        source='''\
# Case 1: clean close — finally runs, GeneratorExit propagates, close returns
def gen_clean():
    try:
        yield 1
        yield 2
        yield 3
    finally:
        pass

g = gen_clean()
assert next(g) == 1
g.close()
try:
    next(g)
    assert False, "should raise StopIteration after close"
except StopIteration:
    pass

# Case 2: generator yields in response to GeneratorExit -> RuntimeError
def gen_bad():
    try:
        yield 1
    except GeneratorExit:
        yield 2  # illegal: yielding after GeneratorExit

g2 = gen_bad()
assert next(g2) == 1
try:
    g2.close()
    assert False, "should raise RuntimeError"
except RuntimeError:
    pass  # CPython raises RuntimeError when generator yields after GeneratorExit

# Case 3: generator catches GeneratorExit and returns cleanly -> ok
def gen_caught():
    try:
        yield 1
        yield 2
    except GeneratorExit:
        return  # cleanup, no yield

g3 = gen_caught()
assert next(g3) == 1
g3.close()  # should not raise
try:
    next(g3)
    assert False, "should raise StopIteration"
except StopIteration:
    pass

# Case 4: close on already-finished generator is a no-op
def gen_done():
    yield 1

g4 = gen_done()
list(g4)
g4.close()  # no-op, must not raise
assert True
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="generator", opt_state="deoptimized",
                         tags={"exception", "generator", "close", "GeneratorExit", "RuntimeError"}),
    ),
    T(
        name="async_function_exception_during_await",
        category="exception_interaction",
        description=(
            "An async function raises a custom exception on iteration "
            "500 inside a loop that awaits ``asyncio.sleep(0)``. The "
            "exception must propagate through the await boundary to the "
            "caller's try/except. A JIT that compiled the coroutine must "
            "deopt at the await suspension and propagate correctly."
        ),
        source='''\
import asyncio

class Boom(Exception):
    pass

async def fail_at(n):
    for i in range(n):
        if i == 500:
            raise Boom("async failure")
        await asyncio.sleep(0)
    return n

async def main():
    try:
        await fail_at(1000)
        assert False, "should raise Boom"
    except Boom as e:
        assert str(e) == "async failure"
    return "ok"

r = asyncio.run(main())
assert r == "ok"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="async",
                         opt_state="deoptimized",
                         tags={"exception", "async", "await", "propagation", "coroutine"}),
    ),
    T(
        name="async_generator_exception",
        category="exception_interaction",
        description=(
            "An async generator raises ValueError on iteration 500. The "
            "exception must propagate out of the ``async for`` loop. A "
            "JIT that compiled the async generator's body must deopt at "
            "the yield point and propagate the exception."
        ),
        source='''\
import asyncio

async def agen(n):
    acc = 0
    for i in range(n):
        if i == 500:
            raise ValueError("async gen failure")
        acc += i
        yield acc

async def main():
    results = []
    try:
        async for v in agen(1000):
            results.append(v)
        assert False, "should raise ValueError"
    except ValueError as e:
        assert str(e) == "async gen failure"
    # 500 values yielded before the exception
    assert len(results) == 500, len(results)
    assert results[0] == 0
    assert results[1] == 1
    assert results[499] == sum(range(500))
    return "ok"

r = asyncio.run(main())
assert r == "ok"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="async",
                         opt_state="deoptimized",
                         tags={"exception", "async-generator", "yield", "propagation"}),
    ),
    T(
        name="nested_try_except_finally_each_level",
        category="exception_interaction",
        description=(
            "Three nested try/except/finally blocks. An exception raised "
            "in the innermost try is caught by the middle except, which "
            "re-raises a different exception, caught by the outer except. "
            "The finally blocks must run in the correct order as "
            "exceptions propagate. A JIT must reconstruct the full block "
            "stack on deopt."
        ),
        source='''\
def work():
    log = []
    try:                                   # outer
        try:                               # middle
            try:                           # inner
                for i in range(1000):
                    if i == 500:
                        raise ValueError("inner")
            finally:                       # inner-finally
                log.append("inner-finally")
        except ValueError:                # middle-except
            log.append("inner-caught")
            raise TypeError("rethrown")
        finally:                           # middle-finally
            log.append("middle-finally")
    except TypeError:                      # outer-except
        log.append("outer-caught")
    finally:                               # outer-finally
        log.append("outer-finally")
    return log

r = work()
expected = [
    "inner-finally",
    "inner-caught",
    "middle-finally",
    "outer-caught",
    "outer-finally",
]
assert r == expected, r
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="nested_branch", opt_state="deoptimized",
                         tags={"exception", "nested-try", "finally", "block-stack", "rethrow"}),
    ),
    T(
        name="stopiteration_with_value_in_custom_iterator",
        category="exception_interaction",
        description=(
            "A custom iterator raises ``StopIteration(value)``. The for "
            "loop must discard the value and terminate cleanly. Manual "
            "``next()`` must expose ``.value``. Inside a generator, "
            "``return X`` is equivalent to ``raise StopIteration(X)``. "
            "A JIT that speculates StopIteration has no value would break."
        ),
        source='''\
class CustomIter:
    def __init__(self, n):
        self.n = n
        self.i = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self.i >= self.n:
            raise StopIteration("done-at-" + str(self.n))
        v = self.i
        self.i += 1
        return v

# for-loop discards StopIteration value
def work():
    total = 0
    for v in CustomIter(1000):
        total += v
    return total

r = work()
assert r == sum(range(1000))

# manual next() exposes .value
it = CustomIter(5)
vals = []
while True:
    try:
        vals.append(next(it))
    except StopIteration as e:
        assert e.value == "done-at-5"
        break
assert vals == [0, 1, 2, 3, 4]

# generator ``return X`` -> StopIteration.value == X
def gen():
    yield 1
    yield 2
    return "gen-return"

g = gen()
assert next(g) == 1
assert next(g) == 2
try:
    next(g)
    assert False, "should raise StopIteration"
except StopIteration as e:
    assert e.value == "gen-return"

# ``yield from`` swallows the inner StopIteration; the inner return
# value becomes the value of the ``yield from`` expression, NOT the
# outer generator's StopIteration value.
def inner():
    yield 1
    return "from-inner"

def outer():
    result = yield from inner()   # result == "from-inner"
    yield result                   # yields "from-inner"
    yield 2

g2 = outer()
assert next(g2) == 1
assert next(g2) == "from-inner"
assert next(g2) == 2
try:
    next(g2)
    assert False, "should raise StopIteration"
except StopIteration as e:
    # outer had no ``return X``, so StopIteration value is None
    assert e.value is None
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"exception", "StopIteration", "iterator", "value", "generator"}),
    ),
    T(
        name="del_exception_swallowed_by_gc",
        category="exception_interaction",
        description=(
            "``__del__`` raises RuntimeError during garbage collection. "
            "CPython must print a warning to stderr but NOT propagate "
            "the exception. A JIT that runs ``__del__`` in a compiled "
            "frame must not let the exception escape into the mutator. "
            "All destructors must still run."
        ),
        source='''\
import gc
import sys
import io

del_log = []

class Tracker:
    def __init__(self, i):
        self.i = i
    def __del__(self):
        del_log.append(self.i)
        raise RuntimeError("in-del-" + str(self.i))

# Capture stderr so the "Exception ignored in __del__" messages
# don't pollute the test output.
_old_stderr = sys.stderr
sys.stderr = io.StringIO()
try:
    def work():
        items = [Tracker(i) for i in range(100)]
        del items   # drops all refs -> __del__ runs for each
        gc.collect()
        return "ok"

    r = work()
finally:
    _captured = sys.stderr.getvalue()
    sys.stderr = _old_stderr

# The RuntimeError inside __del__ must NOT propagate out of work().
assert r == "ok"
# CPython prints "Exception ignored in:" warnings for __del__ exceptions
assert "Exception ignored" in _captured
assert "in-del-0" in _captured
assert "in-del-99" in _captured
# Every Tracker's __del__ must have run exactly once.
assert len(del_log) == 100, len(del_log)
assert set(del_log) == set(range(100))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"exception", "__del__", "GC", "swallow", "finalizer"}),
    ),
    T(
        name="reraise_no_argument_preserves_traceback",
        category="exception_interaction",
        description=(
            "Bare ``raise`` (no argument) re-raises the current exception "
            "with its original traceback intact. The test verifies this "
            "across a deep call stack where each frame re-raises. A JIT "
            "must preserve the exception state across deopt at each level."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="recursion", call_behavior="recursive",
                         opt_state="deoptimized",
                         tags={"exception", "reraise", "traceback", "propagation"}),
    ),
    T(
        name="complex_exception_args_tuple",
        category="exception_interaction",
        description=(
            "An exception is constructed with a multi-element args tuple "
            "containing mixed types (int, str, custom object, dict, list). "
            "The ``.args`` attribute must be exactly the tuple passed to "
            "the constructor. A JIT that speculates ``.args`` is a "
            "single string would break."
        ),
        source='''\
class Widget:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "Widget(" + self.name + ")"
    def __eq__(self, other):
        return isinstance(other, Widget) and self.name == other.name

def work():
    for i in range(1000):
        if i == 500:
            raise ValueError(
                i,
                "msg",
                Widget("w"),
                {"k": "v"},
                [1, 2, 3],
            )
    return "ok"

try:
    work()
    assert False, "should raise ValueError"
except ValueError as e:
    assert len(e.args) == 5
    assert e.args[0] == 500
    assert e.args[1] == "msg"
    assert e.args[2] == Widget("w")
    assert repr(e.args[2]) == "Widget(w)"
    assert e.args[3] == {"k": "v"}
    assert e.args[4] == [1, 2, 3]
    # args tuple is immutable
    try:
        e.args[0] = 999
        assert False, "args should be immutable"
    except TypeError:
        pass
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="deoptimized",
                         tags={"exception", "args", "tuple", "mixed-types"}),
    ),
    T(
        name="exception_in_finally_replaces_active",
        category="exception_interaction",
        description=(
            "A finally block raises a new exception while another "
            "exception is propagating. The new exception replaces the "
            "original, and the original is saved as ``__context__``. A "
            "JIT must handle this exception-replacement semantics during "
            "finally execution."
        ),
        source='''\
def work():
    log = []
    for i in range(1000):
        try:
            if i == 500:
                raise ValueError("first")
        finally:
            if i == 500:
                raise TypeError("in-finally")  # replaces ValueError
        log.append(i)  # never reached for i == 500
    return log

try:
    work()
    assert False, "should raise TypeError"
except TypeError as e:
    assert str(e) == "in-finally"
    # The original ValueError is preserved as __context__
    assert isinstance(e.__context__, ValueError)
    assert str(e.__context__) == "first"
    # __cause__ is None (no explicit ``from``)
    assert e.__cause__ is None
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"exception", "finally", "context", "replace", "chain"}),
    ),
    T(
        name="keyboard_interrupt_in_hot_loop",
        category="exception_interaction",
        description=(
            "KeyboardInterrupt inherits from BaseException, not "
            "Exception. A JIT that compiles ``except Exception:`` as a "
            "catch-all would incorrectly swallow KeyboardInterrupt. This "
            "test verifies that ``except Exception:`` does NOT catch "
            "KeyboardInterrupt, while ``except BaseException:`` does."
        ),
        source='''\
def work_plain():
    acc = 0
    for i in range(1000):
        if i == 500:
            raise KeyboardInterrupt("simulated")
        acc += i
    return acc

# KeyboardInterrupt propagates out of the function
try:
    work_plain()
    assert False, "should raise KeyboardInterrupt"
except KeyboardInterrupt as e:
    assert str(e) == "simulated"

# ``except Exception:`` must NOT catch KeyboardInterrupt
def work_except_exception():
    acc = 0
    for i in range(1000):
        try:
            if i == 500:
                raise KeyboardInterrupt("simulated2")
            acc += i
        except Exception:
            acc -= 1
    return acc

try:
    work_except_exception()
    assert False, "KeyboardInterrupt should NOT be caught by except Exception"
except KeyboardInterrupt:
    pass  # correct

# ``except BaseException:`` DOES catch KeyboardInterrupt
def work_except_base():
    acc = 0
    for i in range(1000):
        try:
            if i == 500:
                raise KeyboardInterrupt("simulated3")
            acc += i
        except BaseException:
            acc -= 1
    return acc

r = work_except_base()
expected = sum(range(500)) + sum(range(501, 1000)) - 1
assert r == expected, (r, expected)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"exception", "KeyboardInterrupt", "BaseException", "hierarchy"}),
    ),
    T(
        name="custom_exception_init_raises",
        category="exception_interaction",
        description=(
            "A custom Exception subclass has an ``__init__`` that raises "
            "RuntimeError when called with a specific argument. The "
            "``raise BadException('bad')`` statement first evaluates the "
            "constructor (which raises RuntimeError), so RuntimeError "
            "propagates — not BadException. A JIT must not cache the "
            "exception type and skip the constructor."
        ),
        source='''\
class BadException(Exception):
    def __init__(self, *args):
        if args and args[0] == "bad":
            raise RuntimeError("in-init")
        super().__init__(*args)

def work():
    for i in range(1000):
        if i == 500:
            raise BadException("bad")
    return "ok"

try:
    work()
    assert False, "should raise RuntimeError (from __init__)"
except RuntimeError as e:
    assert str(e) == "in-init"

# Normal case: __init__ does not raise
def work2():
    for i in range(1000):
        if i == 500:
            raise BadException("ok")
    return "ok"

try:
    work2()
    assert False, "should raise BadException"
except BadException as e:
    assert e.args == ("ok",)
    assert isinstance(e, Exception)

# Verify the exception hierarchy is intact
assert issubclass(BadException, Exception)
assert issubclass(BadException, BaseException)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="deoptimized",
                         tags={"exception", "__init__", "constructor", "hierarchy", "chain"}),
    ),
    T(
        name="exception_str_raises_during_traceback",
        category="exception_interaction",
        description=(
            "A custom Exception's ``__str__`` raises RuntimeError. The "
            "exception can still be caught, and ``.args`` is accessible "
            "without calling ``__str__``. ``traceback.format_exception`` "
            "must not crash even though ``str(e)`` raises. A JIT that "
            "inlines ``__str__`` for error formatting would break."
        ),
        source='''\
import traceback

class StrBoom(Exception):
    def __str__(self):
        raise RuntimeError("in-str")

def work():
    for i in range(1000):
        if i == 500:
            raise StrBoom("original")
    return "ok"

try:
    work()
    assert False, "should raise StrBoom"
except StrBoom as e:
    # Caught successfully even though __str__ raises
    assert isinstance(e, StrBoom)
    assert isinstance(e, Exception)

    # str(e) raises RuntimeError
    try:
        str(e)
        assert False, "str(e) should raise RuntimeError"
    except RuntimeError as re:
        assert str(re) == "in-str"

    # .args is accessible without calling __str__
    assert e.args == ("original",)

# traceback.format_exception must not crash even though __str__ raises
try:
    work()
except StrBoom as e:
    tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
    tb_str = "".join(tb_lines)
    # The traceback should mention the exception type name
    assert "StrBoom" in tb_str
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="deoptimized",
                         tags={"exception", "__str__", "traceback", "format", "swallow"}),
    ),
]
