# -*- coding: utf-8 -*-
# stress test: string_interning_identity_alias
# category: aliasing
#
# Target: `sys.intern` returns the canonical interned string object so two interns of equal value are the *same object* (`is` True). A JIT that uses object identity as a fast-path equality check would silently start returning True for unrelated string literals that happen to be interned.
#
# Tags: ['aliasing', 'identity', 'interning', 'stress', 'string']
import sys

s1 = sys.intern("hello" + "_world")
s2 = sys.intern("hello_world")
assert s1 is s2
assert s1 == s2
# Non-interned copies of equal value are NOT necessarily identical.
plain_a = "hello_world"
plain_b = "hello_world"
# Literal interned at compile time; both should be the same object here.
assert plain_a is plain_b  # CPython interns small string literals.
# But constructing via runtime concatenation may produce a new object.
parts = ["hello", "_", "world"]
joined = "".join(parts)
assert joined == "hello_world"
# After interning, it becomes identical to the canonical form.
assert sys.intern(joined) is s1

