# -*- coding: utf-8 -*-
# stress test: string_percent_format_operator
# category: codegen
#
# Target: The % operator on strings performs printf-style formatting. The JIT must support %d/%s/%f/%x/%o/%r format specifiers, named-argument formatting via a dict, and width/precision modifiers.
#
# Tags: ['codegen', 'format', 'percent']
# Basic positional
assert "%d + %d = %d" % (2, 3, 5) == "2 + 3 = 5"

# String
assert "hello %s" % "world" == "hello world"
assert "%r" % "hi" == "'hi'"

# Float formatting
assert "%.2f" % 3.14159 == "3.14"
assert "%.4f" % 3.14159 == "3.1416"
assert "%e" % 12345.678 == "1.234568e+04"

# Width and padding
assert "%5d" % 42 == "   42"
assert "%-5d|" % 42 == "42   |"
assert "%05d" % 42 == "00042"

# Hex and octal
assert "%x" % 255 == "ff"
assert "%X" % 255 == "FF"
assert "%o" % 64 == "100"
assert "%#x" % 255 == "0xff"
assert "%#o" % 64 == "0o100"

# Named args via dict
assert "%(name)s is %(age)d" % {'name': 'Bob', 'age': 30} == "Bob is 30"

# Mixed positional and repr
assert "%s=%r" % ('x', [1, 2]) == "x=[1, 2]"

# Percent literal
assert "100%%" % () == "100%"
assert "%d%%" % 50 == "50%"

# Width and precision with *
assert "%*d" % (5, 42) == "   42"
assert "%.*f" % (2, 3.14159) == "3.14"

# Multiple args
assert "%s %d %f" % ('count', 5, 2.5) == "count 5 2.500000"

# Tuple formatting (single arg must be a tuple for multi-spec)
result = "%s and %s" % ('a', 'b')
assert result == "a and b"

# Single-element tuple
result = "%s" % ('only',)
assert result == "only"

