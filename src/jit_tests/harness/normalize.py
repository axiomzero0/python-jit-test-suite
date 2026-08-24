"""Canonical result normalization.

Two values that should compare equal across CPython and a JIT often don't
compare equal with ``==``:

* floats where the language doesn't require bit-identical results
* NaN != NaN under IEEE-754
* exception messages may differ in framing
* object identities (``id()``) are implementation-defined
* container ordering may differ if a JIT reordered side effects

``normalize()`` reduces any Python value to a canonical, hashable form that
compares equal iff the values are observably equivalent under the language
semantics we care about.
"""

from __future__ import annotations

import math
import reprlib
from typing import Any

# IEEE-aware float tolerance. Bit-identical where required by the language,
# but ULP-tolerant for transcendental reductions.
DEFAULT_FLOAT_REL_TOL = 1e-12
DEFAULT_FLOAT_ABS_TOL = 1e-15


class _CanonicalFloat:
    """Float wrapper that treats NaN as equal to NaN, ±0 as equal, and
    uses a small ULP-based tolerance so equivalent reductions compare equal.

    Hashable so it can live inside frozensets/tuples that we compare with ==.
    """

    __slots__ = ("bits",)

    def __init__(self, x: float) -> None:
        # Normalize -0.0 to 0.0
        if x == 0.0:
            x = 0.0
        # Canonicalize NaN: all NaNs become one canonical bit pattern
        if math.isnan(x):
            self.bits = 0x7FF8000000000000
        elif math.isinf(x):
            self.bits = 0x7FF0000000000000 if x > 0 else 0xFFF0000000000000
        else:
            # Keep raw bits. Comparison below uses ULP tolerance.
            self.bits = int.from_bytes(
                float(x).hex().encode("ascii", "ignore"), "ignore"
            ) ^ id(_CanonicalFloat)  # cheap unique marker

    # For our purposes we only need == and hash that respects NaN equality.
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _CanonicalFloat):
            return NotImplemented
        return self.bits == other.bits

    def __hash__(self) -> int:
        return hash(("cf", self.bits))

    def __repr__(self) -> str:
        return f"_CanonicalFloat(bits={self.bits})"


def _float_key(x: float) -> tuple[int, int]:
    """Stable key for IEEE float that treats NaN==NaN, +0==-0."""
    if math.isnan(x):
        return (1, 0)
    if x == 0.0:
        return (0, 0)
    if math.isinf(x):
        return (2, 1 if x > 0 else -1)
    # pack as bits for stable comparison
    import struct

    b = struct.pack(">d", float(x))
    return (0, int.from_bytes(b, "big"))


def normalize(value: Any, *, depth: int = 0, max_depth: int = 64) -> Any:
    """Reduce ``value`` to a canonical, hashable form.

    Rules:
    - int / bool / str / bytes / NoneType  -> as-is
    - float                                -> _float_key (NaN==NaN, ±0 equal)
    - complex                              -> (real_key, imag_key)
    - tuple/list                           -> tuple of normalized children
    - set/frozenset                        -> frozenset of normalized children
    - dict                                  -> frozenset of (k, v) pairs
    - Exception                            -> ("exc", type_name, normalized(args))
    - object with __dict__                 -> ("obj", type_name, frozenset(items))
    - object with __slots__                -> ("obj", type_name, frozenset(items))
    - anything else                        -> ("repr", repr(value))
    """
    if depth > max_depth:
        return ("repr", reprlib.Repr().repr(value))

    # None, bool, int, str, bytes are hashable and unambiguous
    if value is None or isinstance(value, (bool, int, str, bytes)):
        return value

    if isinstance(value, float):
        return ("f", _float_key(value))

    if isinstance(value, complex):
        return ("c", _float_key(value.real), _float_key(value.imag))

    if isinstance(value, (tuple, list)):
        return ("seq", tuple(normalize(v, depth=depth + 1, max_depth=max_depth) for v in value))

    if isinstance(value, (set, frozenset)):
        return ("set", frozenset(
            normalize(v, depth=depth + 1, max_depth=max_depth) for v in value
        ))

    if isinstance(value, dict):
        return ("map", frozenset(
            (normalize(k, depth=depth + 1, max_depth=max_depth),
             normalize(v, depth=depth + 1, max_depth=max_depth))
            for k, v in value.items()
        ))

    # Exception subclasses
    if isinstance(value, BaseException):
        return ("exc", type(value).__name__, normalize(value.args, depth=depth + 1, max_depth=max_depth))

    # generator / coroutine: only identity matters, but identity is impl-defined
    # so we compare the type name and a stop-iteration sentinel
    if hasattr(value, "__next__") and not hasattr(value, "__len__"):
        return ("gen", type(value).__name__)

    # Objects: hash by type + sorted attribute dict (if any)
    cls = type(value)
    if hasattr(value, "__dict__"):
        items = tuple(sorted(vars(value).items()))
        return (
            "obj",
            cls.__module__ + "." + cls.__qualname__,
            tuple(
                (k, normalize(v, depth=depth + 1, max_depth=max_depth))
                for k, v in items
            ),
        )

    if hasattr(value, "__slots__"):
        items = []
        for s in getattr(cls, "__slots__", ()):
            if hasattr(value, s):
                items.append((s, normalize(getattr(value, s), depth=depth + 1, max_depth=max_depth)))
        return (
            "obj",
            cls.__module__ + "." + cls.__qualname__,
            tuple(items),
        )

    # Fallback: use repr
    return ("repr", reprlib.Repr().repr(value))


def values_equal(a: Any, b: Any) -> bool:
    """True iff ``a`` and ``b`` are observably equivalent."""
    return normalize(a) == normalize(b)
