"""Decorator utilities"""
import asyncio
from typing import Literal


def set_interval(
    interval_in_seconds: float, interval_type: Literal["constant", "dynamic"]
):
    """Trigger an asynchronous function every n seconds"""

    def scheduler(func):
        async def wrapper(*args, **kwargs):
            while True:
                if interval_type == "dynamic":
                    # Wait n seconds between the end of the last execution and the beginning of the next
                    await asyncio.create_task(func(*args, **kwargs))
                    await asyncio.sleep(interval_in_seconds)
                else:
                    # Wait n seconds regardless of execution time
                    await asyncio.gather(
                        func(*args, **kwargs),
                        asyncio.sleep(interval_in_seconds),
                    )

        return wrapper

    return scheduler
