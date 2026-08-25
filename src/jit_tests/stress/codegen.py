"""Code generation stress tests.

These tests target specific bytecode patterns the JIT must lower
correctly. The interpreter implements each of these via dedicated
opcodes; the JIT must preserve their exact semantics, including
side-effect ordering, short-circuiting, and one-shot evaluation.

Failure modes covered:
- Mixed operator precedence and evaluation order
- Ternary short-circuit (only one branch evaluated)
- Boolean `and`/`or` short-circuit and result value (not always bool)
- Walrus operator in a comprehension binding to enclosing scope
- Chained multiple assignment evaluating RHS exactly once
- Augmented assignment dispatching to __iadd__ then __add__
- Chained comparison evaluating middle operand once
- Tuple unpacking in a for loop (including starred targets)
- Star-expression in a call (positional unpacking)
- Double-star in a call (keyword unpacking)
- f-string with complex embedded expressions
- % string formatting with various format specs
- Slicing with positive and negative step
- Multiple return values packed into a tuple
- Mutable default argument evaluated once at def time
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="operator_precedence_evaluation_order",
        category="codegen",
        description=(
            "A complex expression mixes arithmetic, power, unary, "
            "bitwise, and shift operators. The JIT must emit operations "
            "in CPython's documented precedence order, evaluating each "
            "operand exactly once."
        ),
        source='''\
# Arithmetic precedence: ** binds tighter than *, which binds tighter than +/-
result = 2 + 3 * 4 ** 2 - 1
# 4**2 = 16; 3*16 = 48; 2+48 = 50; 50-1 = 49
assert result == 49

# Unary minus
x = -5
y = -x * 2 + 3
# -x = 5; 5*2 = 10; 10+3 = 13
assert y == 13

# Bitwise precedence: & higher than |, ^ between
r = 1 | 2 & 3  # 2 & 3 = 2; 1 | 2 = 3
assert r == 3
r = 5 ^ 1 | 2  # 5 ^ 1 = 4; 4 | 2 = 6
assert r == 6

# Shifts: + binds tighter than <<
r = 1 + 2 << 3  # (1+2) << 3 = 24
assert r == 24
r = 16 >> 1 + 1  # 16 >> (1+1) = 16 >> 2 = 4
assert r == 4

# Chained comparison with all operators distinct
a, b, c = 1, 2, 3
assert -1 < a < b < c < 4

# Mixed comparison and arithmetic
r = 1 + 1 == 2 < 3
assert r is True

# Power is right-associative
r = 2 ** 3 ** 2  # 2 ** (3 ** 2) = 2 ** 9 = 512
assert r == 512

# Ternary has lower precedence than most binary ops
r = 1 if True else 2 + 3  # parses as (1 if True else 2) + 3
# Actually: `1 if True else (2 + 3)` — ternary is lowest precedence
# so the entire RHS is the false branch. Verify in CPython:
assert (1 if True else 2 + 3) == 1
assert (1 if False else 2 + 3) == 5
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"codegen", "precedence", "binop"}),
    ),
    T(
        name="ternary_short_circuit",
        category="codegen",
        description=(
            "Ternary `a if cond else b` must only evaluate the chosen "
            "branch. The other branch must not be evaluated, so any "
            "side effects in it must not fire. Nested ternaries must "
            "short-circuit at each level."
        ),
        source='''\
calls = []

def true_branch():
    calls.append('T')
    return 'T'

def false_branch():
    calls.append('F')
    return 'F'

# True condition: only true_branch called
assert (true_branch() if True else false_branch()) == 'T'
assert calls == ['T']
calls.clear()

# False condition: only false_branch called
assert (true_branch() if False else false_branch()) == 'F'
assert calls == ['F']
calls.clear()

# Nested ternary (ladder)
def sign(x):
    return 'pos' if x > 0 else ('zero' if x == 0 else 'neg')

assert sign(5) == 'pos'
assert sign(0) == 'zero'
assert sign(-3) == 'neg'
assert calls == []  # nothing called in this ladder

# Side effect in condition is fine
counter = [0]
def cond():
    counter[0] += 1
    return True
result = 'A' if cond() else 'B'
assert result == 'A'
assert counter[0] == 1

# Falsy non-bool condition
assert ('yes' if 0 else 'no') == 'no'
assert ('yes' if '' else 'no') == 'no'
assert ('yes' if [] else 'no') == 'no'
assert ('yes' if 1 else 'no') == 'yes'
assert ('yes' if [0] else 'no') == 'yes'
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="cold",
                         tags={"codegen", "ternary", "short-circuit"}),
    ),
    T(
        name="boolean_and_or_short_circuit",
        category="codegen",
        description=(
            "`and` returns the first falsy operand (or the last truthy "
            "one), short-circuiting so RHS is not evaluated if LHS "
            "determines the result. `or` is the dual. Result is the "
            "operand value, not coerced to bool."
        ),
        source='''\
calls = []

def t():
    calls.append('t')
    return True

def f():
    calls.append('f')
    return False

# `and` short-circuits on False: only f() called
assert (f() and t()) is False
assert calls == ['f']
calls.clear()

# `or` short-circuits on True: only t() called
assert (t() or f()) is True
assert calls == ['t']
calls.clear()

# Truthy non-bool returned as-is
def five():
    calls.append('five')
    return 5
assert (five() or t()) == 5
assert calls == ['five']  # t not called
calls.clear()

# `and` returns last truthy or first falsy
assert (5 and 6 and 7) == 7
assert (0 and 5) == 0
assert (5 and 0 and 7) == 0

# `or` returns first truthy or last falsy
assert (0 or '' or 7) == 7
assert (0 or '') == ''
assert (0 or None or False) is False

# Side effect ordering with mixed operators
log = []
def log_v(name, v):
    log.append(name)
    return v

# and: evaluates left-to-right, stops at first falsy
log.clear()
result = log_v('a', 1) and log_v('b', 0) and log_v('c', 1)
assert result == 0
assert log == ['a', 'b']

# or: evaluates left-to-right, stops at first truthy
log.clear()
result = log_v('a', 0) or log_v('b', 1) or log_v('c', 0)
assert result == 1
assert log == ['a', 'b']
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"codegen", "and-or", "short-circuit"}),
    ),
    T(
        name="walrus_in_comprehension",
        category="codegen",
        description=(
            "The walrus operator inside a comprehension binds to the "
            "enclosing function scope (not the comprehension's implicit "
            "scope). After the comprehension runs, the bound name is "
            "visible in the enclosing scope and holds the last assigned "
            "value."
        ),
        source='''\
data = [1, 2, 3, 4, 5, 6]

# Walrus in expression position
results = [(y := x * 2, y + 1) for x in data]
assert results == [(2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13)]
# `y` is bound in the enclosing scope to the last value
assert y == 12

# Walrus in filter condition
nums = [1, 2, 3, 4, 5]
filtered = [v for x in nums if (v := x * x) > 5]
assert filtered == [9, 16, 25]
assert v == 25

# Walrus in dict comprehension
d = {x: (s := x + 1) for x in range(3)}
assert d == {0: 1, 1: 2, 2: 3}
assert s == 3

# Walrus in set comprehension
s_set = {(y := x * 10) for x in range(3)}
assert s_set == {0, 10, 20}
assert y == 20

# Walrus binding used later in the same expression
xs = [1, -2, 3, -4]
signs = [(sign := ('pos' if x > 0 else 'neg'), x) for x in xs]
assert signs == [('pos', 1), ('neg', -2), ('pos', 3), ('neg', -4)]
assert sign == 'neg'  # last value
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="cold",
                         tags={"codegen", "walrus", "comprehension"}),
    ),
    T(
        name="multiple_assignment_eval_once",
        category="codegen",
        description=(
            "`a = b = c = expr` evaluates `expr` exactly once and binds "
            "all three names to that single object. Mutations through "
            "any name affect all of them (they are aliases)."
        ),
        source='''\
calls = []

def get_value():
    calls.append('called')
    return [1, 2, 3]

a = b = c = get_value()
assert calls == ['called']  # Only one call
assert a is b is c  # All aliases of the same object
assert a == [1, 2, 3]

# Mutating one affects all (same object)
a.append(4)
assert b == [1, 2, 3, 4]
assert c == [1, 2, 3, 4]

# Independent evaluations produce distinct objects
calls.clear()
m = get_value()
n = get_value()
assert calls == ['called', 'called']  # Two calls
assert m is not n  # Different objects
m.append(99)
assert n == [1, 2, 3]  # n unaffected

# Chain with attribute and subscript targets
class Obj:
    pass
obj = Obj()
d = {'k': None}
obj.x = d['k'] = value = 42
assert obj.x == 42
assert d['k'] == 42
assert value == 42
# All refer to the same int (immutable, but same object due to one eval)
assert obj.x is d['k'] is value

# Longer chain
p = q = r = s = [1, 2]
assert p is q is r is s
p.append(3)
assert q == [1, 2, 3]
assert r == [1, 2, 3]
assert s == [1, 2, 3]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"codegen", "assignment", "eval-once"}),
    ),
    T(
        name="augmented_assignment_iadd_dispatch",
        category="codegen",
        description=(
            "`x += y` first tries `type(x).__iadd__`. If x is mutable "
            "and defines __iadd__, the operation is in-place and returns "
            "x itself. For immutable types (int, str, tuple), __iadd__ "
            "falls back to __add__, producing a new object. A custom "
            "type can define __iadd__ to do in-place mutation."
        ),
        source='''\
# list += uses __iadd__ (in-place extend)
lst = [1, 2, 3]
original_id = id(lst)
lst += [4, 5]
assert id(lst) == original_id  # Same object (in-place)
assert lst == [1, 2, 3, 4, 5]

# list += non-list iterable (still __iadd__, accepts any iterable)
lst = [1, 2]
lst += (3, 4)
assert lst == [1, 2, 3, 4]
lst += "ab"
assert lst == [1, 2, 3, 4, 'a', 'b']

# int += uses __add__ (immutable, new object)
n = 10
n += 5
assert n == 15

# Custom class with __iadd__ that returns self
class Acc:
    def __init__(self, v):
        self.v = v
    def __iadd__(self, other):
        self.v += other * 10
        return self
    def __add__(self, other):
        return Acc(self.v + other)

a = Acc(5)
a_id = id(a)
a += 2  # calls __iadd__
assert id(a) == a_id  # same object, mutated in place
assert a.v == 25  # 5 + 2*10

# Plain + creates new object via __add__
b = a + 3
assert b is not a
assert b.v == 28
assert a.v == 25  # unchanged

# Without __iadd__, += falls back to __add__ and rebinds
class NoIadd:
    def __init__(self, v):
        self.v = v
    def __add__(self, other):
        return NoIadd(self.v + other)

x = NoIadd(1)
x_id = id(x)
x += 10  # __add__ called, x rebound to new object
assert id(x) != x_id
assert x.v == 11
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         opt_state="deoptimized",
                         tags={"codegen", "iadd", "augmented", "dispatch"}),
    ),
    T(
        name="chained_comparison_middle_eval_once",
        category="codegen",
        description=(
            "Chained comparison `a < b < c` evaluates `b` exactly once, "
            "then compares it to both `a` and `c`. If `b` has side "
            "effects, those must fire only once."
        ),
        source='''\
calls = []

def b_value():
    calls.append('b')
    return 5

# True middle: b evaluated once
assert 1 < b_value() < 10
assert calls == ['b']
calls.clear()

# False middle: b evaluated once
assert not (1 < b_value() < 3)
assert calls == ['b']
calls.clear()

# Different comparison operators in same chain
assert 1 <= b_value() <= 10
assert calls == ['b']
calls.clear()

# Mixed: != in chain
assert 1 != b_value() != 100
assert calls == ['b']
calls.clear()

# Long chain
assert 0 < b_value() < 6 < 7 < 8
assert calls == ['b']

# Side effects in operands, verify ordering
log = []
def log_v(x):
    log.append(x)
    return x

# Each operand evaluated once, in order: a, b, c
log.clear()
result = log_v(1) < log_v(5) < log_v(10)
assert result is True
assert log == [1, 5, 10]

# Short-circuit: if first comparison is False, c is not evaluated
log.clear()
result = log_v(10) < log_v(5) < log_v(0)
assert result is False
assert log == [10, 5]  # c not evaluated

# Different operators
log.clear()
result = log_v(1) < log_v(5) <= log_v(5) < log_v(6)
assert result is True
assert log == [1, 5, 5, 6]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"codegen", "chained-comparison", "eval-once"}),
    ),
    T(
        name="for_loop_tuple_unpacking",
        category="codegen",
        description=(
            "A for loop unpacks each iteration's value into multiple "
            "names, including starred targets and nested tuples. The "
            "JIT must UNPACK each item before binding."
        ),
        source='''\
pairs = [(1, 'a'), (2, 'b'), (3, 'c')]
result = {}
for k, v in pairs:
    result[k] = v
assert result == {1: 'a', 2: 'b', 3: 'c'}

# Starred unpacking in loop
quads = [(1, 2, 3, 4), (5, 6, 7, 8)]
collected = []
for a, *middle, d in quads:
    collected.append((a, middle, d))
assert collected[0] == (1, [2, 3], 4)
assert collected[1] == (5, [6, 7], 8)

# Nested unpacking
nested = [((1, 2), 3), ((4, 5), 6)]
flat = []
for (a, b), c in nested:
    flat.append((a, b, c))
assert flat == [(1, 2, 3), (4, 5, 6)]

# Nested with star
nested_star = [((1, 2, 3), 4), ((5, 6, 7, 8), 9)]
flat_star = []
for (a, *rest), last in nested_star:
    flat_star.append((a, rest, last))
assert flat_star[0] == (1, [2, 3], 4)
assert flat_star[1] == (5, [6, 7, 8], 9)

# Dict iteration with unpacking
d = {('x', 1): 'a', ('y', 2): 'b'}
for (name, idx), val in d.items():
    assert isinstance(name, str)
    assert isinstance(idx, int)

# enumerate with nested unpacking
for i, (a, b) in enumerate([(1, 2), (3, 4)]):
    assert (i, a, b) in [(0, 1, 2), (1, 3, 4)]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="cold",
                         tags={"codegen", "unpack", "for-loop"}),
    ),
    T(
        name="star_expression_in_call",
        category="codegen",
        description=(
            "A function call uses `*args` to unpack an iterable as "
            "positional arguments. The unpacking can be combined with "
            "positional and keyword args, and multiple iterables can "
            "be unpacked in the same call."
        ),
        source='''\
def f(a, b, c):
    return a + b + c

args = [1, 2, 3]
assert f(*args) == 6

# Mix of positional and starred
def g(a, b, c, d):
    return a * 1000 + b * 100 + c * 10 + d

assert g(1, *[2, 3, 4]) == 1234
assert g(*[1, 2], 3, 4) == 1234
assert g(*[1, 2], *[3, 4]) == 1234

# Empty star
def h():
    return 'no args'
assert h(*[]) == 'no args'

# Variadic with star
def variadic(*args, **kw):
    return sum(args), sorted(kw.items())
assert variadic(1, *[2, 3]) == (6, [])
assert variadic(1, *[2], x=10) == (3, [('x', 10)])

# Star unpacks a generator
def sum_three(a, b, c):
    return a + b + c
assert sum_three(*iter([10, 20, 30])) == 60

# Star unpacks a string (chars become positional args)
def cat3(a, b, c):
    return a + b + c
assert cat3(*'xyz') == 'xyz'

# Multiple stars in same call
def five(a, b, c, d, e):
    return (a, b, c, d, e)
assert five(*[1, 2], *[3, 4], 5) == (1, 2, 3, 4, 5)

# Too many args raises
try:
    f(*[1, 2, 3, 4])
    assert False, "expected TypeError"
except TypeError:
    pass
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="direct", opt_state="cold",
                         tags={"codegen", "call", "star-unpack"}),
    ),
    T(
        name="double_star_in_call",
        category="codegen",
        description=(
            "A function call uses `**kwargs` to unpack a dict as "
            "keyword arguments. Multiple dicts can be unpacked in the "
            "same call, mixed with explicit keyword args."
        ),
        source='''\
def f(a, b, c):
    return f"{a}-{b}-{c}"

kwargs = {'a': 1, 'b': 2, 'c': 3}
assert f(**kwargs) == "1-2-3"

# Mix of positional and keyword
def g(a, b, c, d):
    return (a, b, c, d)
assert g(1, **{'b': 2, 'c': 3}, d=4) == (1, 2, 3, 4)

# Variadic with double star
def h(**kw):
    return sorted(kw.items())
d1 = {'a': 1, 'b': 2}
d2 = {'c': 3}
result = h(**d1, **d2, e=4)
assert result == [('a', 1), ('b', 2), ('c', 3), ('e', 4)]

# Empty double star
def k():
    return 'ok'
assert k(**{}) == 'ok'

# Double unpacking merge (PEP 448)
merged = {**d1, **d2, 'e': 4}
assert merged == {'a': 1, 'b': 2, 'c': 3, 'e': 4}

# Conflicting keys raise
def two(a):
    return a
try:
    two(a=1, **{'a': 2})
    assert False, "expected TypeError for multiple values"
except TypeError:
    pass

# Mixing * and **
def both(a, b, c):
    return (a, b, c)
assert both(*[1, 2], **{'c': 3}) == (1, 2, 3)
assert both(1, *[2], **{'c': 3}) == (1, 2, 3)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="direct", opt_state="cold",
                         tags={"codegen", "call", "kwargs", "double-star"}),
    ),
    T(
        name="fstring_complex_expressions",
        category="codegen",
        description=(
            "f-strings embed arbitrary expressions, including method "
            "calls, indexing, dict access, nested f-strings, ternaries, "
            "and format specs. The JIT must lower each embedded "
            "expression to its own evaluation, then format the result."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"codegen", "fstring", "format"}),
    ),
    T(
        name="string_percent_format_operator",
        category="codegen",
        description=(
            "The % operator on strings performs printf-style formatting. "
            "The JIT must support %d/%s/%f/%x/%o/%r format specifiers, "
            "named-argument formatting via a dict, and width/precision "
            "modifiers."
        ),
        source='''\
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
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"codegen", "percent", "format"}),
    ),
    T(
        name="slice_with_positive_negative_step",
        category="codegen",
        description=(
            "Slicing supports start, stop, and step, where step may be "
            "negative (reverse). The JIT must handle the empty-range "
            "edge cases and the boundary conditions for negative step."
        ),
        source='''\
lst = list(range(10))  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Positive step
assert lst[::2] == [0, 2, 4, 6, 8]
assert lst[1::2] == [1, 3, 5, 7, 9]
assert lst[::3] == [0, 3, 6, 9]
assert lst[1:8:2] == [1, 3, 5, 7]

# Negative step (reverse)
assert lst[::-1] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
assert lst[::-2] == [9, 7, 5, 3, 1]
assert lst[::-3] == [9, 6, 3, 0]
assert lst[8:0:-1] == [8, 7, 6, 5, 4, 3, 2, 1]
assert lst[8:0:-2] == [8, 6, 4, 2]
assert lst[-1::-1] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
assert lst[-1:-5:-1] == [9, 8, 7, 6]

# Empty slices
assert lst[5:5] == []
assert lst[5:2] == []  # positive step, start > stop
assert lst[2:5:-1] == []  # negative step, start < stop
assert lst[10:0] == []  # start >= len

# Out-of-bounds are clamped
assert lst[5:100] == [5, 6, 7, 8, 9]
assert lst[-100:3] == [0, 1, 2]
assert lst[100:200] == []

# String slicing
s = "abcdefg"
assert s[::-1] == "gfedcba"
assert s[::2] == "aceg"
assert s[1:-1:2] == "bdf"
assert s[6:0:-2] == "gec"  # indices 6,4,2 (stop=0 is excluded)

# Tuple slicing
t = (10, 20, 30, 40, 50)
assert t[::-1] == (50, 40, 30, 20, 10)
assert t[::2] == (10, 30, 50)
assert t[1:4:2] == (20, 40)

# Step of 1 (most common)
assert lst[2:5:1] == [2, 3, 4]
assert lst[::1] == lst

# Assignment to extended slice (must match length)
lst2 = [0] * 10
lst2[2:8:2] = [10, 20, 30]
assert lst2 == [0, 0, 10, 0, 20, 0, 30, 0, 0, 0]

# Negative step assignment
lst3 = list(range(5))
lst3[::-1] = list(range(5))
assert lst3 == [4, 3, 2, 1, 0]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"codegen", "slice", "step", "reverse"}),
    ),
    T(
        name="multiple_return_values_packed",
        category="codegen",
        description=(
            "`return a, b, c` builds a tuple and returns it. The caller "
            "can then unpack or treat it as a single value. The JIT "
            "must build the tuple at the return site, not elide it even "
            "if the caller immediately unpacks."
        ),
        source='''\
def three():
    return 1, 2, 3

r = three()
assert isinstance(r, tuple)
assert r == (1, 2, 3)
assert len(r) == 3

# Unpacking at call site
a, b, c = three()
assert (a, b, c) == (1, 2, 3)

# Mixed return types
def mixed():
    return 1, "hello", [1, 2], {'k': 'v'}
n, s, lst, d = mixed()
assert n == 1
assert s == "hello"
assert lst == [1, 2]
assert d == {'k': 'v'}

# Single-element tuple (trailing comma)
def single():
    return 42,
assert single() == (42,)
assert isinstance(single(), tuple)

# Empty return (None)
def nothing():
    return
assert nothing() is None

# Single non-tuple value
def just_int():
    return 42
assert just_int() == 42
assert not isinstance(just_int(), tuple)

# Return a generator expression (not a tuple)
def gen_return():
    return (x * 2 for x in range(3))
g = gen_return()
assert list(g) == [0, 2, 4]
assert isinstance(g, type((x for x in [])))  # generator type

# Star unpacking in return
def variadic_return(*args):
    return args
assert variadic_return(1, 2, 3) == (1, 2, 3)
assert isinstance(variadic_return(), tuple)
assert variadic_return() == ()

# Conditional return (single ternary expression with nested parens)
def classify(n):
    return ('neg', n) if n < 0 else (('zero', n) if n == 0 else ('pos', n))
assert classify(-5) == ('neg', -5)
assert classify(0) == ('zero', 0)
assert classify(7) == ('pos', 7)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"codegen", "return", "tuple-pack"}),
    ),
    T(
        name="mutable_default_eval_at_def_time",
        category="codegen",
        description=(
            "Default argument expressions are evaluated ONCE, at "
            "function definition time, not on each call. The same "
            "object is reused across calls. This is the classic "
            "gotcha: `def f(x=[])` accumulates state across calls."
        ),
        source='''\
# The default list is built once and shared
def f(x=[]):
    x.append(1)
    return x

assert f() == [1]
assert f() == [1, 1]  # same list
assert f() == [1, 1, 1]

# The default object is the same across all calls
default_id = id(f.__defaults__[0])
f()
assert id(f.__defaults__[0]) == default_id

# Same gotcha with dict default
def g(d={}):
    d['count'] = d.get('count', 0) + 1
    return d
assert g() == {'count': 1}
assert g() == {'count': 2}
assert g() == {'count': 3}

# Same gotcha with set default
def h(s=set()):
    s.add(len(s))
    return s
result1 = h()
result2 = h()
result3 = h()
assert len(result3) == 3
assert result1 is result2 is result3

# Sentinel pattern: use None to get a fresh default per call
def safe(x=None):
    if x is None:
        x = []
    x.append(1)
    return x
assert safe() == [1]
assert safe() == [1]  # new list each call
assert safe() is not safe()

# Mutable default evaluated at def time, not call time
counter = [0]
def make():
    counter[0] += 1
    return counter[0]
def k(x=make()):
    return x
# make() was called once, at def time
assert k() == 1
assert k() == 1  # default unchanged
# counter was incremented once
assert counter[0] == 1
# Define another function -> make() called again
def m(x=make()):
    return x
assert m() == 2  # counter[0] is now 2
assert counter[0] == 2
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="direct", opt_state="deoptimized",
                         tags={"codegen", "default-arg", "shared-default"}),
    ),
]
