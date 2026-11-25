import hashlib
import json
from datetime import datetime, timezone

import pytest

from app.fetch.cache import SourceCache


LOCATION = "https://example.org/vocab.ttl"


class CountingFetch:
    def __init__(self, data: bytes = b"v1", failures: int = 0):
        self.data = data
        self.failures = failures
        self.calls = []

    def __call__(self, location: str, fmt: str) -> bytes:
        self.calls.append((location, fmt))
        if self.failures:
            self.failures -= 1
            raise RuntimeError("source unavailable")
        return self.data


def fixed_clock() -> datetime:
    return datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)


def test_first_load_fetches_and_stores_with_metadata(tmp_path):
    cache = SourceCache(tmp_path, clock=fixed_clock)

    assert cache.fetcher("qudt", CountingFetch(b"v1"))(LOCATION, "turtle") == b"v1"

    entry = cache.get("qudt", LOCATION)
    assert entry.data == b"v1"
    assert entry.location == LOCATION
    assert entry.format == "turtle"
    assert entry.fetched_at == "2026-11-25T12:00:00+00:00"
    assert entry.sha256 == hashlib.sha256(b"v1").hexdigest()
    assert entry.size == 2


def test_after_restart_cache_is_used_without_fetching(tmp_path):
    SourceCache(tmp_path).fetcher("qudt", CountingFetch(b"v1"))(LOCATION, "turtle")
    fetch = CountingFetch(b"v2")

    body = SourceCache(tmp_path).fetcher("qudt", fetch)(LOCATION, "turtle")

    assert body == b"v1"
    assert fetch.calls == []


def test_refresh_fetches_and_replaces_cached_state(tmp_path):
    cache = SourceCache(tmp_path)
    cache.fetcher("qudt", CountingFetch(b"v1"))(LOCATION, "turtle")

    body = cache.fetcher("qudt", CountingFetch(b"v2"), refresh=True)(LOCATION, "turtle")

    assert body == b"v2"
    assert cache.get("qudt", LOCATION).data == b"v2"


def test_failed_refresh_keeps_previous_state(tmp_path):
    cache = SourceCache(tmp_path)
    cache.fetcher("qudt", CountingFetch(b"v1"))(LOCATION, "turtle")

    with pytest.raises(RuntimeError):
        cache.fetcher("qudt", CountingFetch(failures=1), refresh=True)(LOCATION, "turtle")

    assert cache.get("qudt", LOCATION).data == b"v1"


def test_sources_and_locations_are_cached_separately(tmp_path):
    cache = SourceCache(tmp_path)
    cache.fetcher("a", CountingFetch(b"a1"))("https://example.org/1", "turtle")
    cache.fetcher("a", CountingFetch(b"a2"))("https://example.org/2", "turtle")
    cache.fetcher("b", CountingFetch(b"b1"))("https://example.org/1", "turtle")

    assert cache.get("a", "https://example.org/1").data == b"a1"
    assert cache.get("a", "https://example.org/2").data == b"a2"
    assert cache.get("b", "https://example.org/1").data == b"b1"


def test_get_returns_none_when_not_cached(tmp_path):
    assert SourceCache(tmp_path).get("qudt", LOCATION) is None


@pytest.mark.parametrize("source_id", ["../evil", "a/b", "a\\b", "", "Upper", "a b"])
def test_rejects_unsafe_source_id(tmp_path, source_id):
    with pytest.raises(ValueError):
        SourceCache(tmp_path).get(source_id, LOCATION)


def test_only_data_and_metadata_files_inside_source_folder(tmp_path):
    SourceCache(tmp_path).fetcher("qudt", CountingFetch(b"v1"))(LOCATION, "turtle")

    key = hashlib.sha256(LOCATION.encode("utf-8")).hexdigest()
    files = sorted(
        path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()
    )
    assert files == [f"qudt/{key}.data", f"qudt/{key}.json"]
    metadata = json.loads((tmp_path / "qudt" / f"{key}.json").read_text(encoding="utf-8"))
    assert metadata["location"] == LOCATION