from urllib.request import Request, urlopen


MODULE_PLACEHOLDER = "{module}"


class DPPOClient:
    """
    Client for accessing the modules of the Digital Product Passport
    Ontology (DPPO).

    The modules are loaded from a URL template in which the placeholder
    '{module}' is replaced by the module name, e.g. 'dpp-core'.
    """

    def __init__(self, ttl_url_template: str, timeout: int = 30):
        if MODULE_PLACEHOLDER not in ttl_url_template:
            raise ValueError(
                f"DPPO URL template must contain '{MODULE_PLACEHOLDER}': "
                f"'{ttl_url_template}'"
            )

        self.ttl_url_template = ttl_url_template
        self.timeout = timeout

    def get_ttl(self, module: str) -> bytes:
        """
        Download one DPPO module (Turtle) and return its raw content.
        """

        url = self.ttl_url_template.replace(MODULE_PLACEHOLDER, module)

        request = Request(
            url,
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
                f"Failed to load DPPO module '{module}' from '{url}'"
            ) from exc