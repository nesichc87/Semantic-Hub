import pytest
from pydantic import ValidationError

from app.sources.generic.config_schema import XSDSourceConfig


def kbl_like_config(**overrides):
    config = {
        "id": "kbl",
        "prefix": "kbl:",
        "location": "https://example.org/kbl.xsd",
    }
    config.update(overrides)
    return config


def test_accepts_minimal_config_with_defaults():
    config = XSDSourceConfig.model_validate(kbl_like_config())

    assert config.location == "https://example.org/kbl.xsd"
    assert config.kinds == ["complexType", "simpleType"]
    assert config.documentation is False
    assert config.follow is False
    assert config.import_prefixes == {}
    assert config.license is None


@pytest.mark.parametrize(
    "raw",
    [
        {"id": "kbl", "prefix": "kbl:"},
        kbl_like_config(prefix=""),
        kbl_like_config(kinds=["element"]),
        kbl_like_config(locations=["https://example.org/kbl.xsd"]),
    ],
)
def test_rejects_invalid_config(raw):
    with pytest.raises(ValidationError):
        XSDSourceConfig.model_validate(raw)