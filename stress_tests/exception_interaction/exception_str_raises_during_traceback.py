# -*- coding: utf-8 -*-
# stress test: exception_str_raises_during_traceback
# category: exception_interaction
#
# Target: A custom Exception's ``__str__`` raises RuntimeError. The exception can still be caught, and ``.args`` is accessible without calling ``__str__``. ``traceback.format_exception`` must not crash even though ``str(e)`` raises. A JIT that inlines ``__str__`` for error formatting would break.
#
# Tags: ['__str__', 'exception', 'format', 'swallow', 'traceback']
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

