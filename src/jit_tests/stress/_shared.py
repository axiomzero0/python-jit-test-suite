"""Shared alias for the StressTest constructor.

Each category module imports `T` from here to keep test definitions terse:

    from .._shared import T
    STRESS_TESTS = [T(name=..., description=..., source=..., ...)]
"""

from . import StressTest

T = StressTest
