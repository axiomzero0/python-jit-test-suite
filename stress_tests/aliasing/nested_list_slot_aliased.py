# -*- coding: utf-8 -*-
# stress test: nested_list_slot_aliased
# category: aliasing
# opt_state: (runs across all 6 states)
#
# Target: An outer list holds a reference to an inner list. Mutating the inner list (through its alias `b`) must change what the outer list's slot reports. A JIT that scalar-replaces the outer list's elements into unboxed locals would lose this.
#
# Tags: ['aliasing', 'container', 'list', 'nested', 'stress']
b = [10, 20]
a = [b, 99]
b.append(30)
assert a[0] == [10, 20, 30]
assert a[0] is b
b[0] = 999
assert a[0][0] == 999
a[0].append(40)
assert b == [999, 20, 30, 40]

