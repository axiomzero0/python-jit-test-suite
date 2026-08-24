"""Oracle: compares CPython reference behavior to JIT behavior.

Strategy:
1. Run the source under CPython (the reference). Capture return value,
   raised exception, and observable side effects (printed output, mutated
   module globals).
2. Run the same source under the JIT under test with the same inputs.
3. Normalize both observations and compare.

The strongest oracle is differential: ``reference_result == jit_result``
after normalization.

For exceptions, the oracle is ``(type(exc), normalized_args)``.
For floats, use ``_float_key`` so NaN==NaN, +0==-0, but otherwise
require bit-identical (with optional ULP tolerance for transcendental
kernels via :class:`FloatCompare`).
"""

from __future__ import annotations

import contextlib
import io
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

from .normalize import normalize


@dataclass
class Observation:
    """Everything we observe from running a program once."""

    return_value: Any = None
    exception: BaseException | None = None
    stdout: str = ""
    stderr: str = ""
    globals_after: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0

    def canonical(self) -> dict:
        if self.exception is not None:
            exc = self.exception
            return {
                "kind": "exception",
                "type": type(exc).__name__,
                "args": normalize(exc.args),
                "return": None,
                "stdout": self.stdout,
                "stderr": self.stderr,
                "globals": normalize(self.globals_after),
                "exit": self.exit_code,
            }
        return {
            "kind": "return",
            "type": None,
            "args": None,
            "return": normalize(self.return_value),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "globals": normalize(self.globals_after),
            "exit": self.exit_code,
        }


def run_cpython(
    source: str,
    *,
    inputs: dict[str, Any] | None = None,
    capture_globals: tuple[str, ...] = (),
    timeout: float | None = None,
) -> Observation:
    """Run ``source`` in a fresh module namespace under stock CPython."""
    ns: dict[str, Any] = dict(inputs or {})
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    obs = Observation()

    # Save initial globals snapshot so we can diff later.
    initial_keys = set(ns.keys())

    try:
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            compiled = compile(source, "<cpython_ref>", "exec")
            exec(compiled, ns)
        # If the source defined a top-level ``main`` callable, call it.
        if "main" in ns and callable(ns["main"]):
            obs.return_value = ns["main"]()
        else:
            obs.return_value = None
    except SystemExit as e:
        obs.exit_code = e.code if isinstance(e.code, int) else 1
        obs.exception = e
    except BaseException as e:  # noqa: BLE001 - we want everything
        obs.exception = e

    obs.stdout = out_buf.getvalue()
    obs.stderr = err_buf.getvalue()

    obs.globals_after = {
        k: ns[k]
        for k in capture_globals
        if k in ns and k not in initial_keys
    }
    return obs


def run_callable(
    fn: Callable[..., Any],
    *args,
    **kwargs,
) -> Observation:
    """Run an in-process callable and capture its observable behavior.

    Used when the JIT exposes a Python-level entry point that we want to
    invoke repeatedly with different inputs.
    """
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    obs = Observation()
    try:
        with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(err_buf):
            obs.return_value = fn(*args, **kwargs)
    except BaseException as e:  # noqa: BLE001
        obs.exception = e
    obs.stdout = out_buf.getvalue()
    obs.stderr = err_buf.getvalue()
    return obs


def compare(
    reference: Observation,
    candidate: Observation,
    *,
    strict_stdout: bool = True,
    strict_stderr: bool = False,
) -> tuple[bool, str]:
    """Compare two observations. Returns ``(equal, reason)``."""
    rc = reference.canonical()
    cc = candidate.canonical()

    # Type of completion must match (return vs exception).
    if rc["kind"] != cc["kind"]:
        return False, f"completion kind differs: {rc['kind']} vs {cc['kind']}"

    # Exception comparison: type + normalized args
    if rc["kind"] == "exception":
        if rc["type"] != cc["type"]:
            return False, f"exception type differs: {rc['type']} vs {cc['type']}"
        if rc["args"] != cc["args"]:
            return False, f"exception args differ: {rc['args']!r} vs {cc['args']!r}"

    # Return value
    if rc["return"] != cc["return"]:
        return False, f"return value differs: {rc['return']!r} vs {cc['return']!r}"

    # Side effects
    if strict_stdout and rc["stdout"] != cc["stdout"]:
        return False, f"stdout differs:\n--- ref ---\n{rc['stdout']!r}\n--- cand ---\n{cc['stdout']!r}"
    if strict_stderr and rc["stderr"] != cc["stderr"]:
        return False, f"stderr differs: {rc['stderr']!r} vs {cc['stderr']!r}"

    if rc["globals"] != cc["globals"]:
        return False, f"mutated globals differ: {rc['globals']!r} vs {cc['globals']!r}"

    if rc["exit"] != cc["exit"]:
        return False, f"exit code differs: {rc['exit']} vs {cc['exit']}"

    return True, "ok"
