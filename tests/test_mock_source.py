from app.models.semantic import SemanticConcept
from app.sources.mock import MockSemanticSource


def test_mock_source_resolve_returns_semantic_concept():
    source = MockSemanticSource()

    concept = source.resolve("mock:123")

    assert isinstance(concept, SemanticConcept)
    assert concept.semantic_id == "mock:123"
    assert concept.source == "mock"
    assert concept.name == "Example semantic concept"