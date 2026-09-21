from urllib.request import Request, urlopen


class KBLClient:
    """
    Client for accessing KBL resources.
    """

    def __init__(self, xsd_url: str, timeout: int = 30):
        self.xsd_url = xsd_url
        self.timeout = timeout

    def get_xsd(self) -> bytes:
        """
        Download the KBL XSD and return its raw content.
        """

        request = Request(
            self.xsd_url,
            headers={
                "User-Agent": "Semantic-Hub/0.1",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read()

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load KBL XSD from '{self.xsd_url}'"
            ) from exc