
from io import BytesIO

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def upload(filename, content):
    return client.post(
        "/api/audit",
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
    response = client.post("/api/audit")

    assert response.status_code == 422
