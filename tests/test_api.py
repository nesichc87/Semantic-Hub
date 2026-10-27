from fastapi.testclient import TestClient
from app.api.routes import semantic
from app.main import app


client = TestClient(app)


def test_resolve_mock_in_original_format():
    response = client.get("/api/resolve/mock:123")

    assert response.status_code == 200

    body = response.json()

    assert body["semantic_id"] == "mock:123"
    assert body["format"] == "original"
    assert body["result"]["semantic_id"] == "mock:123"


def test_resolve_mock_in_iec61360_format():
    response = client.get("/api/resolve/mock:123?format=iec61360")

    assert response.status_code == 200

    body = response.json()

    assert body["format"] == "iec61360"
    assert body["result"]["semantic_id"] == "mock:123"
    assert body["result"]["preferred_name"] == "Example semantic concept"
    assert body["result"]["properties"] == []
def test_resolve_with_unsupported_format_returns_422():
    response = client.get("/api/resolve/mock:123?format=xml")

    assert response.status_code == 422

def test_resolve_returns_503_when_source_cannot_be_loaded(monkeypatch):
    def unavailable(semantic_id):
        raise RuntimeError("Failed to load source from 'file:///private/path'")

    monkeypatch.setattr(semantic.resolver, "resolve", unavailable)

    response = client.get("/api/resolve/mock:123")

    assert response.status_code == 503
    assert "private" not in response.text