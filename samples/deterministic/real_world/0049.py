# -*- coding: utf-8 -*-
# test_id: rw-0000049
# category: real_world
# semantic: real_world
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['lexer', 'real-world', 'small']
def tokenize(s):
    toks = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit():
            j = i
            while j < len(s) and s[j].isdigit():
                j += 1
            toks.append(('NUM', int(s[i:j]))); i = j; continue
        if c.isalpha():
            j = i
            while j < len(s) and s[j].isalpha():
                j += 1
            toks.append(('ID', s[i:j])); i = j; continue
        toks.append(('OP', c)); i += 1
    return toks
assert tokenize('x = 42') == [('ID','x'),('OP','='),('NUM',42)]

