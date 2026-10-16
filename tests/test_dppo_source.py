from app.sources.dppo.source import DPPOSemanticSource


class FakeDPPOService:
    def get_class(self, semantic_id: str) -> dict:
        return {
            "name": "ComponentDPP",
            "description": "A DPP for a component.",
            "properties": [],
        }

    def suggest_classes(self, query: str) -> list[str]:
        return [f"dppo:dpp-core:{query}"]


def test_can_resolve_only_dppo_ids():
    source = DPPOSemanticSource(FakeDPPOService())

    assert source.can_resolve("dppo:dpp-core:ComponentDPP")
    assert not source.can_resolve("vec:PartVersion")
    assert not source.can_resolve("qudt:unit:M")


def test_resolve_maps_service_result():
    source = DPPOSemanticSource(FakeDPPOService())

    concept = source.resolve("dppo:dpp-core:ComponentDPP")

    assert concept.semantic_id == "dppo:dpp-core:ComponentDPP"
    assert concept.source == "dppo"
    assert concept.name == "ComponentDPP"
    assert concept.description == "A DPP for a component."


def test_suggest_delegates_to_service():
    source = DPPOSemanticSource(FakeDPPOService())

    assert source.suggest("ComponentDPP") == ["dppo:dpp-core:ComponentDPP"]