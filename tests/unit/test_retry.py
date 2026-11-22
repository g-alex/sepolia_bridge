import pytest

from sepolia_bridge.retry import with_retry

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_with_retry_succeeds_after_failures():
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("rpc down")
        return "ok"

    result = await with_retry(flaky, max_retries=3, delay=0)
    assert result == "ok"
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_with_retry_raises_after_exhaustion():
    async def always_fail():
        raise TimeoutError("boom")

    with pytest.raises(TimeoutError):
        await with_retry(always_fail, max_retries=2, delay=0)
