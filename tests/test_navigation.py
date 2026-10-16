from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_demo_page_links_to_swagger():
    response = client.get("/ui/")

    assert 'href="/docs"' in response.text


def test_swagger_description_links_to_demo_page():
    response = client.get("/openapi.json")

    assert "(/ui/)" in response.json()["info"]["description"]