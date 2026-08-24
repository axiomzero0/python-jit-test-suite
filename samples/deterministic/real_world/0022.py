# -*- coding: utf-8 -*-
# test_id: rw-0000022
# category: real_world
# semantic: real_world
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['json_parser', 'pathological', 'real-world']
def parse(s):
    # minimal hand-rolled JSON-ish parser for objects of ints
    assert s[0] == '{' and s[-1] == '}'
    body = s[1:-1]
    if not body:
        return {}
    out = {}
    for kv in body.split(','):
        k, v = kv.split(':')
        out[k.strip().strip(chr(34))] = int(v.strip())
    return out
assert parse('{"a": 1, "b": 2}') == {'a': 1, 'b': 2}

for i in range(1000):
    parse('{"a": 1, "b": 2}')

