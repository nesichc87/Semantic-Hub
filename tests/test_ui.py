from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ui_serves_html_page():
    response = client.get("/ui/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>Semantic Hub</title>" in response.text



def test_ui_without_trailing_slash_redirects():
    response = client.get("/ui", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].endswith("/ui/")