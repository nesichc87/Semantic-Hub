"""Generic table source type: one row per concept, defined by configuration only.

Data is read through an injected fetch function. The identifier column is
only stripped, so codes stay exactly as in the source; names and
descriptions are whitespace-normalized. An unusable table raises
RuntimeError (reported as an unavailable source).
"""

import csv
import io
import logging
from dataclasses import dataclass

from app.models.semantic import SemanticConcept
from app.sources.base import SemanticSource
from app.sources.generic.config_schema import TableSourceConfig
from app.sources.generic.rdf import Fetch
from app.sources.ranking import rank_matches


logger = logging.getLogger(__name__)

MAX_ROWS = 200_000


@dataclass
class _Row:
    name: str
    description: str | None
    equivalents: list[str]


class GenericTableSource(SemanticSource):

    def __init__(self, config: TableSourceConfig, fetch: Fetch):
        self.config = config
        self._fetch = fetch
        self._rows: dict[str, _Row] | None = None

    # ---------- SemanticSource ----------

    def can_resolve(self, semantic_id: str) -> bool:
        return semantic_id.startswith(self.config.prefix)

    def resolve(self, semantic_id: str) -> SemanticConcept:
        if not self.can_resolve(semantic_id):
            raise ValueError(f"Unknown semantic ID: {semantic_id}")

        row = self._get_rows().get(semantic_id[len(self.config.prefix):])
        if row is None:
            raise ValueError(f"Unknown semantic ID: {semantic_id}")

        return SemanticConcept(
            semantic_id=semantic_id,
            source=self.config.id,
            name=row.name,
            description=row.description,
            properties=[],
            provenance={"source": self.config.id, "source_reference": semantic_id},
        )

    def suggest(self, query: str) -> list[str]:
        if not query.strip():
            return []

        candidates = {
            self.config.prefix + key: [row.name, key]
            for key, row in self._get_rows().items()
        }
        return rank_matches(query, candidates)

    def equivalents(self) -> dict[str, set[str]]:
        """Entries of the equivalence column per semantic ID."""
        return {
            self.config.prefix + key: set(row.equivalents)
            for key, row in self._get_rows().items()
            if row.equivalents
        }

    # ---------- Loading ----------

    def _get_rows(self) -> dict[str, _Row]:
        if self._rows is None:
            raw = self._fetch(self.config.location, self.config.format)
            table = self._read_table(raw)
            # Assigned only after a successful load, so errors are not cached.
            self._rows = self._index(table)
        return self._rows

    def _read_table(self, raw: bytes) -> list[list[str]]:
        if self.config.format == "csv":
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise RuntimeError(f"Table is not valid UTF-8: {self.config.location}") from exc
            delimiter = self.config.delimiter or _guess_delimiter(text)
            rows = []
            for values in csv.reader(io.StringIO(text), delimiter=delimiter):
                rows.append(values)
                if len(rows) > MAX_ROWS:
                    raise RuntimeError(f"Table has more than {MAX_ROWS} rows: {self.config.location}")
            return rows
        raise NotImplementedError("Excel files are added in the next step")

    def _index(self, table: list[list[str]]) -> dict[str, _Row]:
        header_row = self.config.header_row
        if header_row > len(table):
            raise RuntimeError(
                f"Header row {header_row} is outside the table ({len(table)} rows): "
                f"{self.config.location}"
            )
        header = [cell.strip() for cell in table[header_row - 1]]

        def index_of(column: str | None) -> int | None:
            if column is None:
                return None
            if column not in header:
                raise RuntimeError(
                    f"Column '{column}' not found in header row {header_row}: "
                    f"{self.config.location}"
                )
            return header.index(column)

        columns = self.config.columns
        i_id = index_of(columns.id)
        i_name = index_of(columns.name)
        i_description = index_of(columns.description)
        i_equivalence = index_of(columns.equivalence)

        def cell(values: list[str], index: int | None) -> str:
            return values[index] if index is not None and index < len(values) else ""

        rows: dict[str, _Row] = {}
        first_row: dict[str, int] = {}
        for number, values in enumerate(table[header_row:], start=header_row + 1):
            key = cell(values, i_id).strip()
            if not key:
                continue  # empty rows, footnotes
            if key in rows:
                logger.warning(
                    "Skipped duplicate identifier '%s' in row %d of %s (row %d applies)",
                    key, number, self.config.location, first_row[key],
                )
                continue
            first_row[key] = number
            rows[key] = _Row(
                name=_normalize(cell(values, i_name)) or key,
                description=_normalize(cell(values, i_description)) or None,
                equivalents=cell(values, i_equivalence).replace(";", " ").split(),
            )

        if not rows:
            raise RuntimeError(f"Table has no rows with an identifier: {self.config.location}")
        return rows


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _guess_delimiter(text: str) -> str:
    """Delimiter that occurs equally often in most lines (robust against notes above the header)."""
    lines = [line for line in text.splitlines()[:200] if line.strip()]
    best, best_score = ",", (0, 0)
    for delimiter in (",", ";", "\t", "|"):
        counts = [line.count(delimiter) for line in lines if line.count(delimiter)]
        if not counts:
            continue
        mode = max(set(counts), key=counts.count)
        score = (counts.count(mode), mode)
        if score > best_score:
            best, best_score = delimiter, score
    return best