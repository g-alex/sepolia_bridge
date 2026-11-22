"""Small retry helper for flaky RPC calls."""

import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def with_retry(
    action: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    last_error: BaseException | None = None
    attempts = max(1, max_retries)

    for attempt in range(1, attempts + 1):
        try:
            return await action()
        except exceptions as exc:
            last_error = exc
            logger.warning("Attempt %s/%s failed: %s", attempt, attempts, exc)
            if attempt < attempts:
                await asyncio.sleep(delay)

    assert last_error is not None
    raise last_error
