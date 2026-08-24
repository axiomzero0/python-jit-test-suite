# -*- coding: utf-8 -*-
# test_id: conc-0000025
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: async
# opt_state: warm
# tags: ['GC', 'async_gather', 'concurrency']
import asyncio
async def f(i):
    return i * 2
async def main():
    return await asyncio.gather(*[f(i) for i in range(10)])
assert asyncio.run(main()) == [i * 2 for i in range(10)]

