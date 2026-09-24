from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.formatter.original import OriginalFormatter
from app.registry.registry import SemanticRegistry
from app.resolver.resolver import SemanticResolver
from app.sources.mock import MockSemanticSource
from app.sources.kbl.client import KBLClient
from app.sources.kbl.parser import KBLParser
from app.sources.kbl.service import KBLService
from app.sources.kbl.source import KBLSemanticSource


router = APIRouter()


KBL_XSD_URL = (
    "https://ecad-wiki.prostep.org/"
    "specifications/kbl/v25-sr1/kbl2.5-sr1.xsd"
)


# ---------------------------------------------------------------------------
# KBL source configuration
# ---------------------------------------------------------------------------

kbl_client = KBLClient(KBL_XSD_URL)
kbl_parser = KBLParser()

kbl_service = KBLService(
    client=kbl_client,
    parser=kbl_parser,
)

kbl_source = KBLSemanticSource(kbl_service)


# ---------------------------------------------------------------------------
# Semantic registry and resolver
# ---------------------------------------------------------------------------

registry = SemanticRegistry()

registry.register(MockSemanticSource())
registry.register(kbl_source)

resolver = SemanticResolver(registry)


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

original_formatter = OriginalFormatter()


# ---------------------------------------------------------------------------
# Semantic resolution
# ---------------------------------------------------------------------------

@router.get(
    "/resolve/{semantic_id}",
    summary="Resolve a semantic identifier",
    description=(
        "Resolves a semantic identifier through the Semantic Hub "
        "registry and returns the corresponding semantic information "
        "in the requested output format."
    ),
)
def resolve(
    semantic_id: str,
    format: Literal["original"] = Query(
        default="original",
        description=(
            "Output format used to represent the resolved semantic "
            "information. Currently only 'original' is supported."
        ),
    ),
):
    """
    Resolve a semantic identifier.

    The resolver determines the responsible semantic source,
    retrieves the semantic information and converts the internal
    semantic model into the requested API representation.
    """

    try:
        concept = resolver.resolve(semantic_id)

        if format == "original":
            result = original_formatter.format(concept)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format '{format}'",
            )

        return {
            "semantic_id": semantic_id,
            "format": format,
            "result": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ---------------------------------------------------------------------------
# Semantic suggestions
# ---------------------------------------------------------------------------

@router.get(
    "/suggest",
    summary="Suggest semantic identifiers",
    description=(
        "Searches the registered semantic sources for semantic "
        "identifiers matching the supplied query."
    ),
)
def suggest(
    query: str = Query(
        ...,
        min_length=1,
        description=(
            "Search text used to find matching semantic identifiers."
        ),
    ),
):
    """
    Suggest semantic identifiers matching a search query.

    The registry delegates the search to all registered semantic
    sources and aggregates their results.
    """

    return {
        "query": query,
        "results": registry.suggest(query),
    }