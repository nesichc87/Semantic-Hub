from app.formatter.iec61360 import IEC61360Formatter
from app.models.semantic import (
    SemanticConcept,
    SemanticProperty,
)


def test_format_semantic_concept():
    concept = SemanticConcept(
        semantic_id="kbl:Component",
        source="kbl",
        name="Component",
        description="A component in a wiring harness.",
        properties=[
            SemanticProperty(
                semantic_id="kbl:Component:Part_number",
                name="Part_number",
                description="Identifier of the component.",
                data_type="xs:string",
                unit=None,
                provenance={
                    "source": "kbl",
                    "source_reference": "kbl:Component",
                },
            )
        ],
        provenance={
            "source": "kbl",
            "source_reference": "kbl:Component",
        },
    )

    formatter = IEC61360Formatter()

    result = formatter.format(concept)

    assert result.semantic_id == "kbl:Component"
    assert result.preferred_name == "Component"
    assert result.definition == "A component in a wiring harness."
    assert result.source_of_definition == "kbl"

    assert len(result.properties) == 1

    prop = result.properties[0]

    assert prop.semantic_id == "kbl:Component:Part_number"
    assert prop.preferred_name == "Part_number"
    assert prop.definition == "Identifier of the component."
    assert prop.data_type == "STRING"
    assert prop.unit is None
    assert prop.source_of_definition == "kbl"

def test_format_concept_without_optional_fields():
    concept = SemanticConcept(
        semantic_id="kbl:Example",
        source="kbl",
        name="Example",
    )

    formatter = IEC61360Formatter()

    result = formatter.format(concept)

    assert result.semantic_id == "kbl:Example"
    assert result.preferred_name == "Example"
    assert result.definition is None
    assert result.source_of_definition is None
    assert result.properties == []

def test_format_property_with_unsupported_data_type_returns_none():
    concept = SemanticConcept(
        semantic_id="kbl:Component",
        source="kbl",
        name="Component",
        properties=[
            SemanticProperty(
                semantic_id="kbl:Component:Mass_information",
                name="Mass_information",
                data_type="kbl:Numerical_value",
            )
        ],
    )

    formatter = IEC61360Formatter()

    result = formatter.format(concept)

    assert len(result.properties) == 1
    assert result.properties[0].semantic_id == (
        "kbl:Component:Mass_information"
    )
    assert result.properties[0].data_type is None