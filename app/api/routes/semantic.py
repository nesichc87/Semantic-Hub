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
from app.formatter.iec61360 import IEC61360Formatter
from app.sources.vec.client import VECClient
from app.sources.vec.service import VECService
from app.sources.vec.source import VECSemanticSource


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
# VEC source configuration
# ---------------------------------------------------------------------------

VEC_TTL_URL = (
    "https://ecad-wiki.prostep.org/"
    "specifications/vec/v220/vec-2.2.0-ontology.ttl"
)

vec_client = VECClient(VEC_TTL_URL)
vec_service = VECService(client=vec_client)
vec_source = VECSemanticSource(vec_service)

# ---------------------------------------------------------------------------
# Semantic registry and resolver
# ---------------------------------------------------------------------------

registry = SemanticRegistry()

registry.register(MockSemanticSource())
registry.register(kbl_source)
registry.register(vec_source)

resolver = SemanticResolver(registry)


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

original_formatter = OriginalFormatter()
iec61360_formatter = IEC61360Formatter()
formatters = {
    "original": original_formatter,
    "iec61360": iec61360_formatter,
}


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
    format: Literal["original", "iec61360"] = Query(
        default="original",
        description=(
                "Output format used to represent the resolved semantic "
                "information. Supported formats: 'original', 'iec61360'."
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

        result = formatters[format].format(concept)

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