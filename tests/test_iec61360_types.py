import pytest

from app.formatter.iec61360_types import map_data_type


@pytest.mark.parametrize(
    ("source_type", "expected"),
    [
        ("xs:string", "STRING"),
        ("string", "STRING"),
        ("xs:boolean", "BOOLEAN"),
        ("boolean", "BOOLEAN"),
        ("xs:integer", None),
        ("xs:double", None),
        ("kbl:Numerical_value", None),
        (None, None),
        ("unknown:type", None),
    ],
)
def test_map_data_type(source_type, expected):
    assert map_data_type(source_type) == expected