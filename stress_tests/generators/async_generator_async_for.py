# -*- coding: utf-8 -*-
# stress test: async_generator_async_for
# category: generators
#
# Target: An async generator (``async def`` with ``yield``) suspends on the event loop rather than the bytecode frame, but the resumable-frame requirement is identical. ``async for`` must drive the generator through every suspension, and a JIT that compiles the async-for loop must keep the async generator frame alive across ``await`` points.
#
# Tags: ['async-for', 'async-generator', 'yield']
import asyncio

async def agen(n):
    for i in range(n):
        yield i * i

async def main():
    out = []
    async for x in agen(10):
        out.append(x)
    return out

result = asyncio.run(main())
assert result == [i * i for i in range(10)]
assert len(result) == 10

# Verify the async generator can also be partially consumed and resumed,
# exercising the same frame across an explicit anext()/asend() cycle.
async def consume_partial():
    g = agen(5)
    a = await g.__anext__()
    b = await g.__anext__()
    rest = [v async for v in g]
    return (a, b, rest)

a, b, rest = asyncio.run(consume_partial())
assert (a, b, rest) == (0, 1, [4, 9, 16])

