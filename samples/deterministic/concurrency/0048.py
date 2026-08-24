# -*- coding: utf-8 -*-
# test_id: conc-0000048
# category: concurrency
# semantic: concurrency
# type_stability: unknown
# control_flow: if_else
# call_behavior: async
# opt_state: cold
# tags: ['GC', 'async_exception', 'concurrency']
import asyncio
async def boom():
    raise ValueError('x')
async def main():
    try:
        await boom()
    except ValueError:
        return 'caught'
assert asyncio.run(main()) == 'caught'

