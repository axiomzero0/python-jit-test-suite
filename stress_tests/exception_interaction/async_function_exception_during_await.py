# -*- coding: utf-8 -*-
# stress test: async_function_exception_during_await
# category: exception_interaction
#
# Target: An async function raises a custom exception on iteration 500 inside a loop that awaits ``asyncio.sleep(0)``. The exception must propagate through the await boundary to the caller's try/except. A JIT that compiled the coroutine must deopt at the await suspension and propagate correctly.
#
# Tags: ['async', 'await', 'coroutine', 'exception', 'propagation']
import asyncio

class Boom(Exception):
    pass

async def fail_at(n):
    for i in range(n):
        if i == 500:
            raise Boom("async failure")
        await asyncio.sleep(0)
    return n

async def main():
    try:
        await fail_at(1000)
        assert False, "should raise Boom"
    except Boom as e:
        assert str(e) == "async failure"
    return "ok"

r = asyncio.run(main())
assert r == "ok"

