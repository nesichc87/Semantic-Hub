import ipaddress
import socket

import pytest

from app.fetch.safe_fetcher import (
    BlockedAddressError,
    FetchError,
    check_url,
    is_allowed_address,
    resolve_allowed,
)


def test_errors_are_runtime_errors():
    assert issubclass(FetchError, RuntimeError)
    assert issubclass(BlockedAddressError, FetchError)


def test_check_url_returns_scheme_host_and_port():
    assert check_url("https://Example.org/x.ttl") == ("https", "example.org", 443)
    assert check_url("http://example.org:8080/x") == ("http", "example.org", 8080)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.org/x.ttl",
        "https:///x.ttl",
        "https://user:secret@example.org/x.ttl",
        "example.org/x.ttl",
    ],
)
def test_check_url_rejects_disallowed_urls(url):
    with pytest.raises(BlockedAddressError):
        check_url(url)


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "100.64.0.1",
        "224.0.0.1",
        "0.0.0.0",
        "::1",
        "fe80::1",
        "fc00::1",
        "ff02::1",
        "::ffff:127.0.0.1",
    ],
)
def test_blocks_internal_addresses(address):
    assert not is_allowed_address(ipaddress.ip_address(address))


@pytest.mark.parametrize("address", ["93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946"])
def test_allows_public_addresses(address):
    assert is_allowed_address(ipaddress.ip_address(address))


def fake_resolver(answers: dict[str, list[str]]):
    def resolve(host: str, port: int) -> list[str]:
        if host not in answers:
            raise socket.gaierror("Name or service not known")
        return answers[host]

    return resolve


def test_resolve_allowed_returns_addresses():
    resolver = fake_resolver({"example.org": ["93.184.216.34"]})

    assert resolve_allowed("example.org", 443, resolver) == [
        ipaddress.ip_address("93.184.216.34")
    ]


def test_resolve_rejects_if_any_address_is_internal():
    resolver = fake_resolver({"mixed.example": ["93.184.216.34", "127.0.0.1"]})

    with pytest.raises(BlockedAddressError):
        resolve_allowed("mixed.example", 443, resolver)


def test_resolve_failure_is_fetch_error_but_not_blocked():
    with pytest.raises(FetchError) as info:
        resolve_allowed("missing.example", 443, fake_resolver({}))

    assert not isinstance(info.value, BlockedAddressError)