from collections import defaultdict, deque
from math import ceil
from threading import Lock
from time import monotonic

from fastapi import HTTPException


class RateLimiter:
    def __init__(self, limit=10, window_seconds=60):
        if limit < 1 or window_seconds <= 0:
            raise ValueError("Invalid rate limit configuration")

        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = Lock()

    def check(self, identity):
        now = monotonic()

        with self.lock:
            timestamps = self.requests[identity]

            while timestamps and now - timestamps[0] >= self.window_seconds:
                timestamps.popleft()

            if len(timestamps) >= self.limit:
                retry_after = max(
                    1,
                    ceil(self.window_seconds - (now - timestamps[0])),
                )

                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

            timestamps.append(now)