// Semantic Hub demo page: resolve a semantic ID and show both output formats.
"use strict";

const SOURCES = {
  kbl: { label: "KBL", title: "KBL-Schema", detail: "XSD 2.5 SR-1" },
  vec: { label: "VEC", title: "VEC-Ontologie", detail: "OWL 2.2.0 (Turtle)" },
  qudt: { label: "QUDT", title: "QUDT Units", detail: "Vokabular (Turtle)" },
  mock: { label: "Mock", title: "Mock-Quelle", detail: "nur Entwicklung" },
};

const NULL_HINTS = {
  kbl: { description: "Das KBL-XSD enthält keine fachlichen Definitionen.", definition: "Das KBL-XSD enthält keine fachlichen Definitionen." },
};
const PROSE_KEYS = new Set(["description", "definition"]);

const $ = (id) => document.getElementById(id);

const input = $("q");
const resolveButton = $("resolve-btn");
const exampleButtons = Array.from(document.querySelectorAll(".examples button"));

let requestCounter = 0;

function resolveUrl(semanticId, format) {
  return "/api/resolve/" + encodeURIComponent(semanticId) + "?format=" + format;
}

function showOnly(state) {
  $("empty").hidden = state !== "empty";
  $("notfound").hidden = state !== "notfound";
  $("concept").hidden = state !== "found";
  $("views").hidden = state !== "found";
}

function setBusy(busy) {
  resolveButton.disabled = busy;
  resolveButton.textContent = busy ? "Lädt …" : "Auflösen";
}

function markExample(semanticId) {
  exampleButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.id === semanticId));
  });
}

function nullValue(hint) {
  const fragment = document.createDocumentFragment();
  const value = document.createElement("span");
  value.className = "null";
  value.textContent = "null";
  fragment.appendChild(value);
  if (hint) {
    const why = document.createElement("span");
    why.className = "null-why";
    why.textContent = hint;
    fragment.appendChild(why);
  }
  return fragment;
}

function fillList(list, rows) {
  list.replaceChildren();
  rows.forEach(([key, value, hint]) => {
    const term = document.createElement("dt");
    term.textContent = key;
     const description = document.createElement("dd");
    if (PROSE_KEYS.has(key)) {
      description.classList.add("prose");
    }
    if (value === null || value === undefined) {
      description.appendChild(nullValue(hint));
    } else {
      description.textContent = String(value);
    }
    list.append(term, description);
  });
}

function propertyCount(properties) {
  const count = Array.isArray(properties) ? properties.length : 0;
  return count === 1 ? "1 Eintrag" : count + " Einträge";
}

function updateFlow(semanticId, original) {
  $("flow-request").textContent = "GET /api/resolve/" + semanticId;
  const source = SOURCES[original ? original.source : ""];
  $("flow-source").textContent = source ? source.title : "KBL · VEC · QUDT";
  $("flow-source-detail").textContent = source ? source.detail : "XSD bzw. Ontologie";
  $("flow-model").textContent = original
    ? propertyCount(original.properties).replace("Einträge", "Properties").replace("Eintrag", "Property")
    : "name · description · properties";
}

function renderFound(original, iec) {
  const hints = NULL_HINTS[original.source] || {};
  const source = SOURCES[original.source];

  const chip = $("concept-source");
  chip.className = "src " + original.source;
  chip.textContent = source ? source.label : original.source;
  $("concept-id").textContent = original.semantic_id;

  const provenance = original.provenance || {};
  fillList($("view-original"), [
    ["semantic_id", original.semantic_id],
    ["source", original.source],
    ["name", original.name],
    ["description", original.description, hints.description],
    ["data_type", original.data_type],
    ["provenance", provenance.source_reference],
    ["properties", propertyCount(original.properties)],
  ]);

  fillList($("view-iec"), [
    ["semantic_id", iec.semantic_id],
    ["preferred_name", iec.preferred_name],
    ["definition", iec.definition, hints.definition],
    ["source_of_definition", iec.source_of_definition],
    ["data_type", iec.data_type, "Kein Werttyp oder nicht eindeutig zuordenbar."],
    ["properties", propertyCount(iec.properties)],
  ]);

  showOnly("found");
}

function renderNotFound(semanticId, status) {
  $("notfound-id").textContent = semanticId;
  $("notfound").querySelector(".pill").textContent = "resolve · " + status;
  $("notfound").querySelector(":scope > p").textContent = status === 404
    ? "Diese ID gibt es nicht. resolve ist exakt und case-sensitive, der Hub rät nicht."
    : "Die Anfrage ist fehlgeschlagen (HTTP " + status + ").";
  $("didyoumean").hidden = true;
  showOnly("notfound");
}

async function resolve(semanticId) {
  semanticId = semanticId.trim();
  if (!semanticId) {
    return;
  }

  const thisRequest = ++requestCounter;
  input.value = semanticId;
  markExample(semanticId);
  updateFlow(semanticId, null);
  setBusy(true);

  try {
    const [originalResponse, iecResponse] = await Promise.all([
      fetch(resolveUrl(semanticId, "original")),
      fetch(resolveUrl(semanticId, "iec61360")),
    ]);
    if (thisRequest !== requestCounter) {
      return;
    }
    if (!originalResponse.ok || !iecResponse.ok) {
      renderNotFound(semanticId, originalResponse.ok ? iecResponse.status : originalResponse.status);
      return;
    }
    const original = (await originalResponse.json()).result;
    const iec = (await iecResponse.json()).result;
    if (thisRequest !== requestCounter) {
      return;
    }
    updateFlow(semanticId, original);
    renderFound(original, iec);
  } catch (error) {
    if (thisRequest === requestCounter) {
      renderNotFound(semanticId, "Netzwerkfehler");
    }
    console.error(error);
  } finally {
    if (thisRequest === requestCounter) {
      setBusy(false);
    }
  }
}

resolveButton.addEventListener("click", () => resolve(input.value));

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    resolve(input.value);
  }
});

exampleButtons.forEach((button) => {
  button.addEventListener("click", () => resolve(button.dataset.id));
});