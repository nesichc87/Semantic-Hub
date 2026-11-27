[← Back to README](../README.md)

# Development

Developed and tested with Python 3.13.

Install the Python dependencies, including the test tools:

```
pip install -r requirements-dev.txt
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

## Source catalog database (in development)

The source catalog (configuration, status and load results of the generic sources) is stored in a database. At start, the application brings the database to the latest migration and activates preselected seed sources; `/health` reports whether the database is reachable. If the database is not reachable, the application still starts. Without `SEMANTIC_HUB_DATABASE_URL`, a local start (e.g. `uvicorn app.main:app --reload`) creates `semantic-hub.db` in the working directory.

| Variable | Default |
|---|---|
| `SEMANTIC_HUB_DATABASE_URL` | `sqlite:///semantic-hub.db` (SQLite file in the working directory) |

If the variable is not set or empty, the default is used. The database file is not part of the repository (`*.db` is ignored). PostgreSQL support follows with the database container.

Migrations are part of the application (`app/catalog/migrations`) and are run from code, so no `alembic.ini` is needed.

| Variable | Meaning |
|---|---|
| `SEMANTIC_HUB_SEED_SOURCES` | Comma-separated IDs of shipped seed sources to activate at the first start (only if the catalog is empty). Setting it confirms the licenses of these sources. The shipped seed list is currently empty. |

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

## Deployment

The Semantic Hub runs as two Docker containers: `semantic-hub` with the FastAPI application (resolver, registry, the four built-in sources, demo page) and `db` with PostgreSQL for the source catalog. The application image only packages the state of the checked-out tag; it contains no source data.

```
┌──────────────────────────────┐      ┌──────────────────────┐
│ semantic-hub (port 8000)     │      │ db                   │
│  FastAPI, Resolver/Registry  │ ───► │  PostgreSQL 18       │
│  Semantic Sources            │      │  source catalog      │
│  /ui/, /docs, /health        │      │  volume db-data      │
└──────────────────────────────┘      └──────────────────────┘
```

Requirements: Docker with Docker Compose v2, and network access to the source servers (prostep ECAD wiki, qudt.org, liusemweb.github.io) unless local copies are configured (see below).

### Start

```
git clone --branch <tag> https://github.com/nesichc87/Semantic-Hub.git
cd Semantic-Hub
cp .env.example .env      # PowerShell: Copy-Item .env.example .env
# set POSTGRES_PASSWORD in .env
docker compose up -d --build
```
Without `POSTGRES_PASSWORD` in `.env`, `docker compose` stops with a message. The database port is not published; only the application reaches it. Releases up to `v0.1.1` run without a database; for those, follow the documentation in the respective tag.

The API listens on port 8000 (change it with the environment variable `SEMANTIC_HUB_PORT`, e.g. `SEMANTIC_HUB_PORT=8080`).

### Check

```
docker compose ps
curl http://localhost:8000/health
curl "http://localhost:8000/api/resolve/vec:PartVersion"
```

- `docker compose ps` shows the state `healthy` once the health check on `/health` succeeds.
- `/health` returns `{"status": "ok", "database": "ok"}`. If the catalog database cannot be reached, it returns 503 with `{"status": "degraded", "database": "unavailable"}`, and the container is reported as `unhealthy`; the demo page and the built-in sources keep working.
- The demo page is at `http://localhost:8000/ui/`, Swagger UI at `http://localhost:8000/docs`.
- The sources load their data on first use, so the first request per source takes longer. A source that cannot be loaded returns 503 and does not affect the others.

### Source URLs and local copies

The source URLs are passed to the container through the environment variables described in "Configuring source URLs". If they are not set, the default online URLs are used. They can be set in the shell or in a `.env` file next to `docker-compose.yml`.

For use without internet access, put the local copies into one folder (same file names as for `scripts/start-demo.ps1`). Build the image once while online, then start with the override file and without `--build`:

```
docker compose build
SEMANTIC_HUB_SOURCE_DIR=/path/to/sources docker compose -f docker-compose.yml -f docker-compose.local-sources.yml up -d
```

In PowerShell:

```
docker compose build
$env:SEMANTIC_HUB_SOURCE_DIR = "C:\sources"
docker compose -f docker-compose.yml -f docker-compose.local-sources.yml up -d
```

Starting with `--build` requires network access even if all image layers are cached, because Docker looks up the base image `python:3.13-slim` in the registry.

The folder is mounted read-only into the container. Local copies of source data are not part of this repository; the licenses of the respective sources apply (see [Semantic sources](sources.md)).

### Logs, restart, stop

```
docker compose logs -f
docker compose restart
docker compose down
```

Both containers restart automatically after a reboot of the Docker host (`restart: unless-stopped`). The application keeps no data; sources are loaded again after every restart. The source catalog is kept in the volume `db-data`; `docker compose down -v` deletes it.

### Update

```
git fetch --tags
git checkout <new tag>
docker compose up -d --build
```

When updating from `v0.1.1` (no database) to a release with database, create `.env` from `.env.example` first.

## Branches and releases

- `main` contains the latest presentable state. It is only changed via pull requests from `develop`, and the tests must pass.
- `develop` is the integration branch for ongoing work.
- Work is done in feature branches created from `develop` (e.g. `feature/generic-sources`) and merged back into `develop` via pull request once the tests pass.
- Presentable states are tagged on `main` using semantic versioning (`vMAJOR.MINOR.PATCH`).

| Tag | State |
|---|---|
| `v0.1.0` | State presented at the AAS-Anwendertreffen 2026 |

To run a tagged state, check out the tag, e.g. `git checkout v0.1.0`.
