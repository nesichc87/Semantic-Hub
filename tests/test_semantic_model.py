from app.models.semantic import SemanticConcept, SemanticProperty


def test_create_semantic_concept():
    prop = SemanticProperty(
        semantic_id="kbl:Part_number",
        name="Part number",
        data_type="string",
    )

    concept = SemanticConcept(
        semantic_id="kbl:Component",
        source="kbl",
        name="Component",
        properties=[prop],
    )

    assert concept.semantic_id == "kbl:Component"
    assert concept.source == "kbl"
    assert len(concept.properties) == 1
    assert concept.properties[0].semantic_id == "kbl:Part_number"