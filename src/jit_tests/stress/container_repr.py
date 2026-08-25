"""Container representation stress tests.

These tests target the JIT's container representations: how lists,
dicts, sets, and tuples are stored in memory and how those internal
layouts change as the container grows, shrinks, or changes the type
of its elements. A naive JIT may specialize a list as "list of int"
and miss the transition to a heterogeneous list, or it may cache a
dict's hash table size and break when the dict rehashes.

Failure modes covered:
- List growth past internal array capacity (reallocation)
- Dict growth past load factor (rehash)
- Set growth (hash table resize)
- List element type change (int -> str -> float -> None -> bool)
- Dict key type change (int -> str -> tuple -> float)
- Tuple unpacking with starred targets and nesting
- Large list comprehension (multiple internal resizes)
- Dict comprehension with deliberate hash collisions
- Set algebra across representations (set, frozenset, mixed)
- Slice assignment that grows or shrinks the list
- Dict update from a generator (iteration during mutation)
- List extend with an alias of itself (in-place growth)
- Dict popitem loop (table shrinkage)
- List -> tuple conversion (different internal representation)
- Frozenset from a set (immutability + hashing)
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="empty_list_grows_to_thousand",
        category="container_repr",
        description=(
            "A list starts empty and grows by one element per iteration "
            "until it holds 1000 ints. CPython's list internally "
            "reallocates the underlying PyObject* array at ~3/2 capacity "
            "steps. The JIT must update any cached length/capacity pair "
            "after each reallocation."
        ),
        source='''\
lst = []
for i in range(1000):
    lst.append(i)

assert len(lst) == 1000
assert lst[0] == 0
assert lst[-1] == 999
assert lst[500] == 500
assert lst == list(range(1000))

# Spot-check after a slice
assert lst[100:105] == [100, 101, 102, 103, 104]

# Insert at front (forces repeated shifts)
lst.insert(0, -1)
assert lst[0] == -1
assert lst[1] == 0
assert len(lst) == 1001

# Pop from end
last = lst.pop()
assert last == 999
assert len(lst) == 1000
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"container", "list", "resize"}),
    ),
    T(
        name="empty_dict_grows_rehash",
        category="container_repr",
        description=(
            "A dict starts empty and grows to 1000 entries, triggering "
            "multiple hash table resizes (CPython resizes when load > 2/3 "
            "capacity). The JIT must keep all key/value pairs intact "
            "across each rehash, including through deliberate deletion "
            "and re-insertion."
        ),
        source='''\
d = {}
for i in range(1000):
    d[i] = i * 2

assert len(d) == 1000
for i in range(1000):
    assert d[i] == i * 2

# All keys present after multiple rehashes
assert all(d[i] == i * 2 for i in range(1000))
assert set(d.keys()) == set(range(1000))

# Delete half, forcing shrink
for i in range(0, 1000, 2):
    del d[i]
assert len(d) == 500
assert all(d[i] == i * 2 for i in range(1, 1000, 2))

# Re-add the deleted keys
for i in range(0, 1000, 2):
    d[i] = i * 2
assert len(d) == 1000
assert all(d[i] == i * 2 for i in range(1000))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"container", "dict", "rehash", "resize"}),
    ),
    T(
        name="empty_set_grows_resize",
        category="container_repr",
        description=(
            "A set starts empty and grows to 1000 elements, triggering "
            "multiple hash table resizes. Duplicates added during growth "
            "must be deduplicated, and lookups must succeed after every "
            "resize."
        ),
        source='''\
s = set()
for i in range(1000):
    s.add(i)

assert len(s) == 1000
for i in range(1000):
    assert i in s

# Re-add the same elements; size must not change
for i in range(1000):
    s.add(i)
assert len(s) == 1000

# Remove and re-add
for i in range(0, 500):
    s.discard(i)
assert len(s) == 500
assert 1 not in s
assert 999 in s

for i in range(0, 500):
    s.add(i)
assert len(s) == 1000
assert 1 in s
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"container", "set", "resize"}),
    ),
    T(
        name="list_int_then_str_type_change",
        category="container_repr",
        description=(
            "A list of ints is built up; then a string is appended. The "
            "element type spec changes from 'list[int]' to "
            "'list[object]'. The JIT must invalidate any specialized "
            "fast path that assumed homogeneous int elements."
        ),
        source='''\
lst = [1, 2, 3]
for i in range(4, 100):
    lst.append(i)

# Now append a string (type spec breaks)
lst.append("hello")
# After [1,2,3] + range(4,100) (96 ints) + "hello" = 100 elements
assert len(lst) == 100
assert lst[:5] == [1, 2, 3, 4, 5]
assert lst[-1] == "hello"
assert lst[99] == "hello"

# Append more types
lst.extend([10.5, None, True, (1, 2)])
assert lst[-4:] == [10.5, None, True, (1, 2)]
assert lst[-1] == (1, 2)
assert lst[-3] is None

# Spot-check that ints are still intact (lst[i] == i+1 for i in 0..98)
assert lst[50] == 51
assert lst[0] == 1

# Convert to a typed structure (sum only works on numerics; bool excluded
# explicitly because isinstance(True, int) is True)
numeric_sum = sum(x for x in lst if isinstance(x, (int, float)) and not isinstance(x, bool))
# Ints 1..99 plus the float 10.5; True is bool so excluded
assert numeric_sum == sum(range(1, 100)) + 10.5
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"container", "list", "type-change"}),
    ),
    T(
        name="dict_int_keys_then_str",
        category="container_repr",
        description=(
            "A dict with all-int keys gets a string key, then a tuple "
            "key, then a float key. The key type spec changes; the dict "
            "may switch from a compact-keys representation to a "
            "general-keys representation. All original entries must "
            "remain accessible."
        ),
        source='''\
d = {}
for i in range(100):
    d[i] = f"int_{i}"

assert d[0] == "int_0"
assert d[99] == "int_99"

# Add a string key (changes key type spec)
d["hello"] = "world"
assert d["hello"] == "world"

# Add a tuple key
d[(1, 2)] = "tuple_key"
assert d[(1, 2)] == "tuple_key"

# Add a float key (different hash type)
d[3.14] = "pi"
assert d[3.14] == "pi"
# 3 (int) and 3.14 (float) hash differently and coexist
assert d[3] == "int_3"

# All original int keys still present
assert all(d.get(i) == f"int_{i}" for i in range(100))

# Length reflects all keys
assert len(d) == 100 + 3

# Delete a heterogeneous mix
del d[0]
del d["hello"]
del d[(1, 2)]
assert len(d) == 100
assert 0 not in d
assert "hello" not in d
assert (1, 2) not in d
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"container", "dict", "type-change", "keys"}),
    ),
    T(
        name="tuple_starred_unpack",
        category="container_repr",
        description=(
            "Tuples of varying sizes are unpacked with starred targets, "
            "including nested unpacking. The JIT must support the full "
            "UNPACK_EX bytecode (PEP 3132) including the empty-middle "
            "and all-in-middle edge cases."
        ),
        source='''\
t = (1, 2, 3, 4, 5)
a, b, *c, d = t
assert a == 1
assert b == 2
assert c == [3, 4]
assert d == 5

# Empty middle
a, *b, c = (1, 2)
assert a == 1
assert b == []
assert c == 2

# All in middle
*a, = (1, 2, 3)
assert a == [1, 2, 3]

# Single trailing star
a, b, *c = (1, 2)
assert (a, b, c) == (1, 2, [])

# Nested tuple unpacking
t2 = ((1, 2), (3, 4), (5, 6))
(a, b), (c, d), (e, f) = t2
assert (a, b, c, d, e, f) == (1, 2, 3, 4, 5, 6)

# Nested with star
t3 = ((1, 2, 3), (4, 5, 6, 7))
(a, *b), (c, *d) = t3
assert a == 1
assert b == [2, 3]
assert c == 4
assert d == [5, 6, 7]

# Swap via unpacking
x, y = 10, 20
x, y = y, x
assert (x, y) == (20, 10)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"container", "tuple", "unpack", "UNPACK_EX"}),
    ),
    T(
        name="large_list_comprehension_resizes",
        category="container_repr",
        description=(
            "A list comprehension builds a 10000-element list. CPython's "
            "BUILD_LIST_FROM_OP performs several internal reallocations "
            "during the comprehension. A nested comprehension builds a "
            "matrix; both must produce correct contents after all "
            "resizes."
        ),
        source='''\
lst = [x * x for x in range(10000)]
assert len(lst) == 10000
assert lst[0] == 0
assert lst[9999] == 9999 ** 2
assert lst[5000] == 25000000
assert sum(lst) == sum(x * x for x in range(10000))

# Nested comprehension -> matrix
matrix = [[i * j for j in range(10)] for i in range(10)]
assert len(matrix) == 10
assert all(len(row) == 10 for row in matrix)
assert matrix[3][4] == 12
assert matrix[5][5] == 25
assert matrix[0][0] == 0
assert matrix[9][9] == 81

# Condition in comprehension
evens = [x for x in range(100) if x % 2 == 0]
assert len(evens) == 50
assert evens[0] == 0
assert evens[-1] == 98

# Multiple for clauses
flattened = [i * 10 + j for i in range(3) for j in range(3)]
assert flattened == [0, 1, 2, 10, 11, 12, 20, 21, 22]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="nested_loop", opt_state="hot",
                         tags={"container", "comprehension", "list", "resize"}),
    ),
    T(
        name="dict_comprehension_with_collisions",
        category="container_repr",
        description=(
            "A dict comprehension builds a dict with 100 keys whose "
            "__hash__ all return 0, forcing a long collision chain. "
            "Lookups must use __eq__ to disambiguate. The JIT cannot "
            "rely on hash equality as a proxy for key equality."
        ),
        source='''\
class CollidingHash:
    __slots__ = ('val',)
    def __init__(self, val):
        self.val = val
    def __hash__(self):
        return 0  # all collide
    def __eq__(self, other):
        return isinstance(other, CollidingHash) and self.val == other.val
    def __repr__(self):
        return f"CH({self.val})"

keys = [CollidingHash(i) for i in range(100)]
d = {k: k.val * 2 for k in keys}
assert len(d) == 100

# Every key looks up correctly despite collisions
for k in keys:
    assert d[k] == k.val * 2

# Look up by an equivalent key (different object, same val)
specific = CollidingHash(50)
assert d[specific] == 100

# Delete a key by an equivalent object
del d[CollidingHash(50)]
assert len(d) == 99
try:
    _ = d[specific]
    assert False, "expected KeyError"
except KeyError:
    pass

# Other keys still present
for k in keys:
    if k.val == 50:
        continue
    assert d[k] == k.val * 2
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"container", "dict", "collision", "hash"}),
    ),
    T(
        name="set_algebra_across_reprs",
        category="container_repr",
        description=(
            "Set operations (difference, intersection, symmetric "
            "difference, union) between sets and frozensets of varying "
            "sizes. The JIT must handle the different internal "
            "representations and the from-set / from-frozenset source "
            "types."
        ),
        source='''\
s1 = set(range(100))
s2 = set(range(50, 150))
s3 = set(range(0, 200, 2))  # even numbers

# Difference
diff = s1 - s2
assert diff == set(range(50))

# Intersection
inter = s1 & s2
assert inter == set(range(50, 100))

# Symmetric difference
sym = s1 ^ s2
assert sym == set(range(50)) | set(range(100, 150))

# Union
uni = s1 | s3
assert uni == set(range(0, 100)) | set(range(0, 200, 2))

# Mixed set / frozenset
fs = frozenset(range(75, 125))
inter2 = s1 & fs
assert inter2 == set(range(75, 100))
diff2 = fs - s1
assert diff2 == set(range(100, 125))

# In-place operations
base = set(range(20))
base &= set(range(10, 30))
assert base == set(range(10, 20))
base |= set(range(30, 40))
assert base == set(range(10, 20)) | set(range(30, 40))
base -= set(range(15, 35))
assert base == {10, 11, 12, 13, 14, 35, 36, 37, 38, 39}
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"container", "set", "frozenset", "algebra"}),
    ),
    T(
        name="list_slice_assignment_length_change",
        category="container_repr",
        description=(
            "Slice assignment replaces a sublist with another of "
            "different length, growing or shrinking the list. Extended "
            "slice assignment (with step) requires the replacement to "
            "have exactly the same length as the slice."
        ),
        source='''\
lst = [1, 2, 3, 4, 5]

# Replace middle with more elements (grow)
lst[1:4] = [10, 20, 30, 40, 50]
assert lst == [1, 10, 20, 30, 40, 50, 5]

# Replace with fewer (shrink)
lst[1:6] = [99]
assert lst == [1, 99, 5]

# Replace with empty (delete middle)
lst[:] = [1, 2, 3, 4, 5]
lst[1:4] = []
assert lst == [1, 5]

# Replace whole list
lst[:] = [10, 20, 30]
assert lst == [10, 20, 30]

# Extended slice (step) - must match length exactly
lst = [0] * 10
lst[2:8:2] = [10, 20, 30]
assert lst == [0, 0, 10, 0, 20, 0, 30, 0, 0, 0]

# Extended slice with wrong length raises
try:
    lst[::2] = [1, 2, 3, 4]  # 5 positions, 4 values
    assert False, "expected ValueError"
except ValueError:
    pass

# Negative-step slice assignment
lst = [1, 2, 3, 4, 5]
lst[::-1] = [10, 20, 30, 40, 50]
assert lst == [50, 40, 30, 20, 10]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"container", "list", "slice", "mutation"}),
    ),
    T(
        name="dict_update_from_generator",
        category="container_repr",
        description=(
            "Dict.update() is called with a generator that yields "
            "(key, value) tuples. The dict must consume the generator "
            "lazily and insert each entry, including overriding existing "
            "keys."
        ),
        source='''\
d = {i: i * 10 for i in range(50)}

# Update with a generator of new keys
d.update((i, i * 100) for i in range(50, 100))
assert len(d) == 100
for i in range(100):
    expected = i * 10 if i < 50 else i * 100
    assert d[i] == expected

# Update with a generator that overrides existing keys
d.update((i, -1) for i in range(0, 100, 10))
for i in range(0, 100, 10):
    assert d[i] == -1
# Non-overridden keys intact
for i in range(1, 10):
    assert d[i] == i * 10

# Update with another dict
d.update({0: 'overwritten', 1: 'also'})
assert d[0] == 'overwritten'
assert d[1] == 'also'

# Update with a list of pairs
d.update([(200, 'list_pair'), (201, 'list_pair2')])
assert d[200] == 'list_pair'
assert d[201] == 'list_pair2'
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"container", "dict", "update", "generator"}),
    ),
    T(
        name="list_extend_self_alias",
        category="container_repr",
        description=(
            "List.extend() is called with the list itself as the "
            "argument. CPython's extend handles aliasing correctly by "
            "first materializing the iterable. The JIT must not "
            "double-iterate or read freed memory."
        ),
        source='''\
lst = [1, 2, 3]
lst.extend(lst)
assert lst == [1, 2, 3, 1, 2, 3]

# Extend with a slice of itself
lst2 = [10, 20, 30]
lst2.extend(lst2[:2])
assert lst2 == [10, 20, 30, 10, 20]

# += is in-place extend
lst3 = [1, 2, 3]
lst3 += lst3
assert lst3 == [1, 2, 3, 1, 2, 3]

# Extend with an iterator over a SNAPSHOT of itself (slice makes a copy)
lst4 = [1, 2, 3]
lst4.extend(iter(lst4[:]))
assert lst4 == [1, 2, 3, 1, 2, 3]

# Extend with a tuple (immutable copy, safe under aliasing)
lst6 = [1, 2, 3]
lst6.extend(tuple(lst6))
assert lst6 == [1, 2, 3, 1, 2, 3]

# Extend with a reversed view of itself (reversed returns a view but
# reads through the live sequence; reversing a 3-element list is finite)
lst7 = [1, 2, 3]
lst7.extend(reversed(lst7))
assert lst7 == [1, 2, 3, 3, 2, 1]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"container", "list", "extend", "aliasing"}),
    ),
    T(
        name="dict_popitem_loop_shrinks",
        category="container_repr",
        description=(
            "A loop calls dict.popitem() until the dict is empty. The "
            "internal hash table must shrink (or at least mark entries "
            "dummy) without losing any un-popped entries. popitem on "
            "an empty dict must raise KeyError."
        ),
        source='''\
d = {i: i * 2 for i in range(100)}
items = []
while d:
    k, v = d.popitem()
    items.append((k, v))

assert len(items) == 100
assert len(d) == 0

# All items accounted for
assert sorted(items) == [(i, i * 2) for i in range(100)]

# popitem on empty raises KeyError
try:
    d.popitem()
    assert False, "expected KeyError"
except KeyError:
    pass

# Rebuild and verify interleaved popitem + get still works.
# In CPython 3.7+, dict.popitem removes the LAST-inserted entry, so after
# 25 pops from a 0..49 dict, the remaining keys are 0..24.
d = {i: i * 3 for i in range(50)}
popped_count = 0
while d:
    if popped_count == 25:
        # Mid-shrink: verify all remaining entries are still present
        remaining = sorted(d.items())
        assert remaining == [(i, i * 3) for i in range(0, 25)]
    k, v = d.popitem()
    popped_count += 1
assert popped_count == 50
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"container", "dict", "popitem", "shrink"}),
    ),
    T(
        name="list_to_tuple_conversion",
        category="container_repr",
        description=(
            "A list is converted to a tuple via tuple(lst). The two "
            "containers have different internal representations (list has "
            "a mutable PyObject* array with capacity; tuple has an "
            "immutable array of fixed size). Mutating the source list "
            "after conversion must not affect the tuple."
        ),
        source='''\
lst = [1, 2, 3, 4, 5]
t = tuple(lst)
assert t == (1, 2, 3, 4, 5)
assert isinstance(t, tuple)
assert isinstance(lst, list)

# Mutate the list; tuple must be unaffected
lst.append(6)
lst[0] = 99
assert lst == [99, 2, 3, 4, 5, 6]
assert t == (1, 2, 3, 4, 5)

# Tuples from various sources
assert tuple("abc") == ('a', 'b', 'c')
assert tuple(range(5)) == (0, 1, 2, 3, 4)
assert tuple(x * 2 for x in [1, 2, 3]) == (2, 4, 6)
assert tuple([]) == ()
assert tuple([(1, 2), (3, 4)]) == ((1, 2), (3, 4))

# tuple() on a tuple returns the same object (immutable)
t2 = (1, 2, 3)
assert tuple(t2) is t2

# tuple from a set (order may vary but elements are preserved)
s = {1, 2, 3}
ts = tuple(s)
assert sorted(ts) == [1, 2, 3]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"container", "tuple", "list", "conversion"}),
    ),
    T(
        name="frozenset_from_set_immutable",
        category="container_repr",
        description=(
            "A frozenset is constructed from a set. The frozenset must "
            "be immutable and usable as a dict key, while the source "
            "set remains mutable. Mutating the source must not affect "
            "the frozenset."
        ),
        source='''\
s = {1, 2, 3, 4, 5}
fs = frozenset(s)
assert fs == frozenset({1, 2, 3, 4, 5})
assert isinstance(fs, frozenset)
assert isinstance(s, set)

# Mutating the source does not affect the frozenset
s.add(6)
s.discard(1)
assert s == {2, 3, 4, 5, 6}
assert fs == frozenset({1, 2, 3, 4, 5})

# frozenset operations
fs2 = frozenset(range(3, 10))
assert fs | fs2 == frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9})
assert fs & fs2 == frozenset({3, 4, 5})
assert fs - fs2 == frozenset({1, 2})

# Can use frozenset as dict key
d = {fs: 'value'}
assert d[frozenset({1, 2, 3, 4, 5})] == 'value'

# Cannot use a set as a dict key (unhashable)
try:
    {s: 'x'}
    assert False, "expected TypeError"
except TypeError:
    pass

# frozenset from a generator
fs3 = frozenset(x * x for x in range(5))
assert fs3 == frozenset({0, 1, 4, 9, 16})

# frozenset from a string (chars become elements)
fs4 = frozenset("hello")
assert fs4 == frozenset({'h', 'e', 'l', 'l', 'o'})
assert fs4 == frozenset({'h', 'e', 'l', 'o'})

# Frozen set is immutable: cannot add/remove
try:
    fs.add(99)
    assert False, "expected AttributeError"
except AttributeError:
    pass
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="cold",
                         tags={"container", "frozenset", "immutable", "hash"}),
    ),
]
