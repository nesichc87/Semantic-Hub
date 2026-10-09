from collections.abc import Iterable, Mapping


EXACT = 0
PREFIX = 1
SUBSTRING = 2


def rank_matches(query: str, candidates: Mapping[str, Iterable[str]]) -> list[str]:
    """
    Return the semantic identifiers whose search texts match the query.

    Matching is case-insensitive. Candidates are ranked by their best
    matching text: exact match, then prefix match, then substring match.
    Within the same rank, identifiers are sorted alphabetically.
    Candidates without a matching text are excluded.
    """

    search = query.strip().lower()

    if not search:
        return []

    ranked = []

    for semantic_id, texts in candidates.items():
        rank = _best_rank(search, texts)

        if rank is not None:
            ranked.append((rank, semantic_id))

    return [semantic_id for _, semantic_id in sorted(ranked)]


def _best_rank(search: str, texts: Iterable[str]) -> int | None:
    best = None

    for text in texts:
        value = text.lower()

        if value == search:
            rank = EXACT
        elif value.startswith(search):
            rank = PREFIX
        elif search in value:
            rank = SUBSTRING
        else:
            continue

        if best is None or rank < best:
            best = rank

    return best