"""Register allocation stress tests.

Register allocation assigns program values (locals, temporaries, and
 spilled values) to a small pool of physical registers. When live
 ranges overlap and pressure exceeds the register file, the allocator
 must spill some values to the stack and reload them around their
 uses. The tests below target the classic failure modes: excessive
 live variables, spill at call sites, live range splitting across loop
 back-edges, long-lived values that span the entire function, values
 live across exception handlers, many temporaries in a single
 expression, overlapping lifetimes in nested loops, register pressure
 from inlined callees, phi nodes at loop headers, and redefinition
 that invalidates a previous assignment.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="many_live_variables_exceed_registers",
        category="register_alloc",
        description=(
            "Twenty-four variables are all simultaneously live across "
            "a single use point. This far exceeds the available "
            "physical registers on any mainstream architecture, so "
            "the allocator must spill most of them to the stack. A "
            "buggy allocator that didn't track live ranges would "
            "clobber values or read uninitialized memory."
        ),
        source='''\
def work():
    a0 = 0
    a1 = 1
    a2 = 2
    a3 = 3
    a4 = 4
    a5 = 5
    a6 = 6
    a7 = 7
    a8 = 8
    a9 = 9
    a10 = 10
    a11 = 11
    a12 = 12
    a13 = 13
    a14 = 14
    a15 = 15
    a16 = 16
    a17 = 17
    a18 = 18
    a19 = 19
    a20 = 20
    a21 = 21
    a22 = 22
    a23 = 23
    # All 24 variables are live here; the allocator must spill most
    # of them and reload each at the point of use.
    return (a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9 +
            a10 + a11 + a12 + a13 + a14 + a15 + a16 + a17 +
            a18 + a19 + a20 + a21 + a22 + a23)

expected = sum(range(24))
assert work() == expected
assert work() == 276
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"register-alloc", "spill", "live-range",
                               "pressure"}),
    ),
    T(
        name="spill_at_call_site",
        category="register_alloc",
        description=(
            "Several variables are live across a call to a non-trivial "
            "callee. The calling convention may clobber caller-saved "
            "registers, so the allocator must either spill the live "
            "values to the stack or move them to callee-saved "
            "registers around the call. A buggy allocator that didn't "
            "model call clobbers would lose values across the call."
        ),
        source='''\
def helper(x):
    # A non-trivial callee: enough work that the JIT cannot elide it.
    s = 0
    for i in range(x):
        s += i
    return s

def work():
    a = 10
    b = 20
    c = 30
    d = 40
    # All four are live across the call to helper.
    result = helper(5)
    return a + b + c + d + result

# helper(5) = 0 + 1 + 2 + 3 + 4 = 10
assert work() == 10 + 20 + 30 + 40 + 10
assert work() == 110
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line",
                         call_behavior="direct", opt_state="hot",
                         tags={"register-alloc", "spill", "call-site",
                               "caller-saved"}),
    ),
    T(
        name="live_range_split_at_back_edge",
        category="register_alloc",
        description=(
            "A loop-carried variable is live across the loop back-edge. "
            "The allocator may choose to split its live range at the "
            "back-edge (spill at the end of the body, reload at the "
            "top). A buggy splitter that didn't account for the back-"
            "edge would either lose the value between iterations or "
            "keep it pinned in a register, blocking other allocations."
        ),
        source='''\
def work(n):
    total = 0
    i = 0
    while i < n:
        # total and i are both loop-carried; both live across the
        # back-edge.
        total += i
        i += 1
    return total

assert work(100) == sum(range(100))
assert work(0) == 0
assert work(1) == 0
assert work(10) == 45
assert work(1000) == 499500
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"register-alloc", "live-range-splitting",
                               "back-edge", "loop-carried"}),
    ),
    T(
        name="long_lived_used_at_start_and_end",
        category="register_alloc",
        description=(
            "A variable is defined at the start of the function, "
            "not used for a long stretch in the middle, then used "
            "again at the very end. Its live range spans the entire "
            "function. A naive allocator would pin it to a register "
            "for the whole function, wasting the register; a good "
            "allocator would split the range and spill it during the "
            "middle. Either way, the value must survive."
        ),
        source='''\
def work():
    x = 42  # used at the start (definition) and the end (use)
    # Lots of unrelated computation in between that does not touch x.
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    mid = a + b + c + d + e + f + g + h
    p = mid * 2
    q = p + 1
    r = q * 3
    s = r - 7
    # x is finally used again here; its value must still be 42.
    return x + s

# Compute the expected value by hand to avoid relying on the JIT.
mid = 1 + 2 + 3 + 4 + 5 + 6 + 7 + 8        # = 36
p = mid * 2                                # = 72
q = p + 1                                  # = 73
r = q * 3                                  # = 219
s = r - 7                                  # = 212
expected = 42 + s                          # = 254
assert work() == expected
assert work() == 254
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"register-alloc", "live-range",
                               "spill", "long-lived"}),
    ),
    T(
        name="live_across_exception_handler",
        category="register_alloc",
        description=(
            "Variables defined before a try block are used inside the "
            "corresponding except handler. The allocator must keep "
            "them live across the exception edge, which is hard to "
            "model because the edge is rarely taken. A buggy "
            "allocator that didn't account for exception edges would "
            "spill them at the try boundary and lose them when the "
            "exception fires."
        ),
        source='''\
def work(x):
    a = 10
    b = 20
    try:
        if x < 0:
            raise ValueError("negative")
        c = a + b + x
        return c
    except ValueError:
        # a and b must still be live here.
        return a + b

assert work(5) == 35      # 10 + 20 + 5
assert work(-1) == 30     # exception path: 10 + 20
assert work(0) == 30      # 10 + 20 + 0
assert work(100) == 130   # 10 + 20 + 100
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="hot",
                         tags={"register-alloc", "exception-edge",
                               "spill", "handler"}),
    ),
    T(
        name="many_temporaries_complex_expr",
        category="register_alloc",
        description=(
            "A single expression introduces many simultaneously-live "
            "temporaries. The allocator must hold all of them at "
            "once (or spill and reload) to evaluate the expression. "
            "A buggy allocator that undercounted temporaries would "
            "reuse a register too early and corrupt the result."
        ),
        source='''\
def work(a, b, c, d, e, f, g, h):
    # Many intermediate temporaries; all are live until the final sum.
    t1 = a + b
    t2 = c + d
    t3 = e + f
    t4 = g + h
    t5 = t1 * t2
    t6 = t3 * t4
    t7 = t5 - t6
    t8 = a * c
    t9 = b * d
    t10 = e * g
    t11 = f * h
    t12 = t8 + t9
    t13 = t10 + t11
    t14 = t12 - t13
    return t7 + t14

# Sanity-check with positive inputs.
a, b, c, d, e, f, g, h = 1, 2, 3, 4, 5, 6, 7, 8
expected = (((a + b) * (c + d) - (e + f) * (g + h)) +
            ((a * c + b * d) - (e * g + f * h)))
assert work(1, 2, 3, 4, 5, 6, 7, 8) == expected

# And with negatives to catch sign-handling bugs.
A, B, C, D, E, F, G, H = -1, -2, -3, -4, -5, -6, -7, -8
expected_neg = (((A + B) * (C + D) - (E + F) * (G + H)) +
                ((A * C + B * D) - (E * G + F * H)))
assert work(-1, -2, -3, -4, -5, -6, -7, -8) == expected_neg

# And zeros.
assert work(0, 0, 0, 0, 0, 0, 0, 0) == 0
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"register-alloc", "temporaries",
                               "pressure", "expression"}),
    ),
    T(
        name="overlapping_lifetimes_nested_loops",
        category="register_alloc",
        description=(
            "Two variables with overlapping lifetimes live across an "
            "outer and an inner loop. The inner variable dies at the "
            "end of each inner iteration but the outer variable lives "
            "across the entire inner loop. A buggy allocator that "
            "didn't model nested scopes correctly would either free "
            "the outer variable too early or hold the inner variable "
            "for too long, wasting registers."
        ),
        source='''\
def work(n, m):
    outer_sum = 0
    for i in range(n):
        # inner_acc's lifetime spans the entire inner loop, but
        # dies before the next outer iteration.
        inner_acc = 0
        for j in range(m):
            # outer_sum, inner_acc, i, j all live here.
            inner_acc += i * j
        outer_sum += inner_acc
    return outer_sum

assert work(5, 5) == sum(i * j for i in range(5) for j in range(5))
assert work(3, 4) == sum(i * j for i in range(3) for j in range(4))
assert work(0, 5) == 0   # outer loop never runs
assert work(5, 0) == 0   # inner loop never runs
assert work(10, 10) == sum(i * j for i in range(10) for j in range(10))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="nested_loop", opt_state="hot",
                         tags={"register-alloc", "nested-loop",
                               "overlapping-lifetimes", "scope"}),
    ),
    T(
        name="register_pressure_from_inlined",
        category="register_alloc",
        description=(
            "A function is called multiple times in close succession. "
            "If the JIT inlines each call, the combined locals of all "
            "the inlined copies create high register pressure. A buggy "
            "allocator that didn't account for the inlined frames' "
            "locals would either fail to inline (missed optimization) "
            "or spill incorrectly and corrupt values."
        ),
        source='''\
def inner(a, b, c, d, e):
    # Five parameters + two locals + return value.
    s = a + b
    t = c + d
    u = s + t
    return u + e

def outer(x):
    # Three inlined calls; their locals all live simultaneously.
    p = inner(x, x + 1, x + 2, x + 3, x + 4)
    q = inner(x * 2, x * 2 + 1, x * 2 + 2, x * 2 + 3, x * 2 + 4)
    r = inner(x * 3, x * 3 + 1, x * 3 + 2, x * 3 + 3, x * 3 + 4)
    return p + q + r

# Reference implementation (no inlining) for cross-checking.
def ref_inner(a, b, c, d, e):
    return ((a + b) + (c + d)) + e

def ref_outer(x):
    return (ref_inner(x, x + 1, x + 2, x + 3, x + 4) +
            ref_inner(x * 2, x * 2 + 1, x * 2 + 2, x * 2 + 3, x * 2 + 4) +
            ref_inner(x * 3, x * 3 + 1, x * 3 + 2, x * 3 + 3, x * 3 + 4))

assert outer(10) == ref_outer(10)
assert outer(0) == ref_outer(0)
assert outer(-5) == ref_outer(-5)
assert outer(100) == ref_outer(100)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line",
                         call_behavior="direct", opt_state="very_hot",
                         tags={"register-alloc", "inlining", "pressure",
                               "caller-saved"}),
    ),
    T(
        name="phi_nodes_at_loop_header",
        category="register_alloc",
        description=(
            "A variable takes different values depending on which "
            "predecessor entered the loop header (the preheader "
            "initializes it; the back-edge updates it). The SSA form "
            "represents this with a phi node. The allocator must "
            "assign a register (or spill slot) that's consistent "
            "across both predecessors. A buggy allocator that didn't "
            "model phis would read garbage on the second iteration."
        ),
        source='''\
def work(start, n):
    # `total` is a phi at the loop header:
    #   - from preheader: total = start
    #   - from back-edge: total = total + i
    total = start
    for i in range(n):
        total += i
    return total

assert work(0, 10) == sum(range(10))
assert work(100, 10) == 100 + sum(range(10))
assert work(0, 0) == 0          # loop never runs; phi picks the preheader value
assert work(-5, 5) == -5 + sum(range(5))
assert work(1000, 100) == 1000 + sum(range(100))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"register-alloc", "phi", "loop-header",
                               "ssa"}),
    ),
    T(
        name="redefined_mid_function",
        category="register_alloc",
        description=(
            "A variable is redefined in the middle of the function. "
            "In SSA form this is two distinct definitions; the "
            "allocator must treat them as independent live ranges "
            "and may assign them to different registers. A buggy "
            "allocator that reused the same register without "
            "checking liveness would corrupt earlier values that "
            "are still in use."
        ),
        source='''\
def work(x):
    a = x * 2          # def 1: a = 2x
    b = a + 1          # b = 2x + 1 (uses def 1 of a)
    a = b * 3          # def 2: a = 6x + 3 (redefinition; def 1 dies here)
    c = a - 1          # c = 6x + 2 (uses def 2 of a)
    a = c + 10         # def 3: a = 6x + 12 (redefinition; def 2 dies here)
    return a + b + c   # (6x + 12) + (2x + 1) + (6x + 2) = 14x + 15

# Verify across a range of inputs to catch subtle bugs.
for x in [0, 1, 2, 5, 10, -3, 100, -100]:
    expected = 14 * x + 15
    got = work(x)
    assert got == expected, f"work({x}) = {got}, expected {expected}"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"register-alloc", "redefinition",
                               "ssa", "live-range"}),
    ),
]
