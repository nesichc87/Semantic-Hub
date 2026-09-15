from fastapi import APIRouter, HTTPException

from app.registry.registry import SemanticRegistry
from app.resolver.resolver import SemanticResolver
from app.sources.mock import MockSemanticSource


router = APIRouter()

registry = SemanticRegistry()
registry.register(MockSemanticSource())

resolver = SemanticResolver(registry)


@router.get("/resolve/{semantic_id}")
def resolve(semantic_id: str):

    try:
        result = resolver.resolve(semantic_id)

        return {
            "semantic_id": semantic_id,
            "result": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )