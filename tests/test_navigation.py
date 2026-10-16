from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_page_links_to_swagger():
    response = client.get("/ui/")

    assert 'href="/docs"' in response.text


def test_docs_uses_local_swagger_assets():
    response = client.get("/docs")

    assert response.status_code == 200
    assert "cdn.jsdelivr.net" not in response.text
    assert "/static/swagger/swagger-ui-bundle.js" in response.text
    assert "/static/swagger/swagger-ui.css" in response.text


def test_docs_links_back_to_demo_page():
    response = client.get("/docs")

    assert 'href="/ui/"' in response.text


def test_swagger_assets_are_served():
    js = client.get("/static/swagger/swagger-ui-bundle.js")
    css = client.get("/static/swagger/swagger-ui.css")

    assert js.status_code == 200
    assert css.status_code == 200
    assert css.headers["content-type"].startswith("text/css")