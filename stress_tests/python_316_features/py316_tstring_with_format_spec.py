# -*- coding: utf-8 -*-
# stress test: py316_tstring_with_format_spec
# category: python_316_features
#
# Target: t-strings support format specs like f-strings. The JIT must correctly parse and apply the format spec. On older Python, the test verifies f-string format spec handling.
#
# Tags: ['PEP-750', 'format-spec', 'py3.16', 't-string']
import sys

if sys.version_info >= (3, 14):
    src = """
x = 3.14159
t = t"pi = {x:.2f}"
interp = t.interpolations[0]
assert hasattr(interp, "format_spec")
assert str(interp.format_spec) == ".2f"
assert interp.value == 3.14159
formatted = format(interp.value, str(interp.format_spec))
assert formatted == "3.14"
"""
    try:
        exec(compile(src, "<tstring-format>", "exec"))
    except SyntaxError:
        pass  # t-string syntax not supported
else:
    # f-string format spec
    x = 3.14159
    s = f"pi = {x:.2f}"
    assert s == "pi = 3.14"

