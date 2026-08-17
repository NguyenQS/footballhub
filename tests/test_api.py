from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_teams():
    response = client.get("/teams")

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_team_not_found():
    response = client.get("/teams/99999")

    assert response.status_code == 404