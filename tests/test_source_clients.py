import pytest

from app.sources.kbl.client import KBLClient
from app.sources.qudt.client import QUDTClient
from app.sources.vec.client import VECClient


CLIENTS = [
    pytest.param(KBLClient, "get_xsd", id="kbl"),
    pytest.param(VECClient, "get_ttl", id="vec"),
    pytest.param(QUDTClient, "get_ttl", id="qudt"),
]


@pytest.mark.parametrize(("client_class", "method_name"), CLIENTS)
def test_client_loads_local_file_url(tmp_path, client_class, method_name):
    content = b"local source content \xc3\xa4"
    path = tmp_path / "source.dat"
    path.write_bytes(content)

    client = client_class(path.as_uri())

    assert getattr(client, method_name)() == content


@pytest.mark.parametrize(("client_class", "method_name"), CLIENTS)
def test_client_raises_runtime_error_for_missing_local_file(
    tmp_path, client_class, method_name
):
    missing = tmp_path / "missing.dat"

    client = client_class(missing.as_uri())

    with pytest.raises(RuntimeError):
        getattr(client, method_name)()