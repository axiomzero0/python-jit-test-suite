"""Concurrency / async: 5K tests.

Axes:

    feature        : threading_basic | threading_lock | threading_queue |
                     threading_pool | async_gather | async_with_lock |
                     async_chain | async_gen | thread_to_async |
                     async_exception | cancellation | race_condition |
                     producer_consumer
    opt_state      : all 6 (the harness mostly runs them cold)
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


FEATURES = (
    "threading_basic", "threading_lock", "threading_queue", "threading_pool",
    "async_gather", "async_with_lock", "async_chain", "async_gen",
    "async_exception", "cancellation", "race_condition", "producer_consumer",
)
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_TEMPLATES = {
    "threading_basic": (
        "import threading\n"
        "results = []\n"
        "def worker(i):\n    results.append(i)\n"
        "ts = [threading.Thread(target=worker, args=(i,)) for i in range(10)]\n"
        "for t in ts:\n    t.start()\n"
        "for t in ts:\n    t.join()\n"
        "assert sorted(results) == list(range(10))\n"
    ),
    "threading_lock": (
        "import threading\n"
        "lock = threading.Lock()\n"
        "counter = [0]\n"
        "def worker():\n"
        "    for _ in range(100):\n"
        "        with lock:\n            counter[0] += 1\n"
        "ts = [threading.Thread(target=worker) for _ in range(10)]\n"
        "for t in ts:\n    t.start()\n"
        "for t in ts:\n    t.join()\n"
        "assert counter[0] == 1000\n"
    ),
    "threading_queue": (
        "import queue, threading\n"
        "q = queue.Queue()\n"
        "def producer():\n    for i in range(100):\n        q.put(i)\n    q.put(None)\n"
        "def consumer(out):\n"
        "    while True:\n        v = q.get()\n        if v is None:\n            break\n        out.append(v)\n"
        "out = []\n"
        "c = threading.Thread(target=consumer, args=(out,))\n"
        "c.start()\n"
        "producer()\n"
        "c.join()\n"
        "assert sorted(out) == list(range(100))\n"
    ),
    "threading_pool": (
        "from concurrent.futures import ThreadPoolExecutor\n"
        "with ThreadPoolExecutor(max_workers=4) as ex:\n    results = list(ex.map(lambda x: x * x, range(20)))\n"
        "assert results == [i * i for i in range(20)]\n"
    ),
    "async_gather": (
        "import asyncio\n"
        "async def f(i):\n    return i * 2\n"
        "async def main():\n    return await asyncio.gather(*[f(i) for i in range(10)])\n"
        "assert asyncio.run(main()) == [i * 2 for i in range(10)]\n"
    ),
    "async_with_lock": (
        "import asyncio\n"
        "lock = asyncio.Lock()\n"
        "async def worker(i, out):\n"
        "    async with lock:\n        out.append(i)\n"
        "async def main():\n"
        "    out = []\n"
        "    await asyncio.gather(*[worker(i, out) for i in range(10)])\n"
        "    return sorted(out)\n"
        "assert asyncio.run(main()) == list(range(10))\n"
    ),
    "async_chain": (
        "import asyncio\n"
        "async def f1(x):\n    return x + 1\n"
        "async def f2(x):\n    return x * 2\n"
        "async def main():\n    return await f2(await f1(10))\n"
        "assert asyncio.run(main()) == 22\n"
    ),
    "async_gen": (
        "import asyncio\n"
        "async def agen(n):\n"
        "    for i in range(n):\n        yield i\n"
        "async def main():\n"
        "    return [v async for v in agen(5)]\n"
        "assert asyncio.run(main()) == [0, 1, 2, 3, 4]\n"
    ),
    "async_exception": (
        "import asyncio\n"
        "async def boom():\n    raise ValueError('x')\n"
        "async def main():\n"
        "    try:\n        await boom()\n"
        "    except ValueError:\n        return 'caught'\n"
        "assert asyncio.run(main()) == 'caught'\n"
    ),
    "cancellation": (
        "import asyncio\n"
        "async def slow():\n    await asyncio.sleep(1.0)\n    return 42\n"
        "async def main():\n"
        "    t = asyncio.create_task(slow())\n    t.cancel()\n"
        "    try:\n        await t\n"
        "    except asyncio.CancelledError:\n        return 'cancelled'\n"
        "assert asyncio.run(main()) == 'cancelled'\n"
    ),
    "race_condition": (
        "import threading\n"
        "# No lock: result is non-deterministic; we just check both runs terminate.\n"
        "counter = [0]\n"
        "def w():\n    for _ in range(100):\n        counter[0] += 1\n"
        "ts = [threading.Thread(target=w) for _ in range(5)]\n"
        "for t in ts:\n    t.start()\n"
        "for t in ts:\n    t.join()\n"
        "assert counter[0] <= 500\n"
    ),
    "producer_consumer": (
        "import asyncio\n"
        "async def producer(q):\n"
        "    for i in range(10):\n        await q.put(i)\n    await q.put(None)\n"
        "async def consumer(q, out):\n"
        "    while True:\n        v = await q.get()\n        if v is None:\n            break\n        out.append(v)\n"
        "async def main():\n"
        "    q = asyncio.Queue()\n    out = []\n"
        "    await asyncio.gather(producer(q), consumer(q, out))\n"
        "    return sorted(out)\n"
        "assert asyncio.run(main()) == list(range(10))\n"
    ),
}


def generate(*, n: int = 5_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="concurrency", id_prefix="conc")
    grid = param_grid(feature=FEATURES, opt=OPT_STATES)

    materialized = list(gb.expand_simple(
        grid,
        lambda p: _TEMPLATES[p["feature"]],
        tags_fn=lambda p: TagSet.make(
            "concurrency",
            type_stability="unknown",
            control_flow="if_else",
            call_behavior=("async" if "async" in p["feature"] or "cancellation" in p["feature"] else "indirect"),
            opt_state=p["opt"].value,
            tags={"concurrency", p["feature"], "GC"},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"conc-{i:07d}",
            category=case.category,
        )
