from app.sources.base import SemanticSource
from app.sources.kbl.service import KBLService


class KBLSemanticSource(SemanticSource):
    """
    Semantic source adapter for KBL.
    """

    def __init__(self, service: KBLService):
        self.service = service

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith("kbl:")

    def resolve(self, semantic_id: str):
        type_name = semantic_id

        return self.service.get_type(type_name)