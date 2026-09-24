from fastapi import FastAPI

from app.api.routes import semantic


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
)


app.include_router(
    semantic.router,
    prefix="/api",
    tags=["Semantic Hub"],
)

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
@app.get("/propose")
def health():
    return {"status": "ok"}