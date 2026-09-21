from fastapi import APIRouter, HTTPException

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


kbl_client = KBLClient(KBL_XSD_URL)
kbl_parser = KBLParser()

kbl_service = KBLService(
    client=kbl_client,
    parser=kbl_parser,
)

kbl_source = KBLSemanticSource(kbl_service)


registry = SemanticRegistry()

registry.register(MockSemanticSource())
registry.register(kbl_source)

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