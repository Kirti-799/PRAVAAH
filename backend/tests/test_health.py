from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify GET /api/health returns 200, valid schema, and expected fields."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "PRAVAAH API"
    assert data["version"] == "0.1.0"


def test_root_endpoint():
    """Verify GET / returns 200 and points to documentation."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "PRAVAAH API"
    assert "docs_url" in data
    assert data["docs_url"] == "/api/docs"
    assert "health_url" in data
    assert data["health_url"] == "/api/health"


def test_not_found_endpoint():
    """Verify invalid endpoints return 404."""
    response = client.get("/api/non-existent-route")
    assert response.status_code == 404
