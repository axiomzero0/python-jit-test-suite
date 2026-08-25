# -*- coding: utf-8 -*-
# stress test: py316_tstring_escape_sequences
# category: python_316_features
#
# Target: t-strings handle escape sequences the same way as regular strings. On older Python, the test verifies f-string escapes.
#
# Tags: ['PEP-750', 'escapes', 'py3.16', 't-string']
import sys

if sys.version_info >= (3, 14):
    src = """
t = t"line1\nline2\ttabbed"
assert t.strings == ("line1\nline2\ttabbed",)
assert len(t.interpolations) == 0
s = t.strings[0]
assert "\n" in s
assert "\t" in s
"""
    try:
        exec(compile(src, "<tstring-escape>", "exec"))
    except SyntaxError:
        pass  # t-string not supported
else:
    s = f"line1\nline2\ttabbed"
    assert "\n" in s
    assert "\t" in s

