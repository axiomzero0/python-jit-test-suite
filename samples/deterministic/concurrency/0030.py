# -*- coding: utf-8 -*-
# test_id: conc-0000030
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: async
# opt_state: cold
# tags: ['GC', 'async_with_lock', 'concurrency']
import asyncio
lock = asyncio.Lock()
async def worker(i, out):
    async with lock:
        out.append(i)
async def main():
    out = []
    await asyncio.gather(*[worker(i, out) for i in range(10)])
    return sorted(out)
assert asyncio.run(main()) == list(range(10))

