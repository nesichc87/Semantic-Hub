from typing import Literal

from fastapi import APIRouter, HTTPException, Query
import os
import logging


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
from app.sources.qudt.client import QUDTClient
from app.sources.qudt.service import QUDTService
from app.sources.qudt.source import QUDTSemanticSource
from app.sources.dppo.client import DPPOClient
from app.sources.dppo.service import DPPOService
from app.sources.dppo.source import DPPOSemanticSource
from app.config import source_url


router = APIRouter()
logger = logging.getLogger(__name__)


KBL_XSD_URL = source_url(
    os.environ,
    "SEMANTIC_HUB_KBL_XSD_URL",
    "https://ecad-wiki.prostep.org/"
    "specifications/kbl/v25-sr1/kbl2.5-sr1.xsd",
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

VEC_TTL_URL = source_url(
    os.environ,
    "SEMANTIC_HUB_VEC_TTL_URL",
    "https://ecad-wiki.prostep.org/"
    "specifications/vec/v220/vec-2.2.0-ontology.ttl",
)

vec_client = VECClient(VEC_TTL_URL)
vec_service = VECService(client=vec_client)
vec_source = VECSemanticSource(vec_service)

# ---------------------------------------------------------------------------
# QUDT source configuration
# ---------------------------------------------------------------------------

QUDT_UNIT_TTL_URL = source_url(
    os.environ,
    "SEMANTIC_HUB_QUDT_UNIT_TTL_URL",
    "https://qudt.org/vocab/unit/",
)

qudt_client = QUDTClient(QUDT_UNIT_TTL_URL)
qudt_service = QUDTService(client=qudt_client)
qudt_source = QUDTSemanticSource(qudt_service)

# ---------------------------------------------------------------------------
# DPPO source configuration
# ---------------------------------------------------------------------------

DPPO_TTL_URL = source_url(
    os.environ,
    "SEMANTIC_HUB_DPPO_TTL_URL",
    "https://liusemweb.github.io/"
    "DPPO/ontology/{module}/0.1/{module}.ttl",
)

dppo_client = DPPOClient(DPPO_TTL_URL)
dppo_service = DPPOService(client=dppo_client)
dppo_source = DPPOSemanticSource(dppo_service)

# ---------------------------------------------------------------------------
# Semantic registry and resolver
# ---------------------------------------------------------------------------

registry = SemanticRegistry()

registry.register(MockSemanticSource())
registry.register(kbl_source)
registry.register(vec_source)
registry.register(qudt_source)
registry.register(dppo_source)

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
    except RuntimeError:
        logger.warning("Resolving '%s' failed", semantic_id, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="The responsible semantic source is currently unavailable.",
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