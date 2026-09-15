from fastapi import FastAPI

from app.api.routes import semantic


app = FastAPI(
    title="Semantic Hub",
    description="REST API for resolving and retrieving semantic information.",
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