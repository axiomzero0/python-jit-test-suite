# -*- coding: utf-8 -*-
# stress test: generator_close_generator_exit
# category: exception_interaction
#
# Target: ``g.close()`` throws GeneratorExit at the yield point. If the generator catches it and yields again, RuntimeError must be raised. If it catches and returns cleanly, close() succeeds. A JIT must deopt at the yield and inject GeneratorExit correctly.
#
# Tags: ['GeneratorExit', 'RuntimeError', 'close', 'exception', 'generator']
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

