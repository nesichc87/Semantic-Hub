"""Safe fetching of external content (ADR-004).

Only http and https URLs are allowed. Host names are resolved and every
address is checked; only globally reachable unicast addresses are
allowed. Pinned connections, redirects, size and time limits and the
content type check are added in later steps.
"""

import http.client
import ipaddress
import socket
import ssl
import time
from collections.abc import Callable
from urllib.parse import urljoin, urlsplit


IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

Resolver = Callable[[str, int], list[str]]
"""Returns the IP addresses (as text) for a host name and port."""
IsAllowed = Callable[[IPAddress], bool]

DEFAULT_PORTS = {"http": 80, "https": 443}


class FetchError(RuntimeError):
    """External content could not be fetched; the source is unavailable."""


class BlockedAddressError(FetchError):
    """The URL or one of the addresses of its host is not allowed."""


def check_url(url: str) -> tuple[str, str, int]:
    """Return scheme, host and port of an allowed URL, else raise BlockedAddressError."""
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    if scheme not in DEFAULT_PORTS:
        raise BlockedAddressError(f"Only http and https URLs are allowed: {url}")
    if parts.username is not None or parts.password is not None:
        # The URL is not repeated here, so that no password ends up in a log.
        raise BlockedAddressError("URLs with credentials are not allowed")
    host = parts.hostname
    if not host:
        raise BlockedAddressError(f"URL has no host: {url}")
    try:
        port = parts.port or DEFAULT_PORTS[scheme]
    except ValueError as exc:
        raise BlockedAddressError(f"URL has an invalid port: {url}") from exc
    return scheme, host, port


def is_allowed_address(address: IPAddress) -> bool:
    """Only globally reachable unicast addresses are allowed."""
    if address.version == 6 and address.ipv4_mapped is not None:
        address = address.ipv4_mapped
    return address.is_global and not address.is_multicast


def system_resolver(host: str, port: int) -> list[str]:
    return [info[4][0] for info in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)]


def resolve_allowed(
    host: str,
    port: int,
    resolver: Resolver = system_resolver,
    is_allowed: IsAllowed = is_allowed_address,
) -> list[IPAddress]:
    """Resolve a host name; every address must be allowed."""
    try:
        answers = resolver(host, port)
    except OSError as exc:  # socket.gaierror is an OSError
        raise FetchError(f"Host name could not be resolved: {host}") from exc
    if not answers:
        raise FetchError(f"Host name could not be resolved: {host}")

    addresses: list[IPAddress] = []
    for answer in answers:
        address = ipaddress.ip_address(answer.split("%", 1)[0])  # drop an IPv6 scope ID
        if not is_allowed(address):
            raise BlockedAddressError(f"Address not allowed for host {host}: {address}")
        if address not in addresses:
            addresses.append(address)
    return addresses

