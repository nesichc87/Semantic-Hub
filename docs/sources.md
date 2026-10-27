[← Back to README](../README.md)

# Semantic Sources

The Semantic Hub is intended to work with heterogeneous semantic resources.

## KBL (implemented, limited scope)

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
- The XSD is loaded on first use and then kept in memory for the lifetime of the process. There is no persistent cache yet; without network access, a local copy must be configured (see [Development](development.md#configuring-source-urls)).
- This is not a complete KBL implementation.

## VEC (implemented, limited scope)

VEC is the second real semantic source. It is integrated via the VEC 2.2.0 OWL ontology (Turtle), not the VEC XSD. This keeps KBL (XSD-based) and the ontology-based sources (VEC, QUDT, DPPO) on their natural representation.

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

## QUDT (implemented, limited scope)

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

## DPPO (implemented, limited scope)

DPPO (Digital Product Passport Ontology) is integrated via its OWL ontology, which is published as five Turtle modules (`dpp-odp`, `dpp-core`, `dpp-info`, `dpp-comp`, `dpp-prov`). All modules are loaded into one RDF graph, following the same pattern as VEC. The integration was checked against version 0.1 (26 classes). According to its authors, the ontology is under development and may still change considerably.

Semantic identifiers use the form `dppo:<module>:<LocalName>`, e.g. `dppo:dpp-core:ComponentDPP` for `http://w3id.org/dppo/ontology/dpp-core/ComponentDPP`. Properties use the same form, e.g. `dppo:dpp-odp:describes`.

**Supported:**

- named OWL classes in the five DPPO modules
- properties attached via `rdfs:domain`, including inherited properties via `rdfs:subClassOf` across modules; inherited properties come first
- names from the local name of the class or property, as for VEC
- definitions from `rdfs:comment` for classes and properties (English or language-neutral comments preferred)
- data types from `rdfs:range`; XSD ranges are normalized to the `xs:` prefix
- exact, case-sensitive class resolution
- case-insensitive search of class names for suggestions
- source provenance; for properties, `source_reference` points to the property resource itself

**Current limitations:**

- Only classes can be resolved.
- Properties whose domain is a blank node (e.g. `owl:unionOf`) are not included.
- IRIs that do not fit the identifier scheme (version 0.1 contains a few IRIs with a version segment, e.g. `.../dpp-info/0.1/CompositionInformation`) are not resolvable and not suggested.
- In version 0.1, most properties have no `rdfs:range`, so they are returned with `data_type: null`.
- The modules are loaded remotely on first use and then kept in memory for the lifetime of the process.
- This is not a complete DPPO implementation.

**License:** not yet clarified. The ontology files refer to a license file that could not be retrieved. No DPPO data is included in this repository.

## ECLASS (under evaluation)

The use of the ECLASS 16.0 Asset is being evaluated. The integration approach and the licensing conditions are still to be clarified. ECLASS data will not be included in this repository unless the license permits it.

## Mock (development and testing)

A mock source (`mock:` prefix) is used for development and testing. It returns a minimal concept of the internal semantic model.
