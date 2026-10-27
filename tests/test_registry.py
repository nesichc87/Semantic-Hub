from app.registry.registry import SemanticRegistry
from app.sources.base import SemanticSource


class FakeSource(SemanticSource):
    def __init__(self, suggestions: list[str]):
        self.suggestions = suggestions
        self.queries = []

    def can_resolve(self, semantic_id: str) -> bool:
        return False

    def resolve(self, semantic_id: str):
        raise NotImplementedError

    def suggest(self, query: str) -> list[str]:
        self.queries.append(query)
        return self.suggestions


def test_suggest_keeps_source_order_and_order_within_each_source():
    registry = SemanticRegistry()
    registry.register(FakeSource(["b:second", "b:first"]))
    registry.register(FakeSource(["a:only"]))

    assert registry.suggest("query") == ["b:second", "b:first", "a:only"]


def test_suggest_passes_query_to_all_sources():
    first = FakeSource([])
    second = FakeSource([])
    registry = SemanticRegistry()
    registry.register(first)
    registry.register(second)

    registry.suggest("metre")

    assert first.queries == ["metre"]
    assert second.queries == ["metre"]

class FailingSource(FakeSource):
    def suggest(self, query: str) -> list[str]:
        raise RuntimeError("source not reachable")


def test_suggest_skips_failing_source_and_keeps_the_others():
    registry = SemanticRegistry()
    registry.register(FakeSource(["a:first"]))
    registry.register(FailingSource([]))
    registry.register(FakeSource(["c:last"]))

    assert registry.suggest("query") == ["a:first", "c:last"]


def test_suggest_logs_failing_source(caplog):
    registry = SemanticRegistry()
    registry.register(FailingSource([]))

    registry.suggest("query")

    assert "FailingSource" in caplog.text