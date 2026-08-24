# -*- coding: utf-8 -*-
# stress test: keyboard_interrupt_in_hot_loop
# category: exception_interaction
# opt_state: (runs across all 6 states)
#
# Target: KeyboardInterrupt inherits from BaseException, not Exception. A JIT that compiles ``except Exception:`` as a catch-all would incorrectly swallow KeyboardInterrupt. This test verifies that ``except Exception:`` does NOT catch KeyboardInterrupt, while ``except BaseException:`` does.
#
# Tags: ['BaseException', 'KeyboardInterrupt', 'exception', 'hierarchy']
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

