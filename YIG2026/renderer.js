"use strict";

// Renders a card from JSON. Nothing in this file knows about the configurator page.
//
//   renderCard({ lines: [{ headline: "You played" }, { display: "{streak.days} days" }] }, payload)
//
// A card is { lines: [...] }. Each line is one { style: value } pair. For text styles the value is the words, with {placeholders} filled in from
// the payload ("{streak.days}" becomes 41). The other styles read their value differently; see the
// renderers below.
//
// To add a style: write a renderer here, add its CSS in styles.css, and add a row to STYLES in
// configurator.js so it shows up on the page.

// ---------- constants ----------

// Game id -> display name. Each game also has an icon (icons/<id>.svg) and a chart color
// (--game-<id> in styles.css).
const GAMES = {
  wordle: "Wordle",
  connections: "Connections",
  spelling_bee: "Spelling Bee",
  midi: "The Midi",
  mini: "The Mini",
  crossword: "The Crossword",
  strands: "Strands",
};

// Playbook spacing tokens: token number -> px. { "spacer": "2" } is 16px.
const SPACING_PX = {
  "0.5": 4, "1": 8, "1.5": 12, "2": 16, "2.5": 20, "3": 24, "4": 32,
  "5": 40, "6": 48, "7": 56, "8": 64, "9": 72, "10": 80,
};
const DEFAULT_SPACER_TOKEN = "2";

const CONNECTIONS_COLORS = ["yellow", "green", "blue", "purple"]; // hex values: --connections-* in styles.css
const CHART_MAX_GAMES = 4;
const TEXT_STYLES = ["headline", "headline-strong", "display", "stat", "body", "label", "label-bold"];

// ---------- payload lookup and placeholders ----------

// "streak.days" or "games[0].game" -> the value in the payload, or undefined.
function get(source, path) {
  return String(path)
    .replace(/\[(\d+)\]/g, ".$1")
    .split(".")
    .filter(Boolean)
    .reduce((value, key) => (value == null ? undefined : value[key]), source);
}

function format(value) {
  return typeof value === "number" ? value.toLocaleString("en-US", { maximumFractionDigits: 1 }) : String(value);
}

// Replaces each {path} in a template with its payload value. A game id becomes its display name
// ("wordle" -> "Wordle") unless `raw` is true; icons and the Wordle grid need the value as it is.
// A path that isn't in the payload becomes blank (and logs a warning).
function fill(template, scope, raw = false) {
  return String(template ?? "")
    .replace(/\{([^}]+)\}/g, (_, path) => {
      const value = get(scope, path.trim());
      if (value == null) {
        console.warn(`Unresolved placeholder {${path}}`);
        return "";
      }
      if (raw) return String(value);
      return typeof value === "string" && Object.hasOwn(GAMES, value) ? GAMES[value] : format(value);
    })
    .trim();
}

// ---------- lines ----------

// Creates an element: el("p", "line display", "41 days") or el("div", "row", undefined, [child, child]).
function el(tag, className, text, children) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  if (children) node.append(...children);
  return node;
}

// headline, display, label ...: the value is the words.
function renderText(style, value, scope) {
  return el("p", `line ${style}`, fill(value, scope));
}

// { "spacer": "2" }: empty space as tall as the Playbook spacing token. In this prototype it is drawn as a
// pink block with the token number inside, purely so you can see it while building. On a live card it
// would be invisible: no color, no text. The block and the number are development aids, not design.
function renderSpacer(value) {
  const token = String(value || DEFAULT_SPACER_TOKEN);
  if (!Object.hasOwn(SPACING_PX, token)) {
    console.warn(`Unknown spacing token "${token}"; use one of ${Object.keys(SPACING_PX).join(", ")}`);
  }
  const node = el("div", "line spacer", token);
  node.style.height = `${SPACING_PX[Object.hasOwn(SPACING_PX, token) ? token : DEFAULT_SPACER_TOKEN]}px`;
  return node;
}

