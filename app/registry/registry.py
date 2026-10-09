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

        Results are returned in registration order of the sources.
        The order within each source is kept, so sources can rank
        their own suggestions.
        """

        results = []

        for source in self._sources:
            results.extend(source.suggest(query))

        return results