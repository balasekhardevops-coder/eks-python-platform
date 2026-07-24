from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Python application is running on EKS"
    )


def test_liveness_endpoint() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_endpoint() -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_create_user() -> None:
    response = client.post(
        "/users",
        json={
            "name": "Bala",
            "email": "bala@example.com",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["name"] == "Bala"