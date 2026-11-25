import ipaddress
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.fetch.safe_fetcher import (
    BlockedAddressError,
    FetchError,
    SafeFetcher,
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

class LocalServer:
    """Test HTTP server on 127.0.0.1 with configurable routes."""

    def __init__(self):
        self.routes: dict[str, tuple[int, dict[str, str], bytes]] = {}
        self.requests: list[tuple[str, dict[str, str]]] = []
        self.port = 0


@pytest.fixture
def server():
    state = LocalServer()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            state.requests.append((self.path, dict(self.headers)))
            status, headers, body = state.routes.get(self.path, (404, {}, b"not found"))
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    state.port = httpd.server_address[1]
    thread = threading.Thread(
        target=httpd.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    yield state
    httpd.shutdown()
    httpd.server_close()


LOOPBACK = ipaddress.ip_address("127.0.0.1")


def local_fetcher(**options):
    """Fetcher for the local test server: only 127.0.0.1 is allowed.

    data.example and mirror.example resolve to 127.0.0.1,
    internal.example resolves to 127.0.0.2, which is not allowed.
    """
    return SafeFetcher(
        resolver=fake_resolver(
            {
                "data.example": ["127.0.0.1"],
                "mirror.example": ["127.0.0.1"],
                "internal.example": ["127.0.0.2"],
            }
        ),
        is_allowed=lambda address: address == LOOPBACK,
        **options,
    )


def test_fetches_body_from_resolved_address_with_original_host(server):
    server.routes["/vocab.ttl"] = (200, {"Content-Type": "text/turtle"}, b"@prefix ex: <x> .")

    body = local_fetcher()(f"http://data.example:{server.port}/vocab.ttl", "turtle")

    assert body == b"@prefix ex: <x> ."
    path, headers = server.requests[0]
    assert path == "/vocab.ttl"
    assert headers["Host"] == f"data.example:{server.port}"
    assert "text/turtle" in headers["Accept"]
    assert "Semantic-Hub" in headers["User-Agent"]


def test_http_error_status_is_fetch_error(server):
    with pytest.raises(FetchError) as info:
        local_fetcher()(f"http://data.example:{server.port}/missing.ttl", "turtle")

    assert not isinstance(info.value, BlockedAddressError)


def test_blocked_address_is_never_contacted(server):
    fetcher = SafeFetcher(resolver=fake_resolver({"data.example": ["127.0.0.1"]}))

    with pytest.raises(BlockedAddressError):
        fetcher(f"http://data.example:{server.port}/vocab.ttl", "turtle")
    assert server.requests == []


def test_file_url_is_rejected():
    with pytest.raises(BlockedAddressError):
        SafeFetcher()("file:///etc/passwd", "turtle")

TURTLE = (200, {"Content-Type": "text/turtle"}, b"@prefix ex: <x> .")


def test_follows_relative_redirect(server):
    server.routes["/old.ttl"] = (302, {"Location": "/vocab.ttl"}, b"")
    server.routes["/vocab.ttl"] = TURTLE

    body = local_fetcher()(f"http://data.example:{server.port}/old.ttl", "turtle")

    assert body == b"@prefix ex: <x> ."
    assert [path for path, _ in server.requests] == ["/old.ttl", "/vocab.ttl"]


def test_follows_absolute_redirect_to_other_allowed_host(server):
    server.routes["/old.ttl"] = (
        301,
        {"Location": f"http://mirror.example:{server.port}/vocab.ttl"},
        b"",
    )
    server.routes["/vocab.ttl"] = TURTLE

    local_fetcher()(f"http://data.example:{server.port}/old.ttl", "turtle")

    assert server.requests[1][1]["Host"] == f"mirror.example:{server.port}"


@pytest.mark.parametrize(
    "location",
    ["http://internal.example:{port}/secret", "file:///etc/passwd"],
)
def test_redirect_to_disallowed_target_is_blocked_before_contact(server, location):
    server.routes["/old.ttl"] = (302, {"Location": location.format(port=server.port)}, b"")

    with pytest.raises(BlockedAddressError):
        local_fetcher()(f"http://data.example:{server.port}/old.ttl", "turtle")
    assert [path for path, _ in server.requests] == ["/old.ttl"]


def test_too_many_redirects_is_fetch_error(server):
    server.routes["/loop"] = (302, {"Location": "/loop"}, b"")

    with pytest.raises(FetchError) as info:
        local_fetcher()(f"http://data.example:{server.port}/loop", "turtle")

    assert not isinstance(info.value, BlockedAddressError)
    assert len(server.requests) == 6  # first request plus 5 redirects


def test_redirect_without_location_is_fetch_error(server):
    server.routes["/old.ttl"] = (302, {}, b"")

    with pytest.raises(FetchError):
        local_fetcher()(f"http://data.example:{server.port}/old.ttl", "turtle")

def fake_clock(*values: float):
    """Returns the given times in order, then keeps returning the last one."""
    remaining = list(values)

    def clock() -> float:
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    return clock


def test_body_up_to_limit_is_accepted(server):
    server.routes["/small.ttl"] = (200, {}, b"x" * 10)

    body = local_fetcher(max_bytes=10)(f"http://data.example:{server.port}/small.ttl", "turtle")

    assert body == b"x" * 10


def test_body_over_limit_is_fetch_error(server):
    server.routes["/big.ttl"] = (200, {}, b"x" * 11)

    with pytest.raises(FetchError, match="larger than"):
        local_fetcher(max_bytes=10)(f"http://data.example:{server.port}/big.ttl", "turtle")


def test_total_time_limit_is_fetch_error(server):
    server.routes["/vocab.ttl"] = TURTLE

    with pytest.raises(FetchError, match="time limit"):
        local_fetcher(clock=fake_clock(0.0, 121.0))(
            f"http://data.example:{server.port}/vocab.ttl", "turtle"
        )


@pytest.mark.parametrize("content_type", ["text/html; charset=utf-8", "application/xhtml+xml"])
def test_html_page_is_fetch_error(server, content_type):
    server.routes["/page"] = (200, {"Content-Type": content_type}, b"<html></html>")

    with pytest.raises(FetchError, match="HTML"):
        local_fetcher()(f"http://data.example:{server.port}/page", "turtle")


@pytest.mark.parametrize("content_type", ["text/plain", "application/octet-stream"])
def test_other_content_types_are_accepted(server, content_type):
    server.routes["/raw.ttl"] = (200, {"Content-Type": content_type}, b"@prefix ex: <x> .")

    assert local_fetcher()(f"http://data.example:{server.port}/raw.ttl", "turtle")