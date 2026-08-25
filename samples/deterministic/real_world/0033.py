# -*- coding: utf-8 -*-
# test_id: rw-0000033
# category: real_world
# semantic: real_world
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: very_hot
# tags: ['csv_parser', 'medium', 'real-world']
def parse(line):
    out = []
    cur = ''
    in_q = False
    for c in line:
        if c == '"':
            in_q = not in_q
        elif c == ',' and not in_q:
            out.append(cur); cur = ''
        else:
            cur += c
    out.append(cur)
    return out
assert parse('a,b,c') == ['a','b','c']
assert parse('"a,b",c') == ['a,b','c']

for _ in range(10):
    pass

