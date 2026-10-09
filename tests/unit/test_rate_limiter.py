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
def test_cleanup_removes_expired_identities(monkeypatch):
    from api.security import rate_limiter as module

    clock = [100.0]
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])

    limiter = module.RateLimiter(limit=10, window_seconds=60)

    limiter.check("user-a")
    assert "user-a" in limiter.requests

    clock[0] = 161.0
    limiter.cleanup()

    assert "user-a" not in limiter.requests


def test_cleanup_preserves_active_identities(monkeypatch):
    from api.security import rate_limiter as module

    clock = [100.0]
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])

    limiter = module.RateLimiter(limit=10, window_seconds=60)

    limiter.check("old-user")

    clock[0] = 130.0
    limiter.check("active-user")

    clock[0] = 161.0
    limiter.cleanup()

    assert "old-user" not in limiter.requests
    assert "active-user" in limiter.requests
    assert len(limiter.requests["active-user"]) == 1
def test_automatic_cleanup_on_new_request(monkeypatch):
    from api.security import rate_limiter as module

    clock = [100.0]
    monkeypatch.setattr(module, "monotonic", lambda: clock[0])

    limiter = module.RateLimiter(limit=10, window_seconds=60)

    limiter.check("old-user")
    assert "old-user" in limiter.requests

    clock[0] = 161.0
    limiter.check("new-user")

    assert "old-user" not in limiter.requests
    assert "new-user" in limiter.requests