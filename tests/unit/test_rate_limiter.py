import pytest
from fastapi import HTTPException

from api.security.rate_limiter import RateLimiter


def test_requests_within_limit_are_allowed():
    limiter = RateLimiter(limit=2, window_seconds=60)

    limiter.check("user-1")
    limiter.check("user-1")


def test_exceeding_limit_returns_429():
    limiter = RateLimiter(limit=2, window_seconds=60)

    limiter.check("user-1")
    limiter.check("user-1")

    with pytest.raises(HTTPException) as error:
        limiter.check("user-1")

    assert error.value.status_code == 429
    assert int(error.value.headers["Retry-After"]) >= 1


def test_different_users_have_independent_limits():
    limiter = RateLimiter(limit=1, window_seconds=60)

    limiter.check("user-1")
    limiter.check("user-2")

    with pytest.raises(HTTPException) as error:
        limiter.check("user-1")

    assert error.value.status_code == 429


def test_limit_resets_after_window(monkeypatch):
    current_time = [100.0]

    monkeypatch.setattr(
        "api.security.rate_limiter.monotonic",
        lambda: current_time[0],
    )

    limiter = RateLimiter(limit=1, window_seconds=60)

    limiter.check("user-1")

    current_time[0] = 161.0

    limiter.check("user-1")


@pytest.mark.parametrize(
    "limit,window_seconds",
    [
        (0, 60),
        (-1, 60),
        (10, 0),
        (10, -5),
    ],
)
def test_invalid_configuration(limit, window_seconds):
    with pytest.raises(ValueError):
        RateLimiter(limit=limit, window_seconds=window_seconds)