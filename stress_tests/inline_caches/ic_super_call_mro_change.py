# -*- coding: utf-8 -*-
# stress test: ic_super_call_mro_change
# category: inline_caches
# opt_state: (runs across all 6 states)
#
# Target: super() call caches the MRO. Then the class hierarchy changes (new base inserted). The cached super() lookup must invalidate.
#
# Tags: ['IC', 'MRO', 'hierarchy-mutation', 'super']
class Base:
    def f(self): return "Base"

class Mid(Base):
    def f(self): return "Mid->" + super().f()

class Top(Mid):
    def f(self): return "Top->" + super().f()

t = Top()
for _ in range(1000):
    assert t.f() == "Top->Mid->Base"

# Insert a new class between Mid and Base via __bases__ mutation.
# After this, MRO for Top becomes: Top -> Mid -> Inserted -> Base
# But super().f() in Mid was compiled to call Base.f; with the new
# MRO it should call Inserted.f. The IC for super() must invalidate.
class Inserted(Base):
    def f(self): return "Inserted"

Mid.__bases__ = (Inserted,)
# t.f() should now traverse Top -> Mid -> Inserted (Inserted inherits Base.f)
result = t.f()
assert result == "Top->Mid->Inserted", f"got {result!r}"

