"use strict";

// The card creator page: pick a payload, edit the card JSON, see the card.
//
// The data flow is one loop. The two JSON boxes are the source of truth:
//   payload box + card JSON box  ->  renderCard()  ->  the card on the right
// Every other control (the lines panel, the text on the card, the payload dropdown) works by
// rewriting one of the two boxes and calling redraw().
//
// Depends on renderer.js (renderCard, fill, el, GAMES, SPACING_PX, TEXT_STYLES, CONNECTIONS_COLORS) and
// sample-data.js (PAYLOADS, STARTING_CARD).

(function () {
  // ---------- styles ----------

  // Every line style the page offers. `example` is the value used in the "Available styles" list.
  // Adding a style to the renderer? Add a row here too.
  const STYLES = [
    { name: "headline", example: "You played a streak of" },
    { name: "headline-strong", example: "You solved it in 2." },
    { name: "stat", example: "{days_all} words" },
    { name: "body", example: "You really know how to harvest honey from the beehive." },
    { name: "display", example: "{streak.days} days" },
    { name: "label", example: "You kept coming back" },
    { name: "label-bold", example: "of {streak.game}" },
    { name: "game-icon", example: "{streak.game}" },
    { name: "spacer", example: "2" },
    { name: "wordle-grid", example: "{best_wordle_solve.word}" },
    { name: "connections-color", example: "{top_connections_color}" },
    { name: "games-chart", example: "games" },
  ];
  const STYLE_NAMES = [...STYLES.map((s) => s.name), "none"];

  // Where the visual styles read from the payload. Anon players have community data instead.
  const PAYLOAD_PATHS = {
    personal: {
      "game-icon": "{streak.game}",
      "wordle-grid": "{best_wordle_solve.word}",
      "connections-color": "{top_connections_color}",
      "games-chart": "games",
    },
    anon: {
      "game-icon": "{community.longest_streak.game}",
      "wordle-grid": "{community.wordle_most_solved_word}",
      "connections-color": "{community.top_connections_color}",
      "games-chart": "community.games",
    },
  };

  // A new line of these styles starts on a fixed choice; the others start by reading the payload.
  const STARTING_VALUES = { "game-icon": "wordle", spacer: "2", "connections-color": "blue" };

  // Styles with a second dropdown next to them (the "variant"): a fixed choice, or "from payload".
  const VARIANTS = {
    "game-icon": () => [
      ...Object.entries(GAMES).map(([id, name]) => ({ value: id, label: name })),
      { value: PAYLOAD_PATHS[audience()]["game-icon"], label: "from payload" },
    ],
    spacer: () =>
      Object.keys(SPACING_PX)
        .sort((a, b) => parseFloat(a) - parseFloat(b))
        .map((token) => ({ value: token, label: `${token} · ${SPACING_PX[token]}px` })),
    "connections-color": () => [
      ...CONNECTIONS_COLORS.map((color) => ({ value: color, label: color })),
      { value: PAYLOAD_PATHS[audience()]["connections-color"], label: "from payload" },
    ],
  };

  function startingValue(style) {
    if (TEXT_STYLES.includes(style)) return "Your text here";
    if (style === "none") return "";
    return STARTING_VALUES[style] ?? PAYLOAD_PATHS[audience()][style] ?? "";
  }

  // ---------- state ----------

  const payloadInput = document.getElementById("payload-input");
  const cardInput = document.getElementById("card-input");
  const payloadStatus = document.getElementById("payload-status");
  const cardStatus = document.getElementById("card-status");
  const cardMount = document.getElementById("card");
  const lineList = document.getElementById("line-list");
  const payloadSelect = document.getElementById("payload-select");

  const PAYLOAD_IDS = Object.keys(PAYLOADS);
  const DEFAULT_PAYLOAD_ID = "sub-4-wordle";
  let payloadId = DEFAULT_PAYLOAD_ID;

  // Edits survive switching payloads (in memory only; reload to reset).
  const payloadEdits = {}; // payload id -> edited text
  const cardEdits = {}; //    "personal" or "anon" -> edited text

  const audience = () => (payloadId === "anon" ? "anon" : "personal");
  const pretty = (value) => JSON.stringify(value, null, 2);

  // Parses a JSON box. Marks the box red and shows the error if it isn't valid; returns null.
  function readJson(box, status) {
    try {
      const value = JSON.parse(box.value);
      box.classList.remove("invalid");
      status.textContent = "";
      return value;
    } catch (error) {
      box.classList.add("invalid");
      status.textContent = error.message;
      return null;
    }
  }

  // ---------- redraw ----------

  // Rebuilds the card from the two boxes. If either is invalid, the last good card stays on screen.
  // keepLineList: leave the lines panel alone (used while typing in it, so the cursor stays put).
  function redraw(keepLineList = false) {
    const payload = readJson(payloadInput, payloadStatus);
    const spec = readJson(cardInput, cardStatus);
    if (payload === null || spec === null) return;
    payloadEdits[payloadId] = payloadInput.value;
    cardEdits[audience()] = cardInput.value;
    try {
      const card = renderCard(spec, payload);
      makeTextEditable(card);
      cardMount.replaceChildren(card);
      if (!keepLineList) renderLineList(spec);
    } catch (error) {
      cardInput.classList.add("invalid");
      cardStatus.textContent = error.message;
    }
  }

  // Changes the "lines" array in the card JSON box, then redraws. Nothing happens if the box is invalid.
  function editLines(change, keepLineList = false) {
    const spec = readJson(cardInput, cardStatus);
    if (!spec || typeof spec !== "object" || Array.isArray(spec)) return;
    if (spec.lines !== undefined && !Array.isArray(spec.lines)) return;
    spec.lines = spec.lines || [];
    change(spec.lines);
    cardInput.value = pretty(spec);
    redraw(keepLineList);
  }

  // ---------- lines panel ----------

  // One row per line: a drag handle, its style, its text or variant, and a remove button.
  function renderLineList(spec) {
    const lines = spec && Array.isArray(spec.lines) ? spec.lines : [];
    lineList.replaceChildren(
      ...lines.map((line, index) => {
        const [style, value] = Object.entries(line)[0] || ["", ""];
        const detail = VARIANTS[style] ? variantSelect(style, value, index) : textInput(style, value, index);
        const row = el("div", "line-row");
        row.append(dragHandle(row, index), styleSelect(style, value, index), detail,
          closeButton("Remove line", () => editLines((lines) => { lines.splice(index, 1); })));
        row.addEventListener("dragover", (event) => showDropTarget(event, row));
        row.addEventListener("dragleave", () => clearDropTarget(row));
        row.addEventListener("drop", (event) => dropLine(event, row, index));
        return row;
      })
    );
  }

  // ---------- drag to reorder ----------

  // The grip on the left of a row. Only the grip is draggable, so text fields and dropdowns still
  // work normally. The dragged line's position travels in the drag data.
  function dragHandle(row, index) {
    const handle = el("span", "line-handle");
    handle.draggable = true;
    handle.title = "Drag to reorder";
    handle.setAttribute("aria-label", `Drag line ${index + 1} to reorder`);
    handle.addEventListener("dragstart", (event) => {
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", String(index));
      if (event.dataTransfer.setDragImage) event.dataTransfer.setDragImage(row, 16, 16);
      row.classList.add("dragging");
    });
    handle.addEventListener("dragend", () => {
      row.classList.remove("dragging");
      lineList.querySelectorAll(".drop-before, .drop-after").forEach((r) => clearDropTarget(r));
    });
    return handle;
  }

  // The upper half of a row means "drop before it"; the lower half means "drop after it".
  const dropAfter = (event, row) => {
    const box = row.getBoundingClientRect();
    return event.clientY > box.top + box.height / 2;
  };

  function showDropTarget(event, row) {
    event.preventDefault(); // allows the drop
    row.classList.toggle("drop-after", dropAfter(event, row));
    row.classList.toggle("drop-before", !dropAfter(event, row));
  }

  function clearDropTarget(row) {
    row.classList.remove("drop-before", "drop-after");
  }

  // Moves line `from` to just before or after this row, then redraws.
  function dropLine(event, row, index) {
    event.preventDefault();
    const from = Number(event.dataTransfer.getData("text/plain"));
    const slot = index + (dropAfter(event, row) ? 1 : 0); // where the line is inserted, counting the old position
    clearDropTarget(row);
    if (!Number.isInteger(from) || from === slot || from + 1 === slot) return;
    editLines((lines) => {
      const [moved] = lines.splice(from, 1);
      lines.splice(slot > from ? slot - 1 : slot, 0, moved);
    });
  }

  // <option>s for a list of names. A name typed by hand in the JSON that isn't in the list stays selectable.
  function optionsFor(select, options, selected) {
    for (const { value, label } of options) {
      const option = el("option", "", label);
      option.value = value;
      option.selected = value === selected;
      select.appendChild(option);
    }
  }

  function styleSelect(style, value, index) {
    const select = el("select");
    select.setAttribute("aria-label", `Style for line ${index + 1}`);
    const names = STYLE_NAMES.includes(style) ? STYLE_NAMES : [style, ...STYLE_NAMES];
    optionsFor(select, names.map((name) => ({ value: name, label: name })), style);
    select.addEventListener("change", () => {
      const next = select.value;
      // Words carry over between text styles; anything else starts on that style's own value.
      const keepText = TEXT_STYLES.includes(next) && TEXT_STYLES.includes(style);
      editLines((lines) => { lines[index] = { [next]: keepText ? value : startingValue(next) }; });
    });
    return select;
  }

  // The line's words (or the payload path the games chart reads), editable. Each keystroke rewrites the
  // card JSON. It's a textarea so it can hold line breaks (Enter adds one here).
  function textInput(style, value, index) {
    const input = el("textarea", "line-text");
    input.rows = 1;
    input.value = String(value);
    input.spellcheck = false;
    input.setAttribute("aria-label", `Text for line ${index + 1}`);
    input.addEventListener("input", () => {
      growToFit(input);
      editLines((lines) => { lines[index] = { [style]: input.value }; }, true);
    });
    queueMicrotask(() => growToFit(input)); // once it is in the page and has a width
    return input;
  }

  // Makes a textarea as tall as its text.
  function growToFit(box) {
    box.style.height = "auto";
    box.style.height = `${box.scrollHeight}px`;
  }

  function variantSelect(style, value, index) {
    const options = VARIANTS[style]();
    if (!options.some((o) => o.value === value)) options.unshift({ value, label: String(value) });
    const select = el("select", "variant-select");
    select.setAttribute("aria-label", `Variant for line ${index + 1}`);
    optionsFor(select, options, value);
    select.addEventListener("change", () => {
      if (style === "game-icon" && GAMES[select.value]) syncStreakGame(select.value);
      editLines((lines) => { lines[index] = { [style]: select.value }; });
    });
    return select;
  }

  // Picking a game for the game icon also sets the payload's streak game, so text like
  // "of {streak.game}" follows the icon.
  function syncStreakGame(game) {
    const path = PAYLOAD_PATHS[audience()]["game-icon"].slice(1, -1).split("."); // "{streak.game}" -> ["streak", "game"]
    const payload = readJson(payloadInput, payloadStatus);
    if (!payload) return;
    const field = path.pop();
    const parent = path.reduce((obj, key) => (obj && typeof obj === "object" ? obj[key] : undefined), payload);
    if (!parent || typeof parent !== "object") return;
    parent[field] = game;
    payloadInput.value = pretty(payload);
  }

  // The round ✕ button: removes a line, or deletes a saved recipe.
  function closeButton(label, onClick) {
    const img = el("img");
    img.src = "ui-icons/close.svg";
    img.alt = "";
    const button = el("button", "line-action", undefined, [img]);
    button.type = "button";
    button.title = label;
    button.setAttribute("aria-label", label);
    button.addEventListener("click", onClick);
    return button;
  }

  // The dropdown and button under the lines panel. New lines go at the end.
  function mountAddLine() {
    const select = document.getElementById("add-line-style");
    optionsFor(select, STYLE_NAMES.map((name) => ({ value: name, label: name })));
    document.getElementById("add-line").addEventListener("click", () =>
      editLines((lines) => { lines.push({ [select.value]: startingValue(select.value) }); }));
  }

  // ---------- editing text on the card ----------

  // "plaintext-only" where the browser supports it, so pasted text carries no formatting.
  const EDITABLE = (() => {
    const probe = el("div");
    try { probe.contentEditable = "plaintext-only"; } catch (error) { /* older browsers */ }
    return probe.contentEditable === "plaintext-only" ? "plaintext-only" : "true";
  })();

  function caretToEnd(node) {
    const range = document.createRange();
    range.selectNodeContents(node);
    range.collapse(false);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }

  // The text in an editable element, as it should be saved. Browsers store a line break in different ways
  // (a "\n" inside the text, a <br>, or a new block), and textContent ignores <br>, so read the tree
  // instead. A <br> at the very end is only the placeholder that lets a trailing empty line show; it is
  // not counted.
  function readEditableText(node) {
    let text = "";
    const walk = (parent) => {
      const children = Array.from(parent.childNodes || []);
      children.forEach((child, i) => {
        if (child.nodeType === 3) {
          text += child.nodeValue;
        } else if (child.nodeName === "BR") {
          const isPlaceholder = parent === node && i === children.length - 1;
          if (!isPlaceholder) text += "\n";
        } else {
          if (text && !text.endsWith("\n")) text += "\n"; // a block starts on a new line
          walk(child);
        }
      });
    };
    walk(node);
    return text;
  }

  // A "\n" at the very end does not show as an empty line until something follows it, so add the
  // placeholder <br> that readEditableText ignores.
  function showTrailingBreak(node) {
    const last = node.lastChild;
    if (readEditableText(node).endsWith("\n") && !(last && last.nodeName === "BR")) {
      node.appendChild(document.createElement("br"));
    }
  }

  // Puts a line break at the cursor as a plain "\n" in the text (the line is in pre-wrap while editing).
  // Done by hand rather than with the browser's insert command, whose result varies by browser.
  // Trade-off: the browser's undo (Ctrl+Z) does not step back over this break.
  function insertLineBreak(node) {
    const selection = window.getSelection();
    if (!selection || !selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    if (!node.contains(range.commonAncestorContainer)) return;
    range.deleteContents();
    const breakNode = document.createTextNode("\n");
    range.insertNode(breakNode);
    range.setStartAfter(breakNode);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    showTrailingBreak(node);
    node.dispatchEvent(new Event("input"));
  }

  // Text lines on the card can be edited where they are.
  //  - focus: show the raw text with its {placeholders}
  //  - typing: rewrite that entry in the card JSON, and mirror it into the lines panel; the card is
  //    not rebuilt, so the cursor stays put
  //  - Shift+Enter: add a line break (saved as \n in the JSON, shown as a break once you leave the line)
  //  - blur (or Enter): show the filled-in text again
  function makeTextEditable(card) {
    for (const node of card.querySelectorAll("[data-line]")) {
      const style = node.dataset.style;
      if (!TEXT_STYLES.includes(style)) continue;
      const index = Number(node.dataset.line);

      // This entry's raw text in the card JSON right now, or null if the JSON can't be read.
      const readRaw = () => {
        const spec = readJson(cardInput, cardStatus);
        const raw = spec && spec.lines && spec.lines[index] && spec.lines[index][style];
        return typeof raw === "string" ? raw : null;
      };

      node.contentEditable = EDITABLE;
      node.spellcheck = false;
      node.setAttribute("aria-label", "Edit text");

      // The first click on a line would put the cursor where you clicked in the filled-in text ("of Wordle"),
      // but the line then switches to its raw text ("of {streak.game}"), so that spot lands in the middle of a
      // placeholder and typing would split it. So the first click focuses the line itself, and the focus
      // handler below puts the cursor at the end. Clicks on a line that is already being edited work normally.
      node.addEventListener("mousedown", (event) => {
        if (document.activeElement === node) return;
        event.preventDefault();
        node.focus();
      });

      node.addEventListener("focus", () => {
        const raw = readRaw();
        if (raw === null) return;
        node.style.whiteSpace = "pre-wrap"; // keep spaces and breaks visible while editing
        node.textContent = raw;
        caretToEnd(node);
      });

      node.addEventListener("input", () => {
        const spec = readJson(cardInput, cardStatus);
        if (!spec) return;
        const text = readEditableText(node);
        spec.lines[index] = { [style]: text };
        cardInput.value = pretty(spec);
        cardEdits[audience()] = cardInput.value;
        const field = lineList.children[index] && lineList.children[index].querySelector(".line-text");
        if (field) {
          field.value = text;
          growToFit(field);
        }
      });

      node.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        if (event.shiftKey) insertLineBreak(node);
        else node.blur();
      });

      node.addEventListener("blur", () => {
        const raw = readRaw();
        const payload = readJson(payloadInput, payloadStatus);
        node.style.whiteSpace = "";
        if (raw === null || payload === null) return;
        node.textContent = fill(raw, payload);
      });
    }
  }

  // ---------- payload ----------

  function loadBoxes() {
    payloadInput.value = payloadEdits[payloadId] ?? pretty(PAYLOADS[payloadId].data);
    cardInput.value = cardEdits[audience()] ?? pretty(STARTING_CARD[audience()]);
    redraw();
  }

  function selectPayload(id) {
    payloadId = id;
    payloadSelect.value = id;
    loadBoxes();
  }

  function mountPayloadSelect() {
    optionsFor(payloadSelect, PAYLOAD_IDS.map((id) => ({ value: id, label: PAYLOADS[id].label })));
    payloadSelect.addEventListener("change", () => selectPayload(payloadSelect.value));
  }

  // ---------- available styles list ----------

  // Every style, drawn once with example text, so you can see what each one looks like.
  function renderStyleList() {
    const payload = PAYLOADS["sub-7-wordle"].data;
    document.getElementById("style-list").replaceChildren(
      ...STYLES.map(({ name, example }) =>
        el("div", "style-item", undefined, [
          el("span", "style-name", name),
          el("div", "style-sample", undefined, [renderCard({ lines: [{ [name]: example }] }, payload)]),
        ]))
    );
  }

  // ---------- saved recipes ----------

  // A recipe is the card JSON plus which kind of player it was written for (personal or anon), so loading
  // it can pick a payload that has the fields it reads. Recipes are saved in this browser (localStorage):
  // they are still here after a reload, but they are not shared with other browsers or people. To move them
  // between browsers or share them, use Export and Import (a JSON file, see exportRecipes below).
  const RECIPES_KEY = "yig2026.recipes";
  const recipeNameInput = document.getElementById("recipe-name");
  const recipeList = document.getElementById("recipe-list");
  const recipeStatus = document.getElementById("recipe-status");

  function recipeMessage(text, isError = false) {
    recipeStatus.textContent = text;
    recipeStatus.classList.toggle("is-info", !isError);
  }

  function readRecipes() {
    try {
      const saved = JSON.parse(localStorage.getItem(RECIPES_KEY) || "[]");
      return Array.isArray(saved) ? saved.filter((r) => r && typeof r.name === "string" && r.card) : [];
    } catch (error) {
      return []; // no saved recipes yet, or storage is blocked
    }
  }

  function writeRecipes(recipes) {
    try {
      localStorage.setItem(RECIPES_KEY, JSON.stringify(recipes));
      return true;
    } catch (error) {
      recipeMessage("Could not save: this browser is blocking local storage.", true);
      return false;
    }
  }

  // "Recipe 1", "Recipe 2" ... the first number not already used.
  function nextRecipeName(recipes) {
    let n = 1;
    while (recipes.some((r) => r.name === `Recipe ${n}`)) n++;
    return `Recipe ${n}`;
  }

  // Saves the card JSON under the name in the box. A name that already exists is replaced.
  function saveRecipe() {
    const card = readJson(cardInput, cardStatus);
    if (card === null) return recipeMessage("Fix the Card JSON first: it is not valid.", true);
    const recipes = readRecipes();
    const name = recipeNameInput.value.trim() || nextRecipeName(recipes);
    const existing = recipes.findIndex((r) => r.name === name);
    const recipe = { name, audience: audience(), card, savedAt: Date.now() };
    if (existing === -1) recipes.push(recipe);
    else recipes[existing] = recipe;
    if (!writeRecipes(recipes)) return;
    recipeNameInput.value = name;
    recipeMessage(existing === -1 ? `Saved "${name}".` : `Replaced "${name}".`);
    renderRecipeList();
  }

  // Puts a saved recipe in the Card JSON box. If it was written for the other kind of player, the payload
  // switches to a default one for that kind first. The name goes in the name box, so saving again replaces it.
  function loadRecipe(recipe) {
    if (recipe.audience !== audience()) selectPayload(recipe.audience === "anon" ? "anon" : DEFAULT_PAYLOAD_ID);
    cardInput.value = pretty(recipe.card);
    recipeNameInput.value = recipe.name;
    redraw();
    recipeMessage(`Loaded "${recipe.name}".`);
  }

  function deleteRecipe(name) {
    if (!writeRecipes(readRecipes().filter((r) => r.name !== name))) return;
    recipeMessage(`Deleted "${name}".`);
    renderRecipeList();
  }

  // Newest first. Click a name to load it; ✕ deletes it.
  function renderRecipeList() {
    const recipes = readRecipes().reverse();
    if (!recipes.length) {
      recipeList.replaceChildren(el("li", "recipe-empty", "No saved recipes yet."));
      return;
    }
    recipeList.replaceChildren(
      ...recipes.map((recipe) => {
        const load = el("button", "recipe-load", undefined, [
          el("span", "recipe-title", recipe.name),
          el("span", "recipe-meta", recipe.audience === "anon" ? "Anon" : "Personal"),
        ]);
        load.type = "button";
        load.title = "Load this recipe";
        load.addEventListener("click", () => loadRecipe(recipe));
        return el("li", "recipe-item", undefined, [load, closeButton(`Delete "${recipe.name}"`, () => deleteRecipe(recipe.name))]);
      })
    );
  }

  // ---------- export and import ----------

  // The file looks like { "format": "yig2026-recipes", "version": 1, "recipes": [ {name, audience, card, savedAt} ] }.
  // The format field lets Import tell one of our files from any other JSON.
  const EXPORT_FORMAT = "yig2026-recipes";

  // Downloads every saved recipe as one .json file.
  function exportRecipes() {
    const recipes = readRecipes();
    if (!recipes.length) return recipeMessage("Nothing to export: save a recipe first.", true);
    const file = { format: EXPORT_FORMAT, version: 1, exportedAt: new Date().toISOString(), recipes };
    const url = URL.createObjectURL(new Blob([pretty(file)], { type: "application/json" }));
    const link = el("a");
    link.href = url;
    link.download = `yig2026-recipes-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    recipeMessage(`Exported ${recipes.length} recipe${recipes.length === 1 ? "" : "s"}.`);
  }

  // Turns whatever was read from a file into a clean recipe, or null if it isn't one.
  // Accepts our export format, or a bare list of recipes.
  function cleanRecipe(item) {
    if (!item || typeof item !== "object") return null;
    const name = typeof item.name === "string" ? item.name.trim() : "";
    const card = item.card;
    if (!name || !card || typeof card !== "object" || Array.isArray(card)) return null;
    if (card.lines !== undefined && !Array.isArray(card.lines)) return null;
    return {
      name,
      audience: item.audience === "anon" ? "anon" : "personal",
      card,
      savedAt: Number.isFinite(item.savedAt) ? item.savedAt : Date.now(),
    };
  }

  // Merges the recipes in a file into the saved ones. A name that already exists is replaced.
  function importRecipes(text) {
    let data;
    try {
      data = JSON.parse(text);
    } catch (error) {
      return recipeMessage("That file is not valid JSON.", true);
    }
    const items = Array.isArray(data) ? data : data && data.format === EXPORT_FORMAT ? data.recipes : null;
    if (!Array.isArray(items)) return recipeMessage("That file is not a recipes export.", true);

    const incoming = items.map(cleanRecipe).filter(Boolean);
    if (!incoming.length) return recipeMessage("No usable recipes in that file.", true);

    const recipes = readRecipes();
    let added = 0;
    let replaced = 0;
    for (const recipe of incoming) {
      const existing = recipes.findIndex((r) => r.name === recipe.name);
      if (existing === -1) { recipes.push(recipe); added++; }
      else { recipes[existing] = recipe; replaced++; }
    }
    if (!writeRecipes(recipes)) return;
    const skipped = items.length - incoming.length;
    recipeMessage(
      `Imported ${incoming.length} recipe${incoming.length === 1 ? "" : "s"} ` +
      `(${added} new, ${replaced} replaced${skipped ? `, ${skipped} skipped` : ""}).`
    );
    renderRecipeList();
  }

  function mountTransfer() {
    const fileInput = document.getElementById("import-file");
    document.getElementById("export-recipes").addEventListener("click", exportRecipes);
    document.getElementById("import-recipes").addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", async () => {
      const file = fileInput.files && fileInput.files[0];
      fileInput.value = ""; // so choosing the same file again still fires
      if (!file) return;
      try {
        importRecipes(await file.text());
      } catch (error) {
        recipeMessage("Could not read that file.", true);
      }
    });
  }

  function mountRecipes() {
    mountTransfer();
    document.getElementById("save-recipe").addEventListener("click", saveRecipe);
    recipeNameInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") saveRecipe();
    });
    renderRecipeList();
  }

  // ---------- start ----------

  payloadInput.addEventListener("input", () => redraw());
  cardInput.addEventListener("input", () => redraw());

  renderStyleList();
  mountAddLine();
  mountPayloadSelect();
  mountRecipes();
  selectPayload(payloadId);
})();
