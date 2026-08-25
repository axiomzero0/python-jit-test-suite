# -*- coding: utf-8 -*-
# stress test: guard_iterator_exhausted
# category: guard_failures
#
# Target: Iterator `has_next` guard fails when the iterator is exhausted earlier than expected.
#
# Tags: ['StopIteration', 'guard', 'iterator']
def consume(it, n):
    results = []
    for i in range(n):
        try:
            results.append(next(it))
        except StopIteration:
            results.append("exhausted")
    return results

it = iter(range(50))
r = consume(it, 100)
assert r[:50] == list(range(50))
assert all(x == "exhausted" for x in r[50:])

