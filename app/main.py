from fastapi import FastAPI

from app.api.routes import semantic
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="Semantic Hub",
    description="""
The Semantic Hub provides a unified retrieval interface for
heterogeneous semantic sources used in Industry 4.0.

It resolves semantic identifiers, suggests matching semantic
concepts and provides different representations of semantic
information while preserving source provenance.

[Open the demo page](/ui/)
""",
    version="0.1.0",
)


app.include_router(
    semantic.router,
    prefix="/api",
    tags=["Semantic Hub"],
)
UI_DIR = Path(__file__).parent / "static" / "ui"

app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")

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