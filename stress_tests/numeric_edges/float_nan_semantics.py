# -*- coding: utf-8 -*-
# stress test: float_nan_semantics
# category: numeric_edges
#
# Target: NaN is not equal to anything, including itself, and propagates through arithmetic. A JIT that folds NaN comparisons or treats NaN as a normal value would break these invariants.
#
# Tags: ['ieee-754', 'nan', 'numeric']
import math
nan = float('nan')
# Defining property: NaN is not equal to itself.
assert nan != nan
assert not (nan == nan)
assert not (nan < 0.0)
assert not (nan > 0.0)
assert not (nan == 0.0)
assert not (nan <= 0.0)
assert not (nan >= 0.0)
assert math.isnan(nan)
# NaN propagates through arithmetic.
assert math.isnan(nan + 1.0)
assert math.isnan(nan * 0.0)
assert math.isnan(nan - nan)
# Containers use PyObject_RichCompareBool, which short-circuits on
# identity before calling __eq__. The SAME nan object IS found (via
# identity) even though nan == nan is False; distinct nan objects are not.
same = [nan, nan]
assert same.count(nan) == 2          # identity fast path counts both
assert nan in same                   # identity fast path
nan_other = float('nan')
assert nan_other not in same         # different objects, == is False
assert nan not in [0.0, 1.0]        # 0.0/1.0 are not nan, == is False
# math.isnan is the only reliable NaN detector.
assert any(math.isnan(x) for x in same)
# A NaN with a sign bit is still NaN and still unequal to itself.
nan2 = float('-nan')
assert math.isnan(nan2)
assert nan2 != nan2

