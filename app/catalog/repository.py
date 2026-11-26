"""Repository of the source catalog.

Entries use the catalog format {"type": ..., "config": {...}} and are
validated with the source factory, without loading the source.
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.catalog.models import SOURCE_STATUSES, Source
from app.sources.generic.factory import create_source


class CatalogConflictError(ValueError):
    """A source ID or prefix conflicts with an existing or reserved one."""


@dataclass(frozen=True)
class SourceRecord:
    id: str
    type: str
    config: dict
    prefixes: list[str]
    status: str
    status_reason: str | None
    license: str | None
    created_at: datetime
    updated_at: datetime


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _no_fetch(location: str, fmt: str) -> bytes:
    raise RuntimeError("Sources are not loaded when they are added to the catalog")


def _overlaps(first: str, second: str) -> bool:
    """Two prefixes overlap if they are equal or one starts with the other."""
    return first.startswith(second) or second.startswith(first)


class SourceCatalog:

    def __init__(
        self,
        engine: Engine,
        reserved_prefixes: Iterable[str] = (),
        clock: Callable[[], datetime] = _utc_now,
    ):
        self._sessions = sessionmaker(engine, expire_on_commit=False)
        self._reserved = list(reserved_prefixes)
        self._clock = clock

    def add(self, entry: Mapping, license: str | None = None) -> SourceRecord:
        """Validate an entry and store it as a proposed source."""
        source = create_source(entry, _no_fetch)  # raises ValueError if invalid
        source_id = source.config.id
        prefixes = [source.config.prefix, *getattr(source.config, "import_prefixes", {}).values()]

        try:
            with self._sessions.begin() as session:
                if session.get(Source, source_id) is not None:
                    raise CatalogConflictError(f"Source ID already exists: {source_id}")

                taken = [(prefix, "reserved") for prefix in self._reserved]
                for other in session.scalars(select(Source)):
                    taken += [(prefix, other.id) for prefix in other.prefixes]
                for prefix in prefixes:
                    for existing, owner in taken:
                        if _overlaps(prefix, existing):
                            raise CatalogConflictError(
                                f"Prefix '{prefix}' overlaps with '{existing}' ({owner})"
                            )

                now = self._clock()
                row = Source(
                    id=source_id,
                    type=entry["type"],
                    config=dict(entry["config"]),
                    prefixes=prefixes,
                    status="proposed",
                    status_reason=None,
                    license=license,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
                record = _to_record(row)
        except IntegrityError as exc:
            # Another request stored the same source ID in the meantime.
            raise CatalogConflictError(f"Source ID already exists: {source_id}") from exc
        return record

    def get(self, source_id: str) -> SourceRecord | None:
        with self._sessions() as session:
            row = session.get(Source, source_id)
            return _to_record(row) if row is not None else None

    def list_sources(self) -> list[SourceRecord]:
        with self._sessions() as session:
            rows = session.scalars(select(Source).order_by(Source.created_at, Source.id))
            return [_to_record(row) for row in rows]

    def set_status(self, source_id: str, status: str, reason: str | None = None) -> SourceRecord:
        if status not in SOURCE_STATUSES:
            raise ValueError(f"Unknown status: {status}")
        with self._sessions.begin() as session:
            row = session.get(Source, source_id)
            if row is None:
                raise ValueError(f"Unknown source ID: {source_id}")
            row.status = status
            row.status_reason = reason
            row.updated_at = self._clock()
            record = _to_record(row)
        return record


def _aware(value: datetime) -> datetime:
    # SQLite stores no time zone; all times in the catalog are UTC.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _to_record(row: Source) -> SourceRecord:
    return SourceRecord(
        id=row.id,
        type=row.type,
        config=dict(row.config),
        prefixes=list(row.prefixes),
        status=row.status,
        status_reason=row.status_reason,
        license=row.license,
        created_at=_aware(row.created_at),
        updated_at=_aware(row.updated_at),
    )