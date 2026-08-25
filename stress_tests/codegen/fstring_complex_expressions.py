# -*- coding: utf-8 -*-
# stress test: fstring_complex_expressions
# category: codegen
#
# Target: f-strings embed arbitrary expressions, including method calls, indexing, dict access, nested f-strings, ternaries, and format specs. The JIT must lower each embedded expression to its own evaluation, then format the result.
#
# Tags: ['codegen', 'format', 'fstring']
x = 42
y = [1, 2, 3]
name = "world"

# Simple
assert f"hello {name}" == "hello world"

# Arithmetic expression
assert f"{x + 1}" == "43"

# Method call
assert f"{name.upper()}" == "WORLD"

# Indexing and slicing
assert f"{y[1]}" == "2"
assert f"{y[-1]}" == "3"

# Format specifiers
assert f"{x:08d}" == "00000042"
assert f"{3.14159:.2f}" == "3.14"
assert f"{x:>10}" == "        42"
assert f"{x:<10}|" == "42        |"
assert f"{x:^10}" == "    42    "
assert f"{255:#x}" == "0xff"

# Dict access
d = {'key': 'value'}
assert f"{d['key']}" == "value"

# Conditional inside f-string
assert f"{'pos' if x > 0 else 'neg'}" == "pos"

# Function call inside f-string
def double(n):
    return n * 2
assert f"{double(x)}" == "84"

# Nested f-string
assert f"{f'{x}' * 2}" == "4242"

# Multiple expressions
assert f"{x} + {y[0]} = {x + y[0]}" == "42 + 1 = 43"

# Conversion flags
class Obj:
    def __str__(self):
        return 'str-form'
    def __repr__(self):
        return 'repr-form'
o = Obj()
assert f"{o}" == "str-form"
assert f"{o!r}" == "repr-form"
assert f"{o!s}" == "str-form"
assert f"{'hi'!a}" == "'hi'"

# Lambda inside f-string
assert f"{(lambda n: n + 1)(5)}" == "6"

# Walrus inside f-string
assert f"{(s := 99)} and {s}" == "99 and 99"
assert s == 99

