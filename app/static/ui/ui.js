// Semantic Hub demo page: resolve a semantic ID and show both output formats.
// Texts come from i18n.js (TEXTS), which is loaded before this script.
"use strict";

const SOURCES = {
  kbl: { label: "KBL" },
  vec: { label: "VEC" },
  qudt: { label: "QUDT" },
  dppo: { label: "DPPO" },
  mock: { label: "Mock" },
};

const PROSE_KEYS = new Set(["description", "definition"]);
const LANGUAGE_STORAGE_KEY = "semantic-hub-language";
const DEFAULT_LANGUAGE = "de";

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

// What is currently shown, so it can be redrawn after a language switch
// without a new request: null, { kind: "found", original, iec } or
// { kind: "notfound", semanticId, status }.
let lastRender = null;

// ---------------------------------------------------------------------------
// Texts and language
// ---------------------------------------------------------------------------

function loadLanguage() {
  try {
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (stored && TEXTS[stored]) {
      return stored;
    }
  } catch (error) {
    // Storage may be unavailable (e.g. private mode): use the default.
  }
  return DEFAULT_LANGUAGE;
}

function saveLanguage(language) {
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch (error) {
    // Not critical: the choice is just not remembered.
  }
}

let language = loadLanguage();

function t(key, values) {
  const text = (TEXTS[language] && TEXTS[language][key])
    || TEXTS[DEFAULT_LANGUAGE][key]
    || key;
  return text.replace(/\{(\w+)\}/g, (match, name) =>
    values && name in values ? String(values[name]) : match
  );
}

// Writes a text into an element. Parts in `backticks` become <code>.
// No innerHTML is used.
function renderText(element, text) {
  element.replaceChildren();
  text.split("`").forEach((part, index) => {
    if (!part) {
      return;
    }
    if (index % 2 === 1) {
      const code = document.createElement("code");
      code.textContent = part;
      element.appendChild(code);
    } else {
      element.appendChild(document.createTextNode(part));
    }
  });
}

function applyStaticTexts() {
  document.documentElement.lang = language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    renderText(element, t(element.dataset.i18n));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
}

function renderLanguageSwitch() {
  const box = $("lang-switch");
  box.replaceChildren();
  Object.keys(TEXTS).forEach((code) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = code.toUpperCase();
    button.setAttribute("aria-pressed", String(code === language));
    button.addEventListener("click", () => setLanguage(code));
    box.appendChild(button);
  });
}

function setLanguage(next) {
  if (!TEXTS[next] || next === language) {
    return;
  }
  language = next;
  saveLanguage(next);
  applyStaticTexts();
  renderLanguageSwitch();
  setBusy(resolveButton.disabled);
  hideSuggest();
  redraw();
}

function redraw() {
  if (!lastRender) {
    return;
  }
  if (lastRender.kind === "found") {
    renderFound(lastRender.original, lastRender.iec);
  } else {
    renderNotFound(lastRender.semanticId, lastRender.status);
    if (lastRender.status === 404) {
      showCaseVariant(lastRender.semanticId, requestCounter);
    }
  }
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function resolveUrl(semanticId, format) {
  return "/api/resolve/" + encodeURIComponent(semanticId) + "?format=" + format;
}

function showOnly(state) {
  $("empty").hidden = state !== "empty";
  $("notfound").hidden = state !== "notfound";
  $("concept").hidden = state !== "found";
  $("views").hidden = state !== "found";
  document.querySelector(".flow").hidden = state !== "empty";
  $("request-line").hidden = state === "empty";
  if (state !== "found") {
    $("props").hidden = true;
  }
}

function setBusy(busy) {
  resolveButton.disabled = busy;
  resolveButton.textContent = busy ? t("search.busy") : t("search.resolve");
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

function nullHints(source) {
  if (source === "kbl") {
    return {
      description: t("null.kbl.definition"),
      definition: t("null.kbl.definition"),
    };
  }
  return {};
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
  return count === 1 ? t("props.count.one") : t("props.count.many", { count });
}

function showRequest(semanticId) {
  $("request-line").textContent =
    "GET /api/resolve/" + semanticId + "?format=original | iec61360";
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
  lastRender = { kind: "found", original, iec };
  const hints = nullHints(original.source);
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
    ["data_type", iec.data_type, t("null.datatype")],
    ["properties", propertyCount(iec.properties)],
  ]);

  showOnly("found");
  renderProperties(original, iec);
}

// status is an HTTP status code or "network" for a failed request.
function renderNotFound(semanticId, status) {
  lastRender = { kind: "notfound", semanticId, status };
  const label = status === "network" ? t("notfound.network") : String(status);

  $("notfound-id").textContent = semanticId;
  $("notfound").querySelector(".pill").textContent = "resolve · " + label;
  renderText(
    $("notfound-text"),
    status === 404 ? t("notfound.text") : t("notfound.failed", { status: label })
  );
  $("didyoumean").hidden = true;
  showOnly("notfound");
}

// ---------------------------------------------------------------------------
// Suggestions
// ---------------------------------------------------------------------------

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
    empty.textContent = t("suggest.none", { query });
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
    count.textContent = t("suggest.hits", { count: list.length })
      + (list.length > SUGGEST_LIMIT ? " · " + t("suggest.shown", { count: SUGGEST_LIMIT }) : "");
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
      more.textContent = t("suggest.more", { count: list.length - SUGGEST_LIMIT });
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
    note.textContent = " " + t("didyoumean.note");

    const [before, after] = t("didyoumean.text").split("{id}");
    const line = $("didyoumean");
    line.replaceChildren(before || "", link, after || "", note);
    line.hidden = false;
  } catch (error) {
    console.error(error);
  }
}

// ---------------------------------------------------------------------------
// Resolution and events
// ---------------------------------------------------------------------------

function resetView() {
  requestCounter++;
  lastRender = null;
  hideSuggest();
  markExample(null);
  setBusy(false);
  $("didyoumean").hidden = true;
  showOnly("empty");
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
  showRequest(semanticId);
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
    renderFound(original, iec);
  } catch (error) {
    if (thisRequest === requestCounter) {
      renderNotFound(semanticId, "network");
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
  if (!input.value.trim()) {
    resetView();
    return;
  }
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

applyStaticTexts();
renderLanguageSwitch();
