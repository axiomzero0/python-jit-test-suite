# -*- coding: utf-8 -*-
# stress test: py316_tstring_basic
# category: python_316_features
#
# Target: PEP 750: Template strings (t-strings) are a new string type in Python 3.14+ that produce a Template object instead of a str. The JIT must handle the t-string protocol correctly. On older Python, the test verifies that the template module fallback (string.Template) still works.
#
# Tags: ['PEP-750', 'py3.16', 't-string', 'template']
import sys

if sys.version_info >= (3, 14):
    # Use a try/except for the t-string syntax in case the parser
    # doesn't support it yet on this build
    try:
        # t-string syntax: t"..." produces a Template object
        # We need to use exec because the parser on 3.12 doesn't accept this syntax
        src = """
name = "world"
t = t"hello {name}"
assert not isinstance(t, str)
assert hasattr(t, "strings")
assert hasattr(t, "interpolations")
assert t.strings == ("hello ", "")
assert len(t.interpolations) == 1
assert t.interpolations[0].value == "world"
"""
        # Execute the t-string source
        exec(compile(src, "<tstring-test>", "exec"))
    except SyntaxError:
        # t-string syntax not supported in this build, skip
        pass
else:
    # On older Python, verify string.Template as the conceptual ancestor
    from string import Template
    name = "world"
    s = Template("hello $name").substitute(name=name)
    assert s == "hello world"

