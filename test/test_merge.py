import pytest
import asyncio
import logging

from aioreactive.core import subscribe
from aioreactive.operators.from_iterable import from_iterable
from aioreactive.operators.merge import merge
from aioreactive.testing import AsyncStream, VirtualTimeEventLoop, AsyncAnonymousObserver

logging.basicConfig(level=logging.DEBUG)


@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_merge_done():
    xs = AsyncStream()

    ys = merge(xs)

    obv = AsyncAnonymousObserver()
    await subscribe(ys, obv)
    await xs.asend(from_iterable([10]))
    await xs.asend(from_iterable([20]))
    await xs.aclose()
    await obv

    assert obv.values == [
        (0, 10),
        (0, 20),
        (0,)
    ]

@pytest.mark.asyncio
async def test_merge_streams():
    xs = AsyncStream()
    s1 = AsyncStream()
    s2 = AsyncStream()

    ys = merge(xs)

    obv = AsyncAnonymousObserver()
    await subscribe(ys, obv)
    await xs.asend(s1)
    await xs.asend(s2)

    await s1.asend_at(1, 10)
    await s1.asend_at(2, 20)
    await s1.asend_at(4, 30)
    await s1.aclose_at(6)

    await s2.asend_at(0, 40)
    await s2.asend_at(3, 50)
    await s2.asend_at(5, 60)
    await s2.aclose_at(6)

    await xs.aclose()
    await obv

    assert obv.values == [
        (0, 40),
        (1, 10),
        (2, 20),
        (3, 50),
        (4, 30),
        (5, 60),
        (6,)
    ]


@pytest.mark.asyncio
async def test_merge_streams_concat():
    s1 = AsyncStream()
    s2 = from_iterable([1, 2, 3])

    xs = from_iterable([s1, s2])

    ys = merge(xs, 1)

    obv = AsyncAnonymousObserver()
    await subscribe(ys, obv)

    await s1.asend_at(1, 10)
    await s1.asend_at(2, 20)
    await s1.asend_at(4, 30)
    await s1.aclose_at(6)

    await obv

    assert obv.values == [
        (1, 10),
        (2, 20),
        (4, 30),
        (6, 1),
        (6, 2),
        (6, 3),
        (6,)
    ]


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_merge_streams())
    loop.close()
