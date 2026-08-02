from bayesiandraft_api.main import create_app
from fastapi.testclient import TestClient


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
