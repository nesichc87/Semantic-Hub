from fastapi.testclient import TestClient

from app.main import app


def sqlite_url(path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_health_ok_with_reachable_database(tmp_path, monkeypatch):
    monkeypatch.setenv("SEMANTIC_HUB_DATABASE_URL", sqlite_url(tmp_path / "catalog.db"))
    monkeypatch.delenv("SEMANTIC_HUB_SEED_SOURCES", raising=False)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_unavailable_database_is_reported_and_app_keeps_running(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "SEMANTIC_HUB_DATABASE_URL", sqlite_url(tmp_path / "missing" / "catalog.db")
    )
    monkeypatch.delenv("SEMANTIC_HUB_SEED_SOURCES", raising=False)

    with TestClient(app) as client:
        health = client.get("/health")
        root = client.get("/")

    assert health.status_code == 503
    assert health.json() == {"status": "degraded", "database": "unavailable"}
    assert root.status_code == 200


def test_health_without_started_catalog_is_unavailable():
    # Without "with", the TestClient does not run the lifespan.
    response = TestClient(app).get("/health")

    assert response.status_code == 503