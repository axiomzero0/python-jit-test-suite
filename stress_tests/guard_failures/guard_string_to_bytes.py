# -*- coding: utf-8 -*-
# stress test: guard_string_to_bytes
# category: guard_failures
# opt_state: (runs across all 6 states)
#
# Target: String type guard fails when bytes is passed.
#
# Tags: ['bytes', 'guard', 'string']
def upper(s):
    return s.upper()

for _ in range(1000):
    upper("hello")

# Guard fails: bytes
try:
    upper(b"hello")
    # bytes does have upper() but returns bytes
    assert upper(b"hello") == b"HELLO"
except AttributeError:
    pass  # depending on impl

assert upper("hello") == "HELLO"

