from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import semantic


STATIC_DIR = Path(__file__).parent / "static"
UI_DIR = STATIC_DIR / "ui"
SWAGGER_DIR = STATIC_DIR / "swagger"

# Swagger UI is served from local copies (swagger-ui-dist 5.17.14) so that
# the API documentation also works without network access.
SWAGGER_JS_URL = "/static/swagger/swagger-ui-bundle.js"
SWAGGER_CSS_URL = "/static/swagger/swagger-ui.css"

DEMO_LINK_BAR = (
    '<div style="padding: 10px 20px; border-bottom: 1px solid #d9d9d9; '
    'font-family: sans-serif; font-size: 15px;">'
    '<a href="/ui/" style="color: #1b46c2; text-decoration: none;">'
    "&larr; Semantic Hub demo page</a></div>"
)


app = FastAPI(
    title="Semantic Hub",
    description="""
The Semantic Hub provides a unified retrieval interface for
heterogeneous semantic sources used in Industry 4.0.

It resolves semantic identifiers, suggests matching semantic
concepts and provides different representations of semantic
information while preserving source provenance.
""",
    version="0.1.0",
    docs_url=None,
)


app.include_router(
    semantic.router,
    prefix="/api",
    tags=["Semantic Hub"],
)

app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")
app.mount("/static/swagger", StaticFiles(directory=SWAGGER_DIR), name="swagger")


@app.get("/docs", include_in_schema=False)
def swagger_ui() -> HTMLResponse:
    """
    Serve Swagger UI with local assets and a link back to the demo page.
    """

    page = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_js_url=SWAGGER_JS_URL,
        swagger_css_url=SWAGGER_CSS_URL,
        swagger_favicon_url="data:,",
    )
    html = page.body.decode("utf-8").replace("<body>", "<body>" + DEMO_LINK_BAR, 1)

    return HTMLResponse(html)


@app.get("/")
def root():
    return {
        "name": "Semantic Hub",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "ok"}