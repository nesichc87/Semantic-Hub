"""Safe fetching of external content (ADR-004).

Only http and https URLs are allowed. Host names are resolved and every
address is checked; only globally reachable unicast addresses are
allowed. Pinned connections, redirects, size and time limits and the
content type check are added in later steps.
"""

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlsplit


IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

Resolver = Callable[[str, int], list[str]]
"""Returns the IP addresses (as text) for a host name and port."""

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


def resolve_allowed(host: str, port: int, resolver: Resolver = system_resolver) -> list[IPAddress]:
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
        if not is_allowed_address(address):
            raise BlockedAddressError(f"Address not allowed for host {host}: {address}")
        if address not in addresses:
            addresses.append(address)
    return addresses