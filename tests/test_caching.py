from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_page_files_must_be_revalidated():
    for path in ("/ui/", "/ui/ui.js", "/ui/i18n.js", "/ui/ui.css"):
        response = client.get(path)

        assert response.status_code == 200, path
        assert response.headers.get("cache-control") == "no-cache", path