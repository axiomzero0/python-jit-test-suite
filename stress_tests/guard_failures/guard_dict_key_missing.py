# -*- coding: utf-8 -*-
# stress test: guard_dict_key_missing
# category: guard_failures
# opt_state: (runs across all 6 states)
#
# Target: Dict key presence guard fails when key is missing.
#
# Tags: ['dict', 'guard', 'missing']
d = {str(i): i for i in range(100)}

def lookup(k):
    return d[k]

for i in range(1000):
    lookup(str(i % 100))

# Guard fails: missing key
for k in ["missing", "absent", "xxx"]:
    try:
        lookup(k)
        assert False
    except KeyError:
        pass

assert lookup("50") == 50

