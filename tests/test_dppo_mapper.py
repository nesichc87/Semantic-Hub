from app.models.semantic import SemanticConcept, SemanticProperty
from app.sources.dppo.mapper import map_dppo_class


def test_map_dppo_class_maps_name_description_properties_and_provenance():
    result = {
        "name": "ComponentDPP",
        "description": "A DPP for a component.",
        "properties": [
            {
                "semantic_id": "dppo:dpp-odp:describes",
                "name": "describes",
                "description": "Links a DPP to its product.",
                "data_type": "dppo:dpp-odp:Product",
            },
        ],
    }

    concept = map_dppo_class("dppo:dpp-core:ComponentDPP", result)

    assert concept == SemanticConcept(
        semantic_id="dppo:dpp-core:ComponentDPP",
        source="dppo",
        name="ComponentDPP",
        description="A DPP for a component.",
        properties=[
            SemanticProperty(
                semantic_id="dppo:dpp-odp:describes",
                name="describes",
                description="Links a DPP to its product.",
                data_type="dppo:dpp-odp:Product",
                provenance={
                    "source": "dppo",
                    "source_reference": "dppo:dpp-odp:describes",
                },
            ),
        ],
        provenance={
            "source": "dppo",
            "source_reference": "dppo:dpp-core:ComponentDPP",
        },
    )