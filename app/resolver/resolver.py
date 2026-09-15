from app.registry.registry import SemanticRegistry


class SemanticResolver:

    def __init__(self, registry: SemanticRegistry):
        self.registry = registry

    def resolve(self, semantic_id: str):

        source = self.registry.get_source(semantic_id)

        if source is None:
            raise ValueError(
                f"No semantic source found for '{semantic_id}'"
            )

        return source.resolve(semantic_id)