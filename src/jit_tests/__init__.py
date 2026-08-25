"""python-jit-test-suite

A workload-matrix + differential-fuzzing + hand-crafted stress test
suite for evaluating Python JIT compilers targeting Python 3.16 semantics.

Top-level layout:
    jit_tests.harness       - core runner, oracle, normalize, state control, tags
    jit_tests.deterministic - generators for the 200K deterministic workload matrix
    jit_tests.fuzz          - the 4 fuzzing engines (AST / mutation / state / differential)
    jit_tests.stress        - hand-crafted stress tests targeting specific JIT failure modes
    jit_tests.perf          - performance metrics collection
    jit_tests.reporting     - dashboard / status reporter
    jit_tests.cli           - command-line entry point
"""

__version__ = "0.2.0"
__target_python__ = "3.16"

__all__ = ["__version__", "__target_python__"]
