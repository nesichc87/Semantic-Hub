from app.formatter.original import OriginalFormatter
from app.models.semantic import SemanticConcept, SemanticProperty


def test_original_formatter():
    concept = SemanticConcept(
        semantic_id="kbl:Component",
        source="kbl",
        name="Component",
        description="A KBL component.",
        properties=[
            SemanticProperty(
                semantic_id="kbl:Component:Part_number",
                name="Part_number",
                data_type="xs:string",
            )
        ],
        provenance={
            "source": "kbl",
            "source_reference": "kbl:Component",
        },
    )

    formatter = OriginalFormatter()

    result = formatter.format(concept)

    assert result["semantic_id"] == "kbl:Component"
    assert result["source"] == "kbl"
    assert result["name"] == "Component"
    assert result["description"] == "A KBL component."

    assert len(result["properties"]) == 1
    assert result["properties"][0]["name"] == "Part_number"
    assert result["properties"][0]["data_type"] == "xs:string"

    assert result["provenance"]["source"] == "kbl"

def test_original_formatter_includes_concept_data_type():
    concept = SemanticConcept(
        semantic_id="kbl:SI_unit_name",
        source="kbl",
        name="SI_unit_name",
        data_type="xs:string",
    )

    result = OriginalFormatter().format(concept)

    assert result["data_type"] == "xs:string"
    assert result["properties"] == []


def test_original_formatter_concept_data_type_defaults_to_none():
    concept = SemanticConcept(
        semantic_id="kbl:Component",
        source="kbl",
        name="Component",
    )

    result = OriginalFormatter().format(concept)

    assert result["data_type"] is None