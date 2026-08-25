# -*- coding: utf-8 -*-
# stress test: async_generator_exception
# category: exception_interaction
#
# Target: An async generator raises ValueError on iteration 500. The exception must propagate out of the ``async for`` loop. A JIT that compiled the async generator's body must deopt at the yield point and propagate the exception.
#
# Tags: ['async-generator', 'exception', 'propagation', 'yield']
import asyncio

async def agen(n):
    acc = 0
    for i in range(n):
        if i == 500:
            raise ValueError("async gen failure")
        acc += i
        yield acc

async def main():
    results = []
    try:
        async for v in agen(1000):
            results.append(v)
        assert False, "should raise ValueError"
    except ValueError as e:
        assert str(e) == "async gen failure"
    # 500 values yielded before the exception
    assert len(results) == 500, len(results)
    assert results[0] == 0
    assert results[1] == 1
    assert results[499] == sum(range(500))
    return "ok"

r = asyncio.run(main())
assert r == "ok"

