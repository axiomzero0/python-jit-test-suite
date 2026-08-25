# -*- coding: utf-8 -*-
# stress test: speculate_dict_then_custom_mapping
# category: type_speculation
#
# Target: JIT speculates `d[k]` is dict.__getitem__. Then an object with __getitem__ is passed. The deopt must call the custom __getitem__ rather than the inlined dict path.
#
# Tags: ['container', 'descriptor', 'type-speculation']
class CustomMapping:
    def __getitem__(self, k):
        if k == 'special':
            return 'CUSTOM'
        return 'default'

def lookup(d, k):
    return d[k]

# Warm up with dict
d = {str(i): i for i in range(100)}
for i in range(1000):
    lookup(d, str(i % 100))

# Now pass a custom mapping
cm = CustomMapping()
assert lookup(cm, 'special') == 'CUSTOM'
assert lookup(cm, 'other') == 'default'

