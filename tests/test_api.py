from fastapi.testclient import TestClient

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