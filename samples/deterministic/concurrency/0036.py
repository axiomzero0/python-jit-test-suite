# -*- coding: utf-8 -*-
# test_id: conc-0000036
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: async
# opt_state: cold
# tags: ['GC', 'async_chain', 'concurrency']
import asyncio
async def f1(x):
    return x + 1
async def f2(x):
    return x * 2
async def main():
    return await f2(await f1(10))
assert asyncio.run(main()) == 22

