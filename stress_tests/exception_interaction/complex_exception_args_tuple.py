# -*- coding: utf-8 -*-
# stress test: complex_exception_args_tuple
# category: exception_interaction
# opt_state: (runs across all 6 states)
#
# Target: An exception is constructed with a multi-element args tuple containing mixed types (int, str, custom object, dict, list). The ``.args`` attribute must be exactly the tuple passed to the constructor. A JIT that speculates ``.args`` is a single string would break.
#
# Tags: ['args', 'exception', 'mixed-types', 'tuple']
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

