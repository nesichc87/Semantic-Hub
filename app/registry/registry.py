from app.sources.base import SemanticSource


class SemanticRegistry:
    def __init__(self):
        self._sources: list[SemanticSource] = []

    def register(self, source: SemanticSource):
        self._sources.append(source)

    def get_source(self, semantic_id: str) -> SemanticSource | None:
        for source in self._sources:
            if source.can_resolve(semantic_id):
                return source

        return None

    def suggest(self, query: str) -> list[str]:
        """
        Collect semantic identifier suggestions from all registered sources.
        """

        results = []

        for source in self._sources:
            results.extend(source.suggest(query))

        return sorted(results)