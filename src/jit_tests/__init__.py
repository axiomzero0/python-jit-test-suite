"""python-jit-test-suite

A workload-matrix + differential-fuzzing test suite for evaluating Python
JIT compilers (CPython baseline, PyPy, custom JITs, etc.).

Top-level layout:
    jit_tests.harness       - core runner, oracle, normalize, state control, tags
    jit_tests.deterministic - generators for the 200K deterministic workload matrix
    jit_tests.fuzz          - the 4 fuzzing engines (AST / mutation / state / differential)
    jit_tests.perf          - performance metrics collection
    jit_tests.reporting     - dashboard / status reporter
    jit_tests.cli           - command-line entry point
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
