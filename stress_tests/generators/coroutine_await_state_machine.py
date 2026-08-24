# -*- coding: utf-8 -*-
# stress test: coroutine_await_state_machine
# category: generators
# opt_state: (runs across all 6 states)
#
# Target: A coroutine is a state machine: each ``await`` is a suspension/resumption edge. The JIT must preserve locals, the await stack, and exception routing across every edge. This coroutine awaits several sub-coroutines in sequence and also verifies that an exception raised after an await propagates correctly back through the suspension point.
#
# Tags: ['await', 'coroutine', 'state-machine']
import asyncio

async def add(a, b):
    await asyncio.sleep(0)   # genuine suspension / state-machine edge
    return a + b

async def compute():
    x = await add(1, 2)
    y = await add(x, 3)
    z = await add(y, 4)
    return z

assert asyncio.run(compute()) == 10

# Exception raised after an await must propagate to the caller, crossing
# the suspension boundary cleanly.
async def faulty():
    await asyncio.sleep(0)
    raise ValueError("boom")

async def caller():
    try:
        await faulty()
    except ValueError as e:
        return f"caught: {e}"

assert asyncio.run(caller()) == "caught: boom"

# A longer chain of awaits stresses repeated state-machine transitions.
async def accumulate(n):
    total = 0
    for i in range(n):
        total = await add(total, i)
    return total

assert asyncio.run(accumulate(100)) == sum(range(100))

