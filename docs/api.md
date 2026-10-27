[← Back to README](../README.md)

# REST API

The REST API is implemented using FastAPI.

Swagger UI: `/docs` (served from a local copy of `swagger-ui-dist` 5.17.14 in `app/static/swagger/`, Apache License 2.0, so it also works without network access; it contains a link back to the demo page)

## Current endpoints

### Health

```
GET /health
```

Returns the current application status.

### Root

```
GET /
```

Returns basic application information.

### Demo page

```
GET /ui/
```

Serves a static demo page (HTML, CSS and JavaScript, no external dependencies). While typing, it requests suggestions from `/api/suggest`. On Enter or the resolve button, it resolves the identifier exactly via `/api/resolve/{semantic_id}` and shows the `original` and `iec61360` output side by side.

Features of the demo page:

- search field with live suggestions grouped by source
- exact resolution via button or Enter, including the 404 case with a hint for IDs that differ only in letter case
- `original` and `iec61360` output side by side, with a property table comparing source and IEC 61360 data types
- example identifiers for KBL, VEC, QUDT and DPPO
- a request line showing the current call; clearing the search field resets the page
- German and English user interface, switchable on the page; all texts are kept in `app/static/ui/i18n.js`, so further languages can be added there (a test checks that all languages define the same keys)
- links to the Swagger UI and back
- the files are served with `Cache-Control: no-cache`, so browsers always load the current version

### Semantic resolution

```
GET /api/resolve/{semantic_id}?format={original|iec61360}
```

Resolves a semantic identifier through the registered semantic sources and returns it in the requested format. If `format` is omitted, `original` is used.

Example:

```
GET /api/resolve/kbl%3AComponent?format=iec61360
```

Response:

```
{
  "semantic_id": "kbl:Component",
  "format": "iec61360",
  "result": { ... }
}
```

Error responses:

- `404` – the semantic identifier could not be resolved
- `422` – invalid request parameters (e.g. unsupported `format` value)
- `503` – the responsible semantic source could not be loaded (e.g. no network access and no local copy)

### Semantic suggestions

```
GET /api/suggest?query={text}
```

Searches all registered semantic sources for semantic identifiers matching the query. `query` is required and must not be empty.

Matching is case-insensitive. Within each source, results are ranked by their best matching search text: exact matches first, then prefix matches, then substring matches, each sorted alphabetically. Search texts are the type or class name (KBL, VEC, DPPO) and, for QUDT, the unit's local name and English or untagged labels. Results are grouped by source in registration order (KBL, VEC, QUDT, DPPO); there is no ranking across sources. A source that cannot be loaded is skipped.

Response:

```
{
  "query": "...",
  "results": [ ... ]
}
```
