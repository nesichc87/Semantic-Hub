import pytest
from pydantic import ValidationError

from app.sources.generic.config_schema import TableSourceConfig


def ucum_like_config(**overrides):
    config = {
        "id": "ucum",
        "prefix": "ucum:",
        "location": "https://example.org/ucum.xlsx",
        "format": "xlsx",
        "columns": {"id": "UCUM_CODE"},
    }
    config.update(overrides)
    return config


def test_accepts_minimal_config_with_defaults():
    config = TableSourceConfig.model_validate(ucum_like_config())

    assert config.format == "xlsx"
    assert config.header_row == 1
    assert config.sheet is None
    assert config.delimiter is None
    assert config.license is None
    assert config.columns.id == "UCUM_CODE"
    assert config.columns.name is None
    assert config.columns.description is None
    assert config.columns.equivalence is None


@pytest.mark.parametrize(
    "raw",
    [
        ucum_like_config(columns={"name": "Name"}),
        ucum_like_config(columns={"id": ""}),
        ucum_like_config(columns={"id": "Code", "extra": ["Note"]}),
        ucum_like_config(header_row=0),
        ucum_like_config(format="ods"),
        ucum_like_config(format="csv", delimiter=";;"),
        ucum_like_config(locations=["https://example.org/ucum.xlsx"]),
    ],
)
def test_rejects_invalid_config(raw):
    with pytest.raises(ValidationError):
        TableSourceConfig.model_validate(raw)