# Semantic Hub

[![Tests](https://github.com/nesichc87/Semantic-Hub/actions/workflows/tests.yml/badge.svg)](https://github.com/nesichc87/Semantic-Hub/actions/workflows/tests.yml)

Prototype implementation of the **Semantic Hub** concept described in:

> **[The Semantic Hub – Unifying Fragmented Semantic Dictionaries for Industry 4.0 and AAS](https://wwwlehre.dhbw-stuttgart.de/~rentschler/Publications/ETFA2026__The_Semantic_Hub_extended.pdf)**  
> Markus Rentschler et al.
>

<img width="1491" height="669" alt="image" src="https://github.com/user-attachments/assets/cc3e382a-f274-4ac4-bd37-4bc9de84b12d" />

This repository implements the **Retrieval Service** of the Semantic Hub concept (resolver, REST API and demo page). The Semantic Wikibase and the IDTA Semantic Repository described in the paper are not part of it. The project was started as a private, open project and is not part of a funded project.

The goal is an open and extensible service that resolves semantic identifiers from different semantic dictionaries through one API, keeps their provenance, and also returns them in an IEC 61360-oriented form as used by Concept Descriptions in the **Asset Administration Shell (AAS)**.

🚧 Early development / work in progress

---

## What it does

- **Resolve** a semantic identifier exactly (case-sensitive, nothing is guessed), e.g. `GET /api/resolve/kbl:Component`
- **Suggest** matching identifiers for a search term across all sources, ranked per source (exact, prefix, substring)
- **Two output formats**: `original` (source-oriented) and `iec61360` (IEC 61360-oriented; not a complete or conformant implementation)
- **Common internal model** between the sources and the output formats, so a new source reuses the existing formatters and API
- **Demo page** under `/ui/` (no external dependencies, German and English) and **Swagger UI** under `/docs`, both usable offline
- **Robust**: a source that cannot be loaded does not break the others (suggestions skip it, resolution returns 503)

## Sources

| Source | Based on | Status |
|---|---|---|
| KBL | KBL XSD v2.5 SR-1 | implemented, limited scope |
| VEC | VEC 2.2.0 OWL ontology | implemented, limited scope |
| QUDT | QUDT unit vocabulary (units only) | implemented, limited scope |
| DPPO | Digital Product Passport Ontology 0.1 | implemented, limited scope |
| ECLASS | ECLASS 16.0 Asset | under evaluation |

Supported constructs, identifier schemes, limitations and licenses of the source data: [docs/sources.md](docs/sources.md). No source data is included in this repository.

## Quickstart

Requires Python 3.13.

```
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open the demo page at `http://127.0.0.1:8000/ui/` or the Swagger UI at `http://127.0.0.1:8000/docs`.

```
GET /api/resolve/vec:PartVersion?format=iec61360
GET /api/suggest?query=metre
```

Run the tests (they also run on every push via GitHub Actions):

```
python -m pytest
```

The sources load their data from the internet on first use. For offline use, local copies can be configured; see [docs/development.md](docs/development.md).

## Documentation

- [Architecture](docs/architecture.md) – layers, request flow, source interface, registry, resolver, formatters, project structure
- [Semantic sources](docs/sources.md) – KBL, VEC, QUDT, DPPO, ECLASS: scope and limitations
- [REST API](docs/api.md) – endpoints, responses and error codes
- [Development](docs/development.md) – setup, tests, source URL configuration, offline demo, Docker plans

## Planned

- QUDT quantity kinds and unit values (e.g. symbol, IEC 61360 code)
- Units with SI reference (under evaluation, e.g. the BIPM SI Digital Framework)
- DPPO properties whose domain is a union of classes (`owl:unionOf`)
- ECLASS, once integration approach and licensing are clarified
- Review and extension of the IEC 61360-oriented output
- Persistent caching of source data
- AAS-compatible semantic information
- Docker-based deployment

## Reference

Rentschler, M. et al.: *The Semantic Hub – Unifying Fragmented Semantic Dictionaries for Industry 4.0 and AAS.* ETFA 2026.
[Extended version (PDF)](https://wwwlehre.dhbw-stuttgart.de/~rentschler/Publications/ETFA2026__The_Semantic_Hub_extended.pdf)

The paper proposes an open infrastructure for integrating heterogeneous semantic resources and describes a Retrieval Service consisting of components including a Registry, Resolver and Formatter. This repository implements the Retrieval Service and uses these concepts as the architectural basis. The internal semantic model between the sources and the formatters is an addition of this implementation.

## License

Licensed under the [Apache License 2.0](LICENSE). The local copy of Swagger UI in `app/static/swagger/` is also licensed under the Apache License 2.0 (see the `LICENSE` file there).
