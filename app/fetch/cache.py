"""File cache for raw source data (ADR-003).

One entry per source and location:
``<root>/<source_id>/<sha256 of location>.data`` plus a ``.json`` file with
location, format, fetch time (UTC), SHA-256 and size. Only the latest state
is kept, and it is replaced only after a successful fetch. Files are written
atomically (temporary file, then ``os.replace``).
"""

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


Fetch = Callable[[str, str], bytes]
"""Returns the raw data for a location; arguments are location and format."""

SOURCE_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*")


@dataclass(frozen=True)
class CacheEntry:
    data: bytes
    location: str
    format: str
    fetched_at: str
    sha256: str
    size: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceCache:

    def __init__(self, root: Path, clock: Callable[[], datetime] = _utc_now):
        self._root = Path(root)
        self._clock = clock

    def get(self, source_id: str, location: str) -> CacheEntry | None:
        """Cached state for a source and location, or None."""
        data_path, metadata_path = self._paths(source_id, location)
        if not data_path.is_file() or not metadata_path.is_file():
            return None
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return CacheEntry(data=data_path.read_bytes(), **metadata)

    def put(self, source_id: str, location: str, fmt: str, data: bytes) -> CacheEntry:
        """Store data as the latest state; data first, metadata last."""
        data_path, metadata_path = self._paths(source_id, location)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        entry = CacheEntry(
            data=data,
            location=location,
            format=fmt,
            fetched_at=self._clock().isoformat(),
            sha256=hashlib.sha256(data).hexdigest(),
            size=len(data),
        )
        metadata = {key: value for key, value in asdict(entry).items() if key != "data"}
        _write_atomic(data_path, data)
        _write_atomic(metadata_path, json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"))
        return entry

    def fetcher(self, source_id: str, fetch: Fetch, refresh: bool = False) -> Fetch:
        """Fetch function that reads through the cache.

        Without ``refresh`` the cached state is used if present; otherwise
        (and always with ``refresh``) ``fetch`` is called and its result
        stored. A failing fetch is raised and leaves the cache unchanged.
        """
        self._check_source_id(source_id)

        def cached_fetch(location: str, fmt: str) -> bytes:
            if not refresh:
                entry = self.get(source_id, location)
                if entry is not None:
                    return entry.data
            data = fetch(location, fmt)
            self.put(source_id, location, fmt, data)
            return data

        return cached_fetch

    def _paths(self, source_id: str, location: str) -> tuple[Path, Path]:
        self._check_source_id(source_id)
        key = hashlib.sha256(location.encode("utf-8")).hexdigest()
        folder = self._root / source_id
        return folder / f"{key}.data", folder / f"{key}.json"

    @staticmethod
    def _check_source_id(source_id: str) -> None:
        # Source IDs come from users later; they must not lead out of the cache folder.
        if not SOURCE_ID_PATTERN.fullmatch(source_id):
            raise ValueError(f"Invalid source ID for the cache: {source_id!r}")


def _write_atomic(path: Path, content: bytes) -> None:
    descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(descriptor, "wb") as file:
            file.write(content)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise