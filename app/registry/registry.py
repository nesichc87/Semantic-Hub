import logging
import threading

from app.sources.base import SemanticSource


logger = logging.getLogger(__name__)


class SemanticRegistry:
    """Registered semantic sources, each identified by a source ID.

    The sources are kept in an immutable tuple. A change builds a new
    tuple under a lock and swaps it in; readers work on the tuple that
    was current when they started, without locking.
    """

    def __init__(self):
        self._sources: tuple[tuple[str, SemanticSource], ...] = ()
        self._lock = threading.Lock()

    def register(self, source_id: str, source: SemanticSource) -> None:
        """Append a source. Raises ValueError if the source ID is already registered."""
        with self._lock:
            if any(existing == source_id for existing, _ in self._sources):
                raise ValueError(f"Source ID already registered: {source_id}")
            self._sources = (*self._sources, (source_id, source))

    def replace(self, source_id: str, source: SemanticSource) -> None:
        """Replace a source at its position. Raises ValueError for an unknown source ID."""
        with self._lock:
            index = self._index_of(source_id)
            sources = list(self._sources)
            sources[index] = (source_id, source)
            self._sources = tuple(sources)

    def unregister(self, source_id: str) -> None:
        """Remove a source. Raises ValueError for an unknown source ID."""
        with self._lock:
            index = self._index_of(source_id)
            self._sources = self._sources[:index] + self._sources[index + 1:]

    def _index_of(self, source_id: str) -> int:
        for index, (existing, _) in enumerate(self._sources):
            if existing == source_id:
                return index
        raise ValueError(f"Unknown source ID: {source_id}")

    def source_ids(self) -> list[str]:
        """Source IDs in registration order."""
        return [source_id for source_id, _ in self._sources]

    def get_source(self, semantic_id: str) -> SemanticSource | None:
        for _, source in self._sources:
            if source.can_resolve(semantic_id):
                return source

        return None

    def suggest(self, query: str) -> list[str]:
        """
        Collect semantic identifier suggestions from all registered sources.

        Results are returned in registration order of the sources.
        The order within each source is kept, so sources can rank
        their own suggestions.

        A source that fails (e.g. because its data cannot be loaded) is
        skipped and logged, so that it does not break the suggestions of
        the other sources.
        """

        results = []

        for source_id, source in self._sources:
            try:
                results.extend(source.suggest(query))
            except Exception:
                logger.warning(
                    "Suggestions from source '%s' failed and were skipped",
                    source_id,
                    exc_info=True,
                )

        return results