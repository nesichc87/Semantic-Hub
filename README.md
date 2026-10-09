# Semantic Hub

Prototype implementation of the **Semantic Hub** concept described in:

> **[The Semantic Hub – Unifying Fragmented Semantic Dictionaries for Industry 4.0 and AAS](https://wwwlehre.dhbw-stuttgart.de/~rentschler/Publications/ETFA2026__The_Semantic_Hub_extended.pdf)**  
> Markus Rentschler et al.

The project aims to provide an open and extensible infrastructure for resolving and retrieving semantic information from different semantic sources in the context of **Industry 4.0** and the **Asset Administration Shell (AAS)**.

The implementation is developed based on the architecture and concepts described in the paper and is being built up incrementally from a clean implementation.

---

## Project Status

🚧 Early development / Work in progress

The project is being built up incrementally. KBL (XSD-based), VEC (ontology-based) and QUDT (RDF vocabulary) are integrated as semantic sources with a limited scope.

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
- **VEC source (limited scope)**, based on the VEC 2.2.0 OWL ontology (Turtle):
  - resolution of named ontology classes
  - properties attached via `rdfs:domain`, including properties inherited via `rdfs:subClassOf`
  - definitions from `rdfs:comment` for classes and properties
  - exact, case-sensitive class resolution
  - case-insensitive search of class names for suggestions
- **QUDT source (limited scope)**, based on the QUDT unit vocabulary (Turtle):
  - resolution of units (`qudt:Unit`) in the QUDT unit namespace
  - names from English or untagged labels, descriptions from plain-text or Dublin Core descriptions
  - exact, case-sensitive unit resolution
  - case-insensitive search of unit names and English labels for suggestions
- In-memory caching of the parsed source data (KBL XSD, VEC ontology, QUDT unit vocabulary) for the lifetime of the process
- Internal semantic model (concepts, properties, source provenance)
- Output formats:
  - `original` – source-oriented, normalized representation of the internal model (not an unchanged KBL serialization)
  - `iec61360` – minimal IEC 61360-oriented representation with partial data type mapping (not a complete or conformant IEC 61360 implementation)
- Suggestion endpoint for semantic identifiers:
  - ranked results per source: exact matches first, then prefix matches, then substring matches
- Automated tests (pytest) for the semantic model, KBL and VEC resolution, data type mapping, formatters and API

### Planned

- QUDT quantity kinds and unit values (e.g. symbol, IEC 61360 code)
- VEC integration
- ECLASS (under evaluation): based on the ECLASS 16.0 Asset; integration approach and licensing conditions are still to be clarified
- Review and extension of the IEC 61360-oriented output
- Persistent caching of source data (approach to be decided, e.g. file-based or database-backed)
- AAS-compatible semantic information
- Graphical user interface (demo page under `/ui/`, in progress)
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
       KBL             VEC             QUDT
   (XSD, limited)  (OWL, limited)   (TTL, limited)
        │               │
        └───────┬───────┘
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

The formatters operate on the internal semantic model rather than on source-specific data. This is intended to allow additional sources to reuse the existing output formats. With VEC as a second, differently modelled source (OWL ontology instead of XSD, ontology-native property identifiers instead of composed ones), the existing formatters, resolver and API endpoints could be reused without changes.

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
│   │   ├── ranking.py              # ranking of suggestions (exact, prefix, substring)
│   │   ├──kbl/
│   │   │   ├── client.py           # loading of the KBL XSD
│   │   │   ├── parser.py           # XSD parsing
│   │   │   ├── service.py          # high-level resolution of KBL types and their elements
│   │   │   ├── mapper.py           # placeholder (currently empty)
│   │   │   └── source.py           # KBL semantic source, maps resolved types to the internal model
│   │   ├── vec/
│   │   │    ├── client.py           # loading of the VEC ontology (Turtle)
│   │   │    ├── service.py          # resolution of VEC classes, properties and inheritance
│   │   │    └── source.py           # VEC semantic source, maps classes to the internal model
│   │   ├── qudt/
│   │   │   ├── client.py           # loading of the QUDT unit vocabulary (Turtle)
│   │   │   ├── service.py          # resolution and search of QUDT units
│   │   │   ├── mapper.py           # maps resolved units to the internal model
│   │   │   └── source.py           # QUDT semantic source
│   ├── config.py                   # source URL configuration via environment variables
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
- simple types are returned as concepts without properties; their base type is kept as the concept's `data_type`
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

### QUDT (implemented, limited scope)

QUDT is the third real semantic source. It is integrated via the QUDT unit vocabulary in Turtle (`https://qudt.org/vocab/unit/`), which is loaded as an RDF graph like the VEC ontology. The integration was checked against QUDT release 3.5.2 (2,932 units). QUDT publishes new releases regularly, so the content behind this URL can change.

Semantic identifiers use the form `qudt:unit:<LocalName>`, e.g. `qudt:unit:M` for `http://qudt.org/vocab/unit/M`.

```
GET /api/resolve/qudt%3Aunit%3AM?format=original
```

**Supported:**

- units (`qudt:Unit`) in the QUDT unit namespace; units are individuals, not classes
- name from `rdfs:label` with the language tag `en` or without a tag; regional variants such as `en-US` are ignored. If no such label exists (2 of 2,932 units in release 3.5.2), the local name is used (e.g. `M`).
- description from `qudt:plainTextDescription`, falling back to `dcterms:description`. In release 3.5.2, 823 units have a plain-text description and 2,438 a Dublin Core description; the fallback may contain LaTeX markup.
- whitespace in names and descriptions is normalized, because line breaks and repeated spaces stem from the Turtle formatting
- exact, case-sensitive unit resolution
- case-insensitive search of local names and English or untagged labels for suggestions

**Current limitations:**

- Only units can be resolved. Quantity kinds are not supported yet.
- Unit values such as symbol, UCUM code, IEC 61360 code, quantity kinds or conversion multiplier are not mapped yet. Units are returned as concepts without properties and with `data_type: null`.
- Only English or untagged literals are used for names and descriptions.
- Suggestions can return many results (e.g. 766 units for `metre`); the number of results is not limited yet. Results are ranked, so `qudt:unit:M` comes first for `metre` (exact match of its English label).
- The vocabulary (about 4 MB) is loaded remotely on first use and then kept in memory for the lifetime of the process. Parsing took about 2.3 s in a local test.
- This is not a complete QUDT implementation.

**License:** According to the `dcterms:rights` statement in the vocabulary metadata, the QUDT ontologies are issued under CC BY 4.0. The metadata additionally states that UCUM tables, codes and definitions are subject to a separate license. No QUDT data is included in this repository.

An earlier prototype accessed QUDT via a SPARQL endpoint. A file-based approach was chosen instead to keep the same source pattern as VEC and to resolve against a fixed release within a process. The prototype's fuzzy best-match resolution was not adopted.

### VEC (implemented, limited scope)

VEC is the second real semantic source. It is integrated via the VEC 2.2.0 OWL ontology (Turtle), not the VEC XSD. This keeps KBL (XSD-based) and the ontology-based sources (VEC, later QUDT) on their natural representation.

Semantic identifiers use the form `vec:<ClassName>` for concepts. Properties keep their ontology-native identifiers, e.g. `vec:PartVersion` and `vec:partVersionPartNumber`. Unlike KBL, property identifiers are therefore not composed from the concept name.

**Supported:**

- named OWL classes in the VEC namespace
- properties attached via `rdfs:domain`
- inherited properties via `rdfs:subClassOf`; inherited properties come first, starting with the most general base class
- definitions from `rdfs:comment` for classes and properties (English or language-neutral comments preferred)
- data types from `rdfs:range`; XSD ranges are normalized to the `xs:` prefix (e.g. `xs:string`)
- exact, case-sensitive class resolution
- case-insensitive search of class names for suggestions
- source provenance; for properties, `source_reference` points to the property resource itself

**Current limitations:**

- Only classes can be resolved. Properties, individuals and enumeration values are not resolvable as separate semantic identifiers.
- OWL restrictions (e.g. cardinalities) are not evaluated.
- Object properties have a class as range (e.g. `vec:AliasIdentification`); they are returned with `data_type: null` in the `iec61360` format.
- If a property has several ranges, the first one (sorted) is used.
- `unit` is not evaluated and currently `null`.
- The ontology is loaded remotely on first use and then kept in memory for the lifetime of the process.
- This is not a complete VEC implementation.

An earlier student prototype mapping the VEC ontology to IEC 61360 served as a reference for the mapping of `rdfs:label`/`rdfs:comment`. Its fuzzy best-match resolution was intentionally not adopted: resolution remains exact, fuzzy matching is limited to suggestions.

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

For suggestions, the Registry delegates the search query to all registered sources and returns their results in registration order of the sources. The order within each source is kept, so each source ranks its own suggestions.

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

Concepts additionally contain their `properties` and a `data_type`. The concept's `data_type` is set for value types (e.g. KBL simple types, using their base type) and is `null` for concepts that are described by properties (e.g. KBL complex types, VEC classes). It is mapped with the same rules as property data types.

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

#### Demo page

```
GET /ui/
```

Serves a static demo page (HTML, CSS and JavaScript, no external dependencies). Work in progress.

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

Matching is case-insensitive. Within each source, results are ranked by their best matching search text: exact matches first, then prefix matches, then substring matches, each sorted alphabetically. Search texts are the type or class name (KBL, VEC) and, for QUDT, the unit's local name and English or untagged labels. Results are grouped by source in registration order (KBL, VEC, QUDT); there is no ranking across sources.

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

The API will then be available at `http://127.0.0.1:8000`, Swagger UI at `http://127.0.0.1:8000/docs` and the demo page at `http://127.0.0.1:8000/ui/`.

Run the tests:

```
python -m pytest
```

Note: The KBL, VEC and QUDT sources load their source data (KBL XSD, VEC ontology, QUDT unit vocabulary) from the prostep ECAD wiki and qudt.org on first use. Resolving KBL, VEC or QUDT identifiers therefore requires network access; KBL-related tests may require it as well. The VEC and QUDT tests use small self-written vocabularies and run without network access.

To run without network access, local copies of the source data can be configured (see below).

### Configuring source URLs

The source URLs can be overridden with environment variables. If a variable is not set or empty, the default online URL is used.

| Variable | Source | Default |
|---|---|---|
| `SEMANTIC_HUB_KBL_XSD_URL` | KBL XSD | `https://ecad-wiki.prostep.org/specifications/kbl/v25-sr1/kbl2.5-sr1.xsd` |
| `SEMANTIC_HUB_VEC_TTL_URL` | VEC ontology | `https://ecad-wiki.prostep.org/specifications/vec/v220/vec-2.2.0-ontology.ttl` |
| `SEMANTIC_HUB_QUDT_UNIT_TTL_URL` | QUDT unit vocabulary | `https://qudt.org/vocab/unit/` |

The variables are read when the application starts, so they must be set before the server is started. Local copies can be configured as `file://` URLs, e.g. in PowerShell:

```
$env:SEMANTIC_HUB_VEC_TTL_URL = "file:///C:/sources/vec-2.2.0-ontology.ttl"
uvicorn app.main:app
```

A local copy must have the same format as the online source (XSD for KBL, Turtle for VEC and QUDT). Local copies of source data are not part of this repository; the licenses of the respective sources apply (see Semantic Sources).

---

## Reference

The project is based on the concepts described in:
https://wwwlehre.dhbw-stuttgart.de/~rentschler/Publications/ETFA2026__The_Semantic_Hub_extended.pdf
Rentschler, M. et al.

The Semantic Hub – Unifying Fragmented Semantic Dictionaries for Industry 4.0 and AAS.

The paper proposes an open infrastructure for integrating heterogeneous semantic resources and describes a Retrieval Service consisting of components including a Registry, Resolver and Formatter.

The project uses these concepts as the architectural basis for the implementation.

