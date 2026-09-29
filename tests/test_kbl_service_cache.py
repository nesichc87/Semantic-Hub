from app.sources.kbl.service import KBLService


class CountingClient:
    """Fake KBL client that counts XSD downloads."""

    def __init__(self):
        self.calls = 0

    def get_xsd(self) -> bytes:
        self.calls += 1
        return b"<xsd/>"


class FakeParser:
    """Fake KBL parser that returns a placeholder root."""

    def parse(self, content: bytes):
        return object()

    def suggest_types(self, root, query: str) -> list[str]:
        return []


def test_xsd_is_loaded_only_once_for_repeated_calls():
    client = CountingClient()
    service = KBLService(client=client, parser=FakeParser())

    service.suggest_types("Component")
    service.suggest_types("Part")

    assert client.calls == 1