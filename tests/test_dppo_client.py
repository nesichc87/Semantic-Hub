import pytest

from app.sources.dppo.client import DPPOClient


def test_get_ttl_loads_module_from_url_template(tmp_path):
    (tmp_path / "dpp-core.ttl").write_bytes(b"@prefix ex: <http://example.org/> .")
    client = DPPOClient(tmp_path.as_uri() + "/{module}.ttl")

    assert client.get_ttl("dpp-core") == b"@prefix ex: <http://example.org/> ."


def test_get_ttl_raises_runtime_error_for_missing_module(tmp_path):
    client = DPPOClient(tmp_path.as_uri() + "/{module}.ttl")

    with pytest.raises(RuntimeError):
        client.get_ttl("dpp-core")


def test_url_template_without_placeholder_is_rejected():
    with pytest.raises(ValueError):
        DPPOClient("https://example.org/dppo.ttl")