// { "game-icon": "wordle" } or { "game-icon": "{streak.game}" }: the game's icon.
function renderIcon(value, scope) {
  const id = fill(value, scope, true);
  if (!Object.hasOwn(GAMES, id)) {
    const missing = el("div", "line game-icon game-icon-missing");
    missing.appendChild(el("span", "game-icon-label", id || "no game"));
    return missing;
  }
  const node = el("div", "line game-icon");
  const img = el("img");
  img.src = `icons/${id}.svg`;
  img.alt = GAMES[id];
  node.appendChild(img);
  return node;
}

// { "wordle-grid": "{best_wordle_solve.word}" }: one green tile per letter.
function renderWordleGrid(value, scope) {
  const node = el("div", "line wordle-grid");
  for (const letter of fill(value, scope, true)) node.appendChild(el("span", "wordle-tile", letter));
  return node;
}

// { "connections-color": "blue" }: a swatch filled with one of the four Connections colors.
function renderConnectionsColor(value, scope) {
  const color = fill(value, scope, true).toLowerCase();
  const node = el("div", "line connections-color");
  node.dataset.color = CONNECTIONS_COLORS.includes(color) ? color : "unknown";
  node.appendChild(el("span", "connections-label", color));
  return node;
}

// { "games-chart": "games" }: the value is a payload path to a list of { game, solved }. Shows the top
// games by games solved, largest first, with bars scaled to the top game. Text uses the label-bold style.
function renderChart(path, scope) {
  const list = el("ol", "line games-chart");
  const games = get(scope, path);
  if (!Array.isArray(games)) return list;
  const rows = games
    .map((g) => ({ game: g.game, solved: Number(g.solved) || 0 }))
    .sort((a, b) => b.solved - a.solved)
    .slice(0, CHART_MAX_GAMES);
  if (!rows.some((r) => r.solved)) console.warn('games-chart: no game has a "solved" count');
  const top = (rows[0] && rows[0].solved) || 1;
  for (const row of rows) {
    const item = el("li", "games-chart-row");
    item.style.setProperty("--bar-color", `var(--game-${row.game})`);
    const track = el("span", "games-chart-track");
    const bar = el("span", "games-chart-bar");
    bar.style.width = `${(row.solved / top) * 100}%`;
    track.appendChild(bar);
    item.append(
      el("span", "games-chart-label label-bold", GAMES[row.game] || row.game),
      track,
      el("span", "games-chart-value label-bold", format(row.solved))
    );
    list.appendChild(item);
  }
  return list;
}

// Styles that aren't plain text. Each takes (value, payload) and returns an element, or null.
const VISUAL_LINES = {
  none: () => null,
  spacer: renderSpacer,
  "game-icon": renderIcon,
  "wordle-grid": renderWordleGrid,
  "connections-color": renderConnectionsColor,
  "games-chart": renderChart,
};

function renderLine(line, scope) {
  const [style, value] = Object.entries(line)[0] || [];
  if (style === undefined) return null;
  if (Object.hasOwn(VISUAL_LINES, style)) return VISUAL_LINES[style](value, scope);
  if (TEXT_STYLES.includes(style)) return renderText(style, value, scope);
  console.warn(`Unknown line style "${style}"`);
  return null;
}

// ---------- cards ----------

// Each line element records its place in the JSON (data-line, data-style) so the configurator can
// map an element on the card back to its entry.
function renderStack(lines, scope) {
  const stack = el("div", "stack");
  lines.forEach((line, index) => {
    const node = renderLine(line, scope);
    if (!node) return;
    node.dataset.line = index;
    node.dataset.style = Object.keys(line)[0];
    stack.appendChild(node);
  });
  return stack;
}

function renderCard(spec, scope) {
  if (!spec || typeof spec !== "object" || Array.isArray(spec)) throw new Error("Card JSON must be an object");
  if (spec.lines !== undefined && !Array.isArray(spec.lines)) throw new Error('"lines" must be an array');
  const card = el("article", "card");
  if (spec.lines) card.appendChild(renderStack(spec.lines, scope));
  return card;
}
