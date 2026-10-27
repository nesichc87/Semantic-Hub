[← Back to README](../README.md)

# Development

Developed and tested with Python 3.13.

Install the Python dependencies:

```
pip install -r requirements.txt
```

Start the development server:

```
uvicorn app.main:app --reload
```

The API will then be available at `http://127.0.0.1:8000`, Swagger UI at `http://127.0.0.1:8000/docs` and the demo page at `http://127.0.0.1:8000/ui/`.

Run the tests:

```
python -m pytest
```

The tests also run automatically on every push and pull request (GitHub Actions, `.github/workflows/tests.yml`).

Note: The KBL, VEC, QUDT and DPPO sources load their source data (KBL XSD, VEC ontology, QUDT unit vocabulary, DPPO modules) from the prostep ECAD wiki, qudt.org and liusemweb.github.io on first use. Resolving these identifiers therefore requires network access; KBL-related tests may require it as well. The VEC, QUDT and DPPO tests use small self-written vocabularies and run without network access.

To run without network access, local copies of the source data can be configured (see below).

## Configuring source URLs

The source URLs can be overridden with environment variables. If a variable is not set or empty, the default online URL is used.

| Variable | Source | Default |
|---|---|---|
| `SEMANTIC_HUB_KBL_XSD_URL` | KBL XSD | `https://ecad-wiki.prostep.org/specifications/kbl/v25-sr1/kbl2.5-sr1.xsd` |
| `SEMANTIC_HUB_VEC_TTL_URL` | VEC ontology | `https://ecad-wiki.prostep.org/specifications/vec/v220/vec-2.2.0-ontology.ttl` |
| `SEMANTIC_HUB_QUDT_UNIT_TTL_URL` | QUDT unit vocabulary | `https://qudt.org/vocab/unit/` |
| `SEMANTIC_HUB_DPPO_TTL_URL` | DPPO modules | `https://liusemweb.github.io/DPPO/ontology/{module}/0.1/{module}.ttl` |

The variables are read when the application starts, so they must be set before the server is started. Local copies can be configured as `file://` URLs, e.g. in PowerShell:

```
$env:SEMANTIC_HUB_VEC_TTL_URL = "file:///C:/sources/vec-2.2.0-ontology.ttl"
uvicorn app.main:app
```

The DPPO URL is a template: `{module}` is replaced by each module name. A local copy can therefore be configured as e.g. `file:///C:/sources/dppo/{module}.ttl`.

A local copy must have the same format as the online source (XSD for KBL, Turtle for VEC, QUDT and DPPO). Local copies of source data are not part of this repository; the licenses of the respective sources apply (see [Semantic sources](sources.md)).

## Running the demo offline

`scripts/start-demo.ps1` (Windows PowerShell) starts the application with local copies of all four sources and loads them before the first request, so that the first visitor does not have to wait for the source data to be parsed.

The script expects a folder containing `kbl2.5-sr1.xsd`, `vec-2.2.0-ontology.ttl`, `qudt-unit.ttl` and the five DPPO modules (`dpp-odp.ttl`, `dpp-core.ttl`, `dpp-info.ttl`, `dpp-comp.ttl`, `dpp-prov.ttl`). It

1. checks that the source files exist and sets the source URL variables to the corresponding `file://` URLs (for DPPO, a URL template),
2. refuses to start if a server is already running on the port,
3. starts uvicorn in a separate window, using the Python interpreter from `.venv`,
4. waits until `/health` responds and resolves one identifier per source,
5. opens the demo page in the browser.

```
powershell -ExecutionPolicy Bypass -File .\scripts\start-demo.ps1 -SourceDir <folder with local copies>
```

`-Port` selects a different port (default: 8000). `-ExecutionPolicy Bypass` applies to this call only and is needed if running scripts is disabled on the machine.

## Docker

Docker-based deployment is planned. A Dockerfile does not exist yet.

Planned deployment:

```
Docker Container
┌──────────────────────────────┐
│                              │
│       Semantic Hub API       │
│                              │
│          FastAPI             │
│             │                │
│       Resolver / Registry    │
│             │                │
│        Semantic Sources      │
│                              │
└──────────────────────────────┘
```

The demo page is served by the API itself and needs no separate container. Additional services may later be deployed as separate containers using Docker Compose, for example:

- a database-backed cache for source data and resolved concepts (under consideration; the caching approach has not been decided yet)
