# Semantic Hub

Prototype implementation of the **Semantic Hub** concept described in:

> **[The Semantic Hub – Unifying Fragmented Semantic Dictionaries for Industry 4.0 and AAS](https://wwwlehre.dhbw-stuttgart.de/~rentschler/Publications/ETFA2026__The_Semantic_Hub_extended.pdf)**  
> Markus Rentschler et al.

The project aims to provide an open and extensible infrastructure for resolving and retrieving semantic information from different semantic sources in the context of **Industry 4.0** and the **Asset Administration Shell (AAS)**.

The implementation is developed based on the architecture and concepts described in the paper and is being built up incrementally from a clean implementation.

---

## Project Status

🚧 Early development / Work in progress

The project is being built up incrementally. KBL is the first real semantic source and is integrated with a limited scope.

### Currently implemented

- FastAPI-based REST API with OpenAPI / Swagger documentation
- Semantic resolver and semantic source registry
- Pluggable semantic source interface
- Mock semantic source (development and testing only)
- **KBL source (limited scope)**, based on the KBL XSD v2.5 SR-1:
  - resolution of named simple and complex XSD types
  - complex type inheritance, including inherited elements
  - resolution of simple type restrictions down to the built-in XSD type
  - exact, case-sensitive type resolution
  - case-insensitive search of named types for suggestions
- Internal semantic model (concepts, properties, source provenance)
- Output formats:
  - `original` – source-oriented, normalized representation of the internal model (not an unchanged KBL serialization)
  - `iec61360` – minimal IEC 61360-oriented representation with partial data type mapping (not a complete or conformant IEC 61360 implementation)
- Suggestion endpoint for semantic identifiers
- Automated tests (pytest) for the semantic model, KBL type resolution, data type mapping and formatters

### Planned

- QUDT integration
- VEC integration
- ECLASS (under evaluation): based on the ECLASS 16.0 Asset; integration approach and licensing conditions are still to be clarified
- Review and extension of the IEC 61360-oriented output
- Persistent caching of source data (approach to be decided, e.g. file-based or database-backed)
- AAS-compatible semantic information
- Graphical user interface
- Docker-based deployment

---

## Architecture

The project follows a layered architecture that separates the REST API from semantic resolution, the individual semantic sources and the output formatting.

```
                 REST API (FastAPI)
                        │
                        ▼
                   API Routes
                        │
                        ▼
                Semantic Resolver
                        │
                        ▼
                Semantic Registry
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
       KBL             QUDT            VEC
   (limited)        (planned)       (planned)
        │
        ▼
 Internal Semantic Model
 (concepts, properties, provenance)
        │
        ▼
    Formatter
 (original / iec61360)
        │
        ▼
   API response
```

Semantic sources are implemented behind a common interface and map their source information into the internal semantic model. Source provenance is kept in the model.

The formatters operate on the internal semantic model rather than on source-specific data. This is intended to allow additional sources to reuse the existing output formats. Whether the internal model is sufficiently source-independent will be verified when a second source is integrated.

A mock source is additionally available for development and testing.

This allows the Semantic Hub to support additional semantic sources without requiring a separate REST service for every source.

---

## Current API Flow

```
HTTP Request
     │
     ▼
FastAPI / API Route
     │
     ▼
Semantic Resolver
     │
     ▼
Semantic Registry  →  responsible semantic source
     │
     ▼
Internal Semantic Model
     │
     ▼
Formatter (original / iec61360)
     │
     ▼
JSON Response
```

Example requests:

```
GET /api/resolve/kbl:Component?format=original
GET /api/resolve/kbl:Component?format=iec61360
```

If no format is given, `original` is used.

Response structure:

```
{
  "semantic_id": "kbl:Component",
  "format": "original",
  "result": { ... }
}
```

The content of `result` depends on the requested format. For `kbl:Component`, both formats return the 16 properties of the KBL type, including inherited elements.

In the `iec61360` format, only supported data types are mapped (currently `xs:string` → `STRING`, `xs:boolean` → `BOOLEAN`). Unsupported or complex types are returned with `data_type: null`; the property itself is kept.

Unknown semantic identifiers result in HTTP 404.

---

## Project Structure

```
Semantic-Hub/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── semantic.py         # REST endpoints (resolve, suggest)
│   │
│   ├── formatter/
│   │   ├── base.py                 # common formatter interface
│   │   ├── original.py             # source-oriented output
│   │   ├── iec61360.py             # IEC 61360-oriented output
│   │   └── iec61360_types.py       # data type mapping for IEC 61360 output
│   │
│   ├── models/
│   │   └── semantic.py             # internal semantic model
│   │
│   ├── registry/
│   │   └── registry.py             # registration of semantic sources
│   │
│   ├── resolver/
│   │   └── resolver.py             # resolution of semantic identifiers
│   │
│   ├── sources/
│   │   ├── base.py                 # common semantic source interface
│   │   ├── mock.py                 # mock source (development / testing)
│   │   └── kbl/
│   │       ├── client.py           # loading of the KBL XSD
│   │       ├── parser.py           # XSD parsing
│   │       ├── service.py          # high-level resolution of KBL types and their elements
│   │       ├── mapper.py           # placeholder (currently empty)
│   │       └── source.py           # KBL semantic source, maps resolved types to the internal model
│   │
│   └── main.py                     # FastAPI application
│
├── tests/                          # pytest test suite
├── requirements.txt
└── README.md
```

The structure is intentionally modular so that semantic sources and formatting logic can be developed independently from the REST API.

---

## Semantic Sources

The Semantic Hub is intended to work with heterogeneous semantic resources.

### KBL (implemented, limited scope)

KBL is the first real semantic source. The source evaluates the KBL XSD v2.5 SR-1 schema, i.e. the type definitions, not KBL instance documents.

Semantic identifiers use the form `kbl:<TypeName>` for concepts and `kbl:<TypeName>:<ElementName>` for properties, e.g. `kbl:Component` and `kbl:Component:Part_number`.

**Supported:**

- named simple and complex XSD types
- complex type inheritance, including inherited elements
- simple type restrictions, resolved down to the built-in XSD type
- exact, case-sensitive resolution of type names
- case-insensitive search of named types for suggestions
- source provenance for concepts and properties

**Current limitations:**

- Only the XSD constructs listed above are supported. The goal is not to support every possible XSD structure.
- Types that cannot be resolved are not guessed. They are kept as a type reference (`original`) or returned with `data_type: null` (`iec61360`).
- Numeric XSD types are not mapped to an IEC 61360 data type, because the semantic context is missing.
- `definition` is `null` for KBL. The KBL XSD v2.5 SR-1 contains no descriptive documentation: its `xs:documentation` entries are exclusively reference hints on `IDREF`/`IDREFS` elements (e.g. "ref to External_reference"). These are not definitions and are currently not evaluated.
- `unit` is `null` for KBL. The KBL schema does not define concrete units: types derived from `Value_with_unit` (e.g. `Numerical_value`) reference a `Unit` object via `xs:IDREF`, so the unit is only determined in a KBL instance document. Since the Semantic Hub evaluates the schema, not instance documents, no unit can be derived.
- The XSD is loaded remotely on first use and then kept in memory for the lifetime of the process. There is no persistent cache yet, so the first request after a restart requires network access.
- This is not a complete KBL implementation.

### Mock (development and testing)

A mock source (`mock:` prefix) is used for development and testing. It returns a minimal concept of the internal semantic model.

### QUDT (planned)

QUDT is planned as an additional semantic source. The existing prototype uses SPARQL-based access to QUDT resources.

### VEC (planned)

VEC is planned as a semantic source and will be integrated through the common semantic source interface.

### ECLASS (under evaluation)

The use of the ECLASS 16.0 Asset is being evaluated. The integration approach and the licensing conditions are still to be clarified. ECLASS data will not be included in this repository unless the license permits it.

---

## Source Abstraction

Semantic sources implement a common interface (`app/sources/base.py`):

```python
class SemanticSource(ABC):

    @abstractmethod
    def can_resolve(self, semantic_id: str) -> bool:
        ...

    @abstractmethod
    def resolve(self, semantic_id: str) -> SemanticConcept:
        ...

    @abstractmethod
    def suggest(self, query: str) -> list[str]:
        ...
```

- `can_resolve()` is used by the Registry to determine which source is responsible for a semantic identifier.
- `resolve()` returns a concept of the internal semantic model (`SemanticConcept`) for an identifier.
- `suggest()` returns semantic identifiers matching a search query.

This avoids coupling the REST API directly to individual semantic dictionaries.

---

## Resolver

The Resolver is responsible for resolving a semantic identifier through the registered semantic sources.

```
Semantic ID
     │
     ▼
  Registry
     │
     ▼
 matching source
     │
     ▼
  Resolver
     │
     ▼
 semantic information
```

The resolver is intentionally separated from the HTTP layer so that the resolution logic can also be used independently of the REST API.

## Registry

The Registry maintains the available semantic sources.

A source is registered with the Registry:

```python
registry.register(source)
```

The Registry uses `can_resolve()` to determine which source is able to resolve a given semantic identifier.

For suggestions, the Registry delegates the search query to all registered sources and aggregates their results.

This provides an extensible mechanism for adding additional semantic resources.

---

## Formatter

The paper describes the use of a Formatter as part of the Retrieval Service. In this implementation, formatters convert a concept of the internal semantic model into an API representation. They operate on the internal model, not on source-specific data.

Two formats are currently available (`?format=` parameter):

### `original` (default)

Source-oriented, normalized representation of the internal semantic model, including properties, semantic identifiers, type references and source provenance.

This is not an unchanged serialization of the source (e.g. not the original KBL XSD).

### `iec61360`

Minimal IEC 61360-oriented representation. This is **not** a complete or conformant IEC 61360 implementation.

Output fields per concept and property:

| Field | Content |
|---|---|
| `semantic_id` | semantic identifier |
| `preferred_name` | name of the concept or property |
| `definition` | description, if available |
| `data_type` | mapped IEC 61360 data type, or `null` |
| `unit` | unit, if available |
| `source_of_definition` | source from the provenance, if available |

Concepts additionally contain their `properties`.

Data type mapping (`app/formatter/iec61360_types.py`):

| Source type | IEC 61360 data type |
|---|---|
| `xs:string` / `string` | `STRING` |
| `xs:boolean` / `boolean` | `BOOLEAN` |
| all other types (numeric XSD types, complex types, unknown or missing types) | `null` |

Unsupported types are not guessed. Properties with an unsupported type are kept in the output and returned with `data_type: null`.

---

## REST API

The REST API is implemented using FastAPI.

Swagger UI: `/docs`
OpenAPI specification: `/openapi.json`

### Current endpoints

#### Health

```
GET /health
```

Returns the current application status.

#### Root

```
GET /
```

Returns basic application information.

#### Semantic resolution

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

#### Semantic suggestions

```
GET /api/suggest?query={text}
```

Searches all registered semantic sources for semantic identifiers matching the query. `query` is required and must not be empty.

Response:

```
{
  "query": "...",
  "results": [ ... ]
}
```
---

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

Additional services may later be deployed as separate containers using Docker Compose, for example:

- a graphical user interface
- a database-backed cache for source data and resolved concepts (under consideration; the caching approach has not been decided yet)

---

## Development

Developed and tested with Python 3.13.

Install the Python dependencies:

```
pip install -r requirements.txt
```

Start the development server:

```
uvicorn app.main:app --reload
```

The API will then be available at `http://127.0.0.1:8000`, Swagger UI at `http://127.0.0.1:8000/docs`.

Run the tests:

```
python -m pytest
```

Note: The KBL source loads the KBL XSD from the prostep ECAD wiki at runtime. Resolving KBL identifiers therefore requires network access; KBL-related tests may require it as well.

---

## Reference

The project is based on the concepts described in:
https://wwwlehre.dhbw-stuttgart.de/~rentschler/Publications/ETFA2026__The_Semantic_Hub_extended.pdf
Rentschler, M. et al.

The Semantic Hub – Unifying Fragmented Semantic Dictionaries for Industry 4.0 and AAS.

The paper proposes an open infrastructure for integrating heterogeneous semantic resources and describes a Retrieval Service consisting of components including a Registry, Resolver and Formatter.

The project uses these concepts as the architectural basis for the implementation.

