from app.sources.kbl.mapper import map_kbl_type


def test_map_simple_type_keeps_base_type_without_properties():
    concept = map_kbl_type(
        "kbl:SI_unit_name",
        {
            "type": "kbl:SI_unit_name",
            "kind": "simple",
            "base_type": "xs:string",
        },
    )

    assert concept.semantic_id == "kbl:SI_unit_name"
    assert concept.name == "SI_unit_name"
    assert concept.data_type == "xs:string"
    assert concept.properties == []


def test_map_complex_type_has_properties_and_no_concept_data_type():
    concept = map_kbl_type(
        "kbl:Component",
        {
            "type": "kbl:Component",
            "kind": "complex",
            "elements": [
                {"name": "Part_number", "type": "xs:string"},
            ],
        },
    )

    assert concept.data_type is None
    assert len(concept.properties) == 1
    assert concept.properties[0].semantic_id == "kbl:Component:Part_number"
    assert concept.properties[0].data_type == "xs:string"