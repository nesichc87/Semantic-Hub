from urllib.request import Request, urlopen


class VECClient:
    """
    Client for accessing VEC resources.
    """

    def __init__(self, ttl_url: str, timeout: int = 30):
        self.ttl_url = ttl_url
        self.timeout = timeout

    def get_ttl(self) -> bytes:
        """
        Download the VEC ontology (Turtle) and return its raw content.
        """

        request = Request(
            self.ttl_url,
            headers={
                "Accept": "text/turtle",
                "User-Agent": "Semantic-Hub/0.1",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read()

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load VEC ontology from '{self.ttl_url}'"
            ) from exc