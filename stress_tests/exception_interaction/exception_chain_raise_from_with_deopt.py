# -*- coding: utf-8 -*-
# stress test: exception_chain_raise_from_with_deopt
# category: exception_interaction
#
# Target: Uses ``raise X from Y`` inside a loop that deopts at i=500 (type change x='trigger'). The __cause__ and __context__ links must survive deopt and be observable by the caller.
#
# Tags: ['cause', 'chain', 'context', 'exception', 'raise-from']
def raiser(n):
    for i in range(n):
        if i == 500:
            x = "trigger"  # type change -> deopt
            try:
                raise KeyError("original")
            except KeyError as ke:
                raise ValueError("chained") from ke

try:
    raiser(1000)
    assert False, "should have raised ValueError"
except ValueError as ve:
    assert str(ve) == "chained"
    assert isinstance(ve.__cause__, KeyError)
    # KeyError.__str__ wraps the arg in repr, so check .args instead
    assert ve.__cause__.args == ("original",)
    assert isinstance(ve.__context__, KeyError)
    assert ve.__context__.args == ("original",)
    assert ve.__suppress_context__ is True

