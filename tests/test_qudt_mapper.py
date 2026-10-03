from app.sources.qudt.mapper import map_qudt_unit


def test_map_unit_has_name_description_and_no_properties():
    concept = map_qudt_unit(
        "qudt:unit:M",
        {
            "name": "Metre",
            "description": "The metric and SI base unit of distance.",
        },
    )

    assert concept.semantic_id == "qudt:unit:M"
    assert concept.source == "qudt"
    assert concept.name == "Metre"
    assert concept.description == "The metric and SI base unit of distance."
    assert concept.properties == []
    assert concept.data_type is None
    assert concept.provenance == {
        "source": "qudt",
        "source_reference": "qudt:unit:M",
    }


def test_map_unit_without_description_keeps_none():
    concept = map_qudt_unit(
        "qudt:unit:M",
        {"name": "Metre", "description": None},
    )

    assert concept.description is None