ACCEPT = {
    "turtle": "text/turtle, */*;q=0.1",
    "json-ld": "application/ld+json, application/json;q=0.9, */*;q=0.1",
    "xml": "application/rdf+xml, */*;q=0.1",
    "xsd": "application/xml, text/xml, */*;q=0.1",
    "csv": "text/csv, */*;q=0.1",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, */*;q=0.1",
}

USER_AGENT = "Semantic-Hub/0.2"
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
MAX_BYTES = 50 * 1024 * 1024
TOTAL_TIMEOUT = 120
CHUNK_SIZE = 64 * 1024
HTML_TYPES = {"text/html", "application/xhtml+xml"}


class _PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTP connection to a checked address; the host name is kept for the Host header."""

    def __init__(self, host: str, port: int, address: str, timeout: float):
        super().__init__(host, port, timeout=timeout)
        self._address = address

    def connect(self):
        self.sock = socket.create_connection((self._address, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection to a checked address; SNI and certificate check use the host name."""

    def __init__(self, host: str, port: int, address: str, timeout: float, context: ssl.SSLContext):
        super().__init__(host, port, timeout=timeout, context=context)
        self._address = address

    def connect(self):
        sock = socket.create_connection((self._address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


class SafeFetcher:
    """Fetch function for the generic source types: ``fetcher(location, format) -> bytes``.

    The connection goes to an address that was checked before, so a second
    DNS lookup cannot lead to an internal address (DNS rebinding).
    """

    def __init__(
            self,
            resolver: Resolver = system_resolver,
            is_allowed: IsAllowed = is_allowed_address,
            timeout: float = 30,
            max_redirects: int = 5,
            max_bytes: int = MAX_BYTES,
            total_timeout: float = TOTAL_TIMEOUT,
            clock: Callable[[], float] = time.monotonic,
    ):
        self._resolver = resolver
        self._is_allowed = is_allowed
        self._timeout = timeout
        self._max_redirects = max_redirects
        self._max_bytes = max_bytes
        self._total_timeout = total_timeout
        self._clock = clock
        self._context = ssl.create_default_context()

    def __call__(self, location: str, fmt: str) -> bytes:
        deadline = self._clock() + self._total_timeout
        url = location
        for _ in range(self._max_redirects + 1):
            redirect, body = self._get(url, fmt, deadline)
            if redirect is None:
                return body
            # Every redirect target is checked like a new URL in the next round.
            url = urljoin(url, redirect)
        raise FetchError(f"More than {self._max_redirects} redirects: {location}")

    def _get(self, url: str, fmt: str, deadline: float) -> tuple[str | None, bytes]:
        """One request. Returns the redirect target (or None) and the body."""
        self._check_deadline(deadline, url)
        scheme, host, port = check_url(url)
        addresses = resolve_allowed(host, port, self._resolver, self._is_allowed)

        parts = urlsplit(url)
        target = parts.path or "/"
        if parts.query:
            target += "?" + parts.query
        headers = {"Accept": ACCEPT.get(fmt, "*/*"), "User-Agent": USER_AGENT}

        connection = self._connect(scheme, host, port, addresses)
        try:
            connection.request("GET", target, headers=headers)
            response = connection.getresponse()
            if response.status in REDIRECT_STATUSES:
                redirect = response.getheader("Location")
                if not redirect:
                    raise FetchError(f"HTTP {response.status} without Location: {url}")
                return redirect, b""
            if not 200 <= response.status < 300:
                raise FetchError(f"HTTP {response.status} for {url}")
            content_type = (response.getheader("Content-Type") or "").split(";", 1)[0].strip().lower()
            if content_type in HTML_TYPES:
                raise FetchError(f"HTML page instead of data: {url}")
            return None, self._read_limited(response, url, deadline)
        except (OSError, http.client.HTTPException) as exc:
            raise FetchError(f"Fetching failed: {url}") from exc
        finally:
            connection.close()

    def _read_limited(self, response, url: str, deadline: float) -> bytes:
        """Read in chunks; stop as soon as the size or time limit is exceeded."""
        chunks: list[bytes] = []
        size = 0
        while chunk := response.read(CHUNK_SIZE):
            size += len(chunk)
            if size > self._max_bytes:
                raise FetchError(f"Response larger than {self._max_bytes} bytes: {url}")
            chunks.append(chunk)
            self._check_deadline(deadline, url)
        return b"".join(chunks)

    def _check_deadline(self, deadline: float, url: str) -> None:
        if self._clock() > deadline:
            raise FetchError(f"Total time limit of {self._total_timeout} s exceeded: {url}")

    def _connect(self, scheme: str, host: str, port: int, addresses: list[IPAddress]):
        """Connect to the first reachable checked address."""
        last_error: OSError | None = None
        for address in addresses:
            if scheme == "https":
                connection = _PinnedHTTPSConnection(
                    host, port, str(address), self._timeout, self._context
                )
            else:
                connection = _PinnedHTTPConnection(host, port, str(address), self._timeout)
            try:
                connection.connect()
                return connection
            except OSError as exc:
                connection.close()
                last_error = exc
        raise FetchError(f"Connection failed: {host}") from last_error