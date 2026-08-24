# -*- coding: utf-8 -*-
# test_id: conc-0000042
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: async
# opt_state: cold
# tags: ['GC', 'async_gen', 'concurrency']
import asyncio
async def agen(n):
    for i in range(n):
        yield i
async def main():
    return [v async for v in agen(5)]
assert asyncio.run(main()) == [0, 1, 2, 3, 4]

