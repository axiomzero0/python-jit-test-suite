# python-jit-test-suite

A workload-matrix + differential-fuzzing test suite for evaluating Python
JIT compilers (CPython baseline, PyPy, custom JITs, etc.).

The design philosophy: a JIT test suite should not be "run Fibonacci 10
million times and declare victory." It should drive the runtime across
the *full* set of states a real JIT cycles through:

```
Python source
    ↓
interpreter
    ↓
profiling
    ↓
baseline JIT
    ↓
optimized JIT
    ↓
deoptimization
    ↓
re-entry / OSR
    ↓
GC / exceptions / side exits
```

That's where JITs actually become annoying. This suite is built around
that graph.

---

## What's inside

| Component                       | Default count |
| ------------------------------- | ------------: |
| Deterministic workload matrix   |     200,000   |
| AST fuzzing                     |     300,000   |
| Mutation fuzzing                |     250,000   |
| Optimization-state fuzzing      |     250,000   |
| Differential fuzzing            |     200,000   |
| **Total fuzz executions**      | **1,000,000** |

Plus: every failing fuzz case is delta-debugged down to the smallest
reproducer and stored as a permanent regression test.

### Deterministic matrix breakdown

| Category                         |       Tests |
| -------------------------------- | ----------: |
| Language semantics               |      30,000 |
| Interpreter/JIT tier transitions |      15,000 |
| Numeric workloads                |      25,000 |
| Objects/classes                  |      20,000 |
| Containers                       |      25,000 |
| Strings/Unicode                  |      15,000 |
| Functions/closures/generators    |      20,000 |
| Exceptions/control flow          |      10,000 |
| Python metaprogramming           |      10,000 |
| Memory/GC/lifetime               |      10,000 |
| Scientific/ML-style kernels      |      10,000 |
| Real-world mini workloads        |      10,000 |
| Concurrency/async                |       5,000 |
| **Total**                        | **200,000** |

---

## Quick start

```bash
# 1. install (editable)
pip install -e '.[dev]'

# 2. run a tiny slice via pytest
JIT_SUITE_SLICE=5 pytest -q

# 3. run the CLI directly
jit-suite deterministic --category numeric --limit 100
jit-suite fuzz --engine ast --limit 100
jit-suite all --limit 1000 --output results.jsonl
```

Each test runs the same source through CPython (reference) and a candidate
controller (default: also CPython — a trivial baseline so the suite works
out of the box). Plug in your real JIT by subclassing
`StateController`.

---

## Architecture

```
src/jit_tests/
├── harness/
│   ├── tags.py        TagSet + enums (semantic / type_stability /
│   │                  control_flow / call_behavior / opt_state / free-form tags)
│   ├── normalize.py   Canonical result normalization
│   │                  (NaN == NaN, ±0 equal, dict/set order-independent)
│   ├── oracle.py      Observation + run_cpython + compare
│   ├── states.py      StateController: warmup / force_deopt / invalidate_ic /
│   │                  trigger_gc, executed across 6 opt states
│   └── runner.py      TestCase + Runner: runs ref+cand, compares
├── deterministic/     13 generators producing the 200K matrix
├── fuzz/
│   ├── ast_fuzzer.py       Weighted AST generator (300K)
│   ├── mutation_fuzzer.py  AST-level mutations of seed programs (250K)
│   ├── state_fuzzer.py     Fixed programs, random runtime-state sequences (250K)
│   ├── differential.py     CPython-vs-JIT comparison programs (200K)
│   ├── minimizer.py        ddmin delta-debugging on AST nodes
│   └── regressions.py      Persist minimized failures as permanent regression tests
├── perf/
│   └── metrics.py     Per-case timing: interpreter/baseline/optimized/cpython
│                      + deopt_count / osr_count / ic_miss / guard_failures
│                      + speedup vs cpython/interpreter, JIT compile overhead,
│                      steady-state throughput, time-to-first-result
├── reporting/
│   └── dashboard.py   Final JIT TEST STATUS block (correctness %, perf summary)
└── cli.py             `jit-suite` command-line entry point
```

---

## The 6 opt states

Every case can be run in any of:

| State         | Behavior                                           |
| ------------- | -------------------------------------------------- |
| `cold`        | Single execution, no warmup.                       |
| `warm`        | 3 warmup reps, then collect.                       |
| `hot`         | 100 warmup reps, then collect.                     |
| `very_hot`    | 10,000 warmup reps, expect full optimization.      |
| `deoptimized` | Run hot, then force deopt, then collect.           |
| `reheated`    | Deopt, then re-warm, then collect.                 |

This catches the classic JIT bug: *"the function works perfectly unless
it has been optimized."*

---

## The 4 fuzzing engines

### A. AST fuzzer — 300K

Generates valid Python ASTs with weighted node selection (operators /
control-flow / calls weighted higher than literals). Each program
compiles, defines `main()`, and is unparsed to source.

### B. Mutation fuzzer — 250K

Takes a small library of seed programs and applies random AST mutations:

- operator replacement  (`+` → `-`, `*`, `/`, `//`, `%`)
- constant replacement   (`5` → `0`, `1`, `-1`, large, float)
- variable swap          (`x` → `y`, `z`)
- branch flip            (`if x` → `if not x`)
- loop bound mutation    (`range(10)` → `range(0)`, `range(1000)`)
- call target swap       (`len` → `abs`, `max`, `min`, `sum`)

