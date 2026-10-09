
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
import api.main as api_module
from api.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def configure_test_auth(monkeypatch):
    monkeypatch.setenv("BETA_API_TOKEN", "test-secret-token")

    limiter = api_module.audit_rate_limiter

    with limiter.lock:
        limiter.requests.clear()



def upload(filename, content):
    return client.post(
        "/api/audit",
        headers={"Authorization": "Bearer test-secret-token"},
        files={
            "file": (
                filename,
                BytesIO(content),
            )
        },
    )


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_csv_audit():
    csv_data = (
        b"Merchant No,Region,Time To Attend\n"
        b"1001,Gauteng,30 minutes\n"
        b"1002,Limpopo,1 hour\n"
        b"1003,Gauteng,45 minutes\n"
    )

    response = upload("sample.csv", csv_data)

    assert response.status_code == 200

    result = response.json()

    assert result["rows"] == 3
    assert result["columns"] == 3
    assert "quality" in result
    assert "recommendations" in result


def test_unsupported_file():
    response = upload(
        "sample.txt",
        b"Unsupported file",
    )

    assert response.status_code == 415


def test_empty_file():
    response = upload(
        "empty.csv",
        b"",
    )

    assert response.status_code == 400


def test_oversized_file():
    response = upload(
        "large.csv",
        b"x" * (5 * 1024 * 1024 + 1),
    )

    assert response.status_code == 413


def test_missing_file():
    response = client.post(
        "/api/audit",
        headers={"Authorization": "Bearer test-secret-token"},
    )

    assert response.status_code == 422
def test_configured_cors_origins(monkeypatch):
    import importlib
    import api.main as api_module

    production_origin = "https://takalani95.github.io"
    blocked_origin = "https://unapproved.example"

    with monkeypatch.context() as patch:
        patch.setenv("ALLOWED_ORIGINS", production_origin)
        reloaded_module = importlib.reload(api_module)

        with TestClient(reloaded_module.app) as test_client:
            allowed = test_client.options(
                "/api/audit",
                headers={
                    "Origin": production_origin,
                    "Access-Control-Request-Method": "POST",
                },
            )

            blocked = test_client.options(
                "/api/audit",
                headers={
                    "Origin": blocked_origin,
                    "Access-Control-Request-Method": "POST",
                },
            )

        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == production_origin

        assert blocked.status_code == 400
        assert "access-control-allow-origin" not in blocked.headers

    importlib.reload(api_module)

def test_beta_access_missing_configuration(monkeypatch):
    monkeypatch.delenv("BETA_API_TOKEN", raising=False)

    response = upload("sample.csv", b"a,b\n1,2\n")

    assert response.status_code == 503


def test_beta_access_missing_token(monkeypatch):
    monkeypatch.setenv("BETA_API_TOKEN", "test-secret-token")

    response = client.post(
        "/api/audit",
        files={
            "file": (
                "sample.csv",
                b"a,b\n1,2\n",
            )
        },
    )

    assert response.status_code == 401

def test_beta_access_invalid_token(monkeypatch):
    monkeypatch.setenv("BETA_API_TOKEN", "test-secret-token")

    response = client.post(
        "/api/audit",
        headers={"Authorization": "Bearer incorrect-token"},
        files={"file": ("sample.csv", b"a,b\n1,2\n")},
    )

    assert response.status_code == 401


def test_beta_access_valid_token(monkeypatch):
    monkeypatch.setenv("BETA_API_TOKEN", "test-secret-token")

    response = client.post(
        "/api/audit",
        headers={"Authorization": "Bearer test-secret-token"},
        files={
            "file": (
                "sample.csv",
                b"Merchant No,Region\n1001,Gauteng\n1002,Limpopo\n",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["rows"] == 2
def test_api_rate_limit_returns_429():
    for _ in range(api_module.audit_rate_limiter.limit):
        response = upload("sample.csv", b"a,b\n1,2\n")
        assert response.status_code == 200

    response = upload("sample.csv", b"a,b\n1,2\n")

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


def test_invalid_token_does_not_bypass_authentication():
    for _ in range(api_module.audit_rate_limiter.limit):
        response = upload("sample.csv", b"a,b\n1,2\n")
        assert response.status_code == 200

    response = client.post(
        "/api/audit",
        headers={"Authorization": "Bearer invalid-token"},
        files={"file": ("sample.csv", b"a,b\n1,2\n")},
    )

    assert response.status_code == 401
