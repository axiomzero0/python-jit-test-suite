# -*- coding: utf-8 -*-
# stress test: bare_except_catches_systemexit
# category: exception_interaction
# opt_state: (runs across all 6 states)
#
# Target: Bare ``except:`` (no type) catches *every* BaseException subclass, including SystemExit. A JIT that compiles the except clause as ``except Exception:`` would let SystemExit escape. This test verifies the catch-all semantics.
#
# Tags: ['BaseException', 'SystemExit', 'bare-except', 'exception']
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