Particularly good for regression testing.

### C. Optimization-state fuzzer — 250K

The really important one. Takes fixed valid programs and randomly
manipulates the **runtime state** they execute under:

```
run cold
run 3 times
run 100 times
run 10,000 times
change argument type
invalidate IC
trigger GC
raise exception
force deopt
resume
change globals
```

The program itself doesn't change. The runtime state does. Catches JIT
bugs that ordinary fuzzing completely misses.

### D. Differential fuzzer — 200K

Run CPython and the candidate with identical source / inputs / seed and
compare:

- return value
- stdout / stderr
- exception type + args
- mutated globals
- observable object state

For particularly nasty cases, plug in a third implementation (PyPy) and
do three-way comparison.

---

## Minimization: ddmin on AST nodes

When a fuzz case finds a discrepancy, the harness automatically
delta-debugs it down toward the smallest input that still fails.

```
438 lines, 1,700 AST nodes  →  2 lines, 7 AST nodes
JIT != CPython                JIT != CPython
```

Every minimized failure is stored as a permanent regression test under
`fuzz_failures/`:

```
fuzz_failures/
    000001.py            <- minimized failing source
    000001.meta.json     <- metadata: fuzz id, opt state, reason
    000002.py
    000002.meta.json
    ...
```

So the suite evolves:

```
fuzzer  →  bug  →  minimizer  →  regression test  →  never breaks again
```

(Unless someone later "cleans up" the deoptimizer and resurrects it
from the dead.)

---

## Performance metrics

For each hot workload the harness collects:

```
interpreter_time       baseline_jit_time      optimized_jit_time
cpython_time           compile_time           warmup_time
peak_memory_bytes      allocation_count       deopt_count
osr_count              ic_miss_count          guard_failures
gc_time                iterations
```

Derived:

```
speedup_vs_cpython     speedup_vs_interpreter
jit_compilation_overhead
steady_state_throughput
time_to_first_result
```

We deliberately measure both `time-to-first-result` and steady-state
throughput, because a JIT that is spectacular after 40 seconds is useless
for every actual Python program.

---

## Final dashboard

After a full run, the harness renders:

```
JIT TEST STATUS
────────────────────────────────────────────────────────────
Deterministic                    200,000 /     200,000
Fuzz                           1,000,000 /   1,000,000
Differential                     200,000 /     200,000
Regressions                             0

Correctness                       100.0000%
Semantic mismatches                     0
Crashes                                 0
Invalid deopts                          0
GC violations                           0

Avg warmup                           0.83 ms
Median hot speedup                       8.70x
P95 hot speedup                          5.10x
Max hot speedup                         31.40x
```

The most important architectural decision is that the test runner
understands JIT state. A static corpus catches compiler bugs. A dynamic
corpus catches specialization bugs. **Stateful differential fuzzing
catches the bugs where the optimizer was correct at 9:01, wrong at 9:02,
and nobody can reproduce it because the moon was apparently in the wrong
phase.**

---

## Plugging in a real JIT

```python
from jit_tests.harness import StateController, Runner

class MyJITController(StateController):
    def warmup(self, source, inputs, n):
        # Run source through your JIT n times to trigger tier-up
        for _ in range(n):
            self._jit_run(source, inputs)

    def force_deopt(self, source, inputs):
        # Trigger your JIT's deopt path
        self._jit_force_deopt(source)

    def invalidate_ic(self, source, inputs):
        # Invalidate your inline caches
        self._jit_invalidate_ics(source)

    def run(self, source, *, inputs=None, opt_state="cold",
            capture_globals=(), timeout=None):
        # Single execution under the JIT, returning an Observation
        out = self._jit_exec(source, inputs, opt_state)
        return Observation(
            return_value=out.return_value,
            exception=out.exception,
            stdout=out.stdout,
            stderr=out.stderr,
            globals_after=out.globals_after,
        )

runner = Runner(reference=StateController(), candidate=MyJITController())
for case in generate_all():
    r = runner.run_one(case)
    if not r.passed:
        print(f"FAIL {case.id}: {r.reason}")
```

---

## Layout

```
python-jit-test-suite/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/jit_tests/
│   ├── harness/        # core: tags, normalize, oracle, states, runner
│   ├── deterministic/  # 13 generators producing 200K cases
│   ├── fuzz/           # 4 engines + minimizer + regression store
│   ├── perf/           # timing metrics + aggregation
│   ├── reporting/      # dashboard
│   └── cli.py          # `jit-suite` CLI
├── tests/
│   ├── test_harness.py    # unit tests on normalize/oracle/runner
│   └── test_suite.py       # pytest wrappers around the matrix
└── fuzz_failures/          # minimized failing cases (auto-populated)
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Status

This is the **starting point**, not the finish line. For a serious Python
JIT, the 200K + 1M setup described here is reasonable rather than
absurdly large. The whole point of having a budget this big is that you
*can* actually run it — the harness is deterministic and shardable, the
fuzzers are reproducible, and every failure gets minimized into a
regression test that lives forever.
