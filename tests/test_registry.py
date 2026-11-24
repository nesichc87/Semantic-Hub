import pytest

from app.registry.registry import SemanticRegistry
from app.sources.base import SemanticSource


class FakeSource(SemanticSource):
    def __init__(self, suggestions: list[str], prefix: str | None = None):
        self.suggestions = suggestions
        self.prefix = prefix
        self.queries = []

    def can_resolve(self, semantic_id: str) -> bool:
        return self.prefix is not None and semantic_id.startswith(self.prefix)

    def resolve(self, semantic_id: str):
        raise NotImplementedError

    def suggest(self, query: str) -> list[str]:
        self.queries.append(query)
        return self.suggestions


class FailingSource(FakeSource):
    def suggest(self, query: str) -> list[str]:
        raise RuntimeError("source not reachable")


def test_suggest_keeps_source_order_and_order_within_each_source():
    registry = SemanticRegistry()
    registry.register("b", FakeSource(["b:second", "b:first"]))
    registry.register("a", FakeSource(["a:only"]))

    assert registry.suggest("query") == ["b:second", "b:first", "a:only"]


def test_suggest_passes_query_to_all_sources():
    first = FakeSource([])
    second = FakeSource([])
    registry = SemanticRegistry()
    registry.register("first", first)
    registry.register("second", second)

    registry.suggest("metre")

    assert first.queries == ["metre"]
    assert second.queries == ["metre"]


def test_suggest_skips_failing_source_and_keeps_the_others():
    registry = SemanticRegistry()
    registry.register("a", FakeSource(["a:first"]))
    registry.register("b", FailingSource([]))
    registry.register("c", FakeSource(["c:last"]))

    assert registry.suggest("query") == ["a:first", "c:last"]


def test_suggest_logs_failing_source(caplog):
    registry = SemanticRegistry()
    registry.register("broken", FailingSource([]))

    registry.suggest("query")

    assert "broken" in caplog.text


def test_source_ids_in_registration_order():
    registry = SemanticRegistry()
    registry.register("kbl", FakeSource([]))
    registry.register("vec", FakeSource([]))

    assert registry.source_ids() == ["kbl", "vec"]


def test_register_rejects_duplicate_id():
    registry = SemanticRegistry()
    registry.register("kbl", FakeSource([]))

    with pytest.raises(ValueError):
        registry.register("kbl", FakeSource([]))
    assert registry.source_ids() == ["kbl"]


def test_get_source_returns_first_source_that_can_resolve():
    first = FakeSource([], prefix="x:")
    registry = SemanticRegistry()
    registry.register("first", first)
    registry.register("second", FakeSource([], prefix="x:"))
    registry.register("other", FakeSource([], prefix="y:"))

    assert registry.get_source("x:Thing") is first
    assert registry.get_source("z:Thing") is None

def test_replace_keeps_position():
    registry = SemanticRegistry()
    registry.register("a", FakeSource(["a:x"]))
    registry.register("b", FakeSource(["b:old"]))
    registry.register("c", FakeSource(["c:x"]))

    registry.replace("b", FakeSource(["b:new"]))

    assert registry.source_ids() == ["a", "b", "c"]
    assert registry.suggest("query") == ["a:x", "b:new", "c:x"]


def test_unregister_removes_source():
    registry = SemanticRegistry()
    registry.register("a", FakeSource([], prefix="a:"))
    registry.register("b", FakeSource([], prefix="b:"))

    registry.unregister("a")

    assert registry.source_ids() == ["b"]
    assert registry.get_source("a:Thing") is None


@pytest.mark.parametrize(
    "method, args",
    [
        ("replace", ("missing", FakeSource([]))),
        ("unregister", ("missing",)),
    ],
)
def test_unknown_source_id_raises_value_error(method, args):
    registry = SemanticRegistry()
    registry.register("a", FakeSource([]))

    with pytest.raises(ValueError):
        getattr(registry, method)(*args)
    assert registry.source_ids() == ["a"]


class UnregisteringSource(FakeSource):
    """Unregisters another source while suggest is running."""

    def __init__(self, registry: SemanticRegistry, other_id: str):
        super().__init__(["first:x"])
        self.registry = registry
        self.other_id = other_id

    def suggest(self, query: str) -> list[str]:
        self.registry.unregister(self.other_id)
        return super().suggest(query)


def test_running_suggest_is_not_affected_by_unregister():
    registry = SemanticRegistry()
    registry.register("first", UnregisteringSource(registry, "second"))
    registry.register("second", FakeSource(["second:x"]))

    assert registry.suggest("query") == ["first:x", "second:x"]
    assert registry.source_ids() == ["first"]