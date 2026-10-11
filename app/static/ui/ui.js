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
const SUGGEST_LIMIT = 5;
const SUGGEST_MIN_CHARS = 2;
const SUGGEST_DELAY_MS = 250;

let suggestCounter = 0;
let suggestTimer = null;

function resolveUrl(semanticId, format) {
  return "/api/resolve/" + encodeURIComponent(semanticId) + "?format=" + format;
}

function showOnly(state) {
  $("empty").hidden = state !== "empty";
  $("notfound").hidden = state !== "notfound";
  $("concept").hidden = state !== "found";
  $("views").hidden = state !== "found";
  if (state !== "found") {
    $("props").hidden = true;
  }
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

function cell(value, mapped) {
  const td = document.createElement("td");
  if (value === null || value === undefined) {
    td.appendChild(nullValue());
  } else if (mapped) {
    const span = document.createElement("span");
    span.className = "mapped";
    span.textContent = String(value);
    td.appendChild(span);
  } else {
    td.textContent = String(value);
  }
  return td;
}

function renderProperties(original, iec) {
  const properties = Array.isArray(original.properties) ? original.properties : [];
  const iecById = new Map(
    (Array.isArray(iec.properties) ? iec.properties : []).map((p) => [p.semantic_id, p])
  );

  const body = $("props-body");
  body.replaceChildren();
  properties.forEach((property) => {
    const iecProperty = iecById.get(property.semantic_id) || {};
    const arrow = document.createElement("td");
    arrow.className = "arrow";
    arrow.textContent = "→";
    const row = document.createElement("tr");
    row.append(
      cell(property.semantic_id),
      cell(property.data_type),
      arrow,
      cell(iecProperty.data_type, true),
      cell(property.unit),
    );
    body.appendChild(row);
  });

  $("props-count").textContent = "(" + properties.length + ")";
  $("props").hidden = properties.length === 0;
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
  renderProperties(original, iec);
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

function sourceOf(semanticId) {
  const index = semanticId.indexOf(":");
  return index > 0 ? semanticId.slice(0, index) : "";
}

function groupBySource(ids) {
  const groups = new Map();
  ids.forEach((id) => {
    const source = sourceOf(id);
    if (!groups.has(source)) {
      groups.set(source, []);
    }
    groups.get(source).push(id);
  });
  return groups;
}

function hideSuggest() {
  suggestCounter++;
  clearTimeout(suggestTimer);
  const box = $("suggest");
  box.hidden = true;
  box.replaceChildren();
}

function renderSuggest(query, ids) {
  const box = $("suggest");
  box.replaceChildren();

  if (ids.length === 0) {
    const empty = document.createElement("div");
    empty.className = "more";
    empty.textContent = "Keine Vorschläge für „" + query + "“.";
    box.appendChild(empty);
    box.hidden = false;
    return;
  }

  groupBySource(ids).forEach((list, source) => {
    const header = document.createElement("div");
    header.className = "group " + source;
    const chip = document.createElement("span");
    chip.className = "src " + source;
    chip.textContent = SOURCES[source] ? SOURCES[source].label : source;
    const count = document.createElement("span");
    count.className = "count";
    count.textContent = list.length + " Treffer" + (list.length > SUGGEST_LIMIT ? " · " + SUGGEST_LIMIT + " angezeigt" : "");
    header.append(chip, count);

    const items = document.createElement("ol");
    list.slice(0, SUGGEST_LIMIT).forEach((id) => {
      const item = document.createElement("li");
      item.setAttribute("role", "option");
      item.textContent = id;
      item.addEventListener("click", () => resolve(id));
      items.appendChild(item);
    });

    box.append(header, items);

    if (list.length > SUGGEST_LIMIT) {
      const more = document.createElement("div");
      more.className = "more";
      more.textContent = (list.length - SUGGEST_LIMIT) + " weitere · Eingabe verfeinern";
      box.appendChild(more);
    }
  });

  box.hidden = false;
}

async function suggest(query) {
  const thisRequest = ++suggestCounter;
  try {
    const response = await fetch("/api/suggest?query=" + encodeURIComponent(query));
    if (thisRequest !== suggestCounter) {
      return;
    }
    if (!response.ok) {
      hideSuggest();
      return;
    }
    const body = await response.json();
    if (thisRequest !== suggestCounter) {
      return;
    }
    renderSuggest(query, body.results);
  } catch (error) {
    if (thisRequest === suggestCounter) {
      hideSuggest();
    }
    console.error(error);
  }
}

async function showCaseVariant(semanticId, thisRequest) {
  const colon = semanticId.lastIndexOf(":");
  if (colon <= 0 || colon === semanticId.length - 1) {
    return;
  }
  const query = semanticId.slice(colon + 1);
  try {
    const response = await fetch("/api/suggest?query=" + encodeURIComponent(query));
    if (!response.ok || thisRequest !== requestCounter) {
      return;
    }
    const ids = (await response.json()).results;
    if (thisRequest !== requestCounter) {
      return;
    }
    const wanted = semanticId.toLowerCase();
    const match = ids.find((id) => id !== semanticId && id.toLowerCase() === wanted);
    if (!match) {
      return;
    }

    const link = document.createElement("button");
    link.type = "button";
    link.className = "linkish";
    link.textContent = match;
    link.addEventListener("click", () => resolve(match));
    const note = document.createElement("span");
    note.textContent = " (gleiche ID bis auf Groß- und Kleinschreibung, gefunden über suggest)";

    const line = $("didyoumean");
    line.replaceChildren("Meintest du ", link, "?", note);
    line.hidden = false;
  } catch (error) {
    console.error(error);
  }
}

async function resolve(semanticId) {
  semanticId = semanticId.trim();
  if (!semanticId) {
    return;
  }
  hideSuggest();

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
      const status = originalResponse.ok ? iecResponse.status : originalResponse.status;
      renderNotFound(semanticId, status);
      if (status === 404) {
        showCaseVariant(semanticId, thisRequest);
      }
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
  } else if (event.key === "Escape") {
    hideSuggest();
  }
});

input.addEventListener("input", () => {
  clearTimeout(suggestTimer);
  const query = input.value.trim();
  if (query.length < SUGGEST_MIN_CHARS) {
    hideSuggest();
    return;
  }
  suggestTimer = setTimeout(() => suggest(query), SUGGEST_DELAY_MS);
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".field")) {
    hideSuggest();
  }
});

exampleButtons.forEach((button) => {
  button.addEventListener("click", () => resolve(button.dataset.id));